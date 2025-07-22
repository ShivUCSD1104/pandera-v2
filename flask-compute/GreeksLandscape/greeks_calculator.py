"""
Black-Scholes Greeks calculator module.

This module implements the mathematical calculations for options Greeks
using the Black-Scholes model with proper error handling for edge cases.
"""

import math
from typing import Optional, Tuple
from scipy.stats import norm
import numpy as np
import logging
from functools import lru_cache
from datetime import datetime, timedelta
import hashlib
import time

from .data import GreeksData
from .exceptions import CalculationError, ValidationError
from .performance_monitor import performance_monitor, monitor_performance

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages caching for Greeks calculations with time-based expiration.
    """
    
    def __init__(self, cache_duration_hours: int = 1):
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache = {}
        self.cache_timestamps = {}
    
    def get_cache_key(self, *args, **kwargs) -> str:
        """Generate a unique cache key from function arguments."""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid based on timestamp."""
        if cache_key not in self.cache_timestamps:
            return False
        
        cache_time = self.cache_timestamps[cache_key]
        return datetime.now() - cache_time < self.cache_duration
    
    def get_cached_result(self, cache_key: str):
        """Get cached result if valid, otherwise return None."""
        if self.is_cache_valid(cache_key):
            return self.cache.get(cache_key)
        return None
    
    def cache_result(self, cache_key: str, result):
        """Cache a result with current timestamp."""
        self.cache[cache_key] = result
        self.cache_timestamps[cache_key] = datetime.now()
    
    def invalidate_cache(self, pattern: str = None):
        """Invalidate cache entries matching a pattern or all if no pattern."""
        if pattern is None:
            self.cache.clear()
            self.cache_timestamps.clear()
            logger.info("All Greeks calculation cache cleared")
        else:
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                self.cache.pop(key, None)
                self.cache_timestamps.pop(key, None)
            logger.info(f"Cleared {len(keys_to_remove)} cache entries matching pattern: {pattern}")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics for performance monitoring."""
        total_entries = len(self.cache)
        valid_entries = sum(1 for key in self.cache.keys() if self.is_cache_valid(key))
        expired_entries = total_entries - valid_entries
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_hit_ratio': getattr(self, '_hit_count', 0) / max(getattr(self, '_total_requests', 1), 1)
        }


# Global cache manager instance
_cache_manager = CacheManager(cache_duration_hours=1)


class GreeksCalculator:
    """
    Calculator for options Greeks using Black-Scholes formulas.
    
    Implements calculations for:
    - Delta: Price sensitivity (∂V/∂S)
    - Gamma: Delta sensitivity (∂²V/∂S²)
    - Theta: Time decay (∂V/∂t)
    - Vega: Volatility sensitivity (∂V/∂σ)
    - Rho: Interest rate sensitivity (∂V/∂r)
    """
    
    def __init__(self):
        self.min_time_to_expiry = 1/365  # Minimum 1 day
        self.min_volatility = 0.001      # Minimum 0.1% volatility
        self.max_volatility = 5.0        # Maximum 500% volatility
    
    @monitor_performance('greeks_calculation')
    def calculate_all_greeks(self, greeks_data: GreeksData) -> GreeksData:
        """
        Calculate all Greeks for a given options data point with caching.
        
        Args:
            greeks_data: GreeksData object with option parameters
            
        Returns:
            GreeksData object with calculated Greeks values
            
        Raises:
            CalculationError: When Greeks calculation fails
            ValidationError: When input parameters are invalid
        """
        try:
            # Generate cache key from input parameters
            cache_key = _cache_manager.get_cache_key(
                greeks_data.underlying_price,
                greeks_data.strike,
                greeks_data.time_to_expiry,
                greeks_data.volatility,
                greeks_data.risk_free_rate,
                greeks_data.option_type
            )
            
            # Check cache first
            _cache_manager._total_requests = getattr(_cache_manager, '_total_requests', 0) + 1
            cached_result = _cache_manager.get_cached_result(cache_key)
            if cached_result is not None:
                _cache_manager._hit_count = getattr(_cache_manager, '_hit_count', 0) + 1
                logger.debug(f"Cache hit for Greeks calculation: {cache_key[:8]}...")
                return cached_result
            
            # Validate and sanitize inputs
            validation_errors = self._validate_inputs_detailed(greeks_data)
            if validation_errors:
                error_msg = "; ".join(validation_errors)
                logger.warning(f"Invalid inputs for Greeks calculation: {error_msg}")
                raise ValidationError(
                    f"Invalid Greeks calculation parameters: {error_msg}",
                    user_message="Invalid option parameters. Please check strike price, expiry date, and other inputs."
                )
            
            # Calculate d1 and d2 for Black-Scholes
            try:
                d1, d2 = self._calculate_d1_d2(greeks_data)
            except Exception as e:
                logger.error(f"Error calculating d1/d2: {str(e)}")
                raise CalculationError(
                    f"Black-Scholes parameter calculation failed: {str(e)}",
                    user_message="Unable to calculate option parameters. Please check your inputs."
                )
            
            # Calculate Greeks based on option type
            try:
                if greeks_data.option_type.lower() == 'call':
                    greeks_data.delta = self._calculate_call_delta(d1)
                    greeks_data.theta = self._calculate_call_theta(greeks_data, d1, d2)
                else:  # put option
                    greeks_data.delta = self._calculate_put_delta(d1)
                    greeks_data.theta = self._calculate_put_theta(greeks_data, d1, d2)
                
                # Gamma and Vega are the same for calls and puts
                greeks_data.gamma = self._calculate_gamma(greeks_data, d1)
                greeks_data.vega = self._calculate_vega(greeks_data, d1)
                greeks_data.rho = self._calculate_rho(greeks_data, d2)
                
            except Exception as e:
                logger.error(f"Error calculating individual Greeks: {str(e)}")
                raise CalculationError(
                    f"Greeks calculation failed: {str(e)}",
                    user_message="Unable to calculate Greeks values. Please try again with different parameters."
                )
            
            # Validate calculated results
            if not self._validate_calculated_greeks(greeks_data):
                logger.warning("Calculated Greeks values are invalid")
                raise CalculationError(
                    "Calculated Greeks values are invalid or out of range",
                    user_message="Greeks calculation produced invalid results. Please check your parameters."
                )
            
            # Cache the result
            _cache_manager.cache_result(cache_key, greeks_data)
            logger.debug(f"Cached Greeks calculation result: {cache_key[:8]}...")
            
            return greeks_data
            
        except (ValidationError, CalculationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error calculating Greeks: {str(e)}")
            raise CalculationError(
                f"Unexpected Greeks calculation error: {str(e)}",
                user_message="An unexpected error occurred during Greeks calculation. Please try again."
            )
    
    def _validate_inputs(self, greeks_data: GreeksData) -> bool:
        """Validate input parameters for Greeks calculation."""
        try:
            # Check for positive values
            if greeks_data.underlying_price <= 0:
                return False
            if greeks_data.strike <= 0:
                return False
            if greeks_data.time_to_expiry <= 0:
                return False
            # Allow zero volatility - we'll handle it in calculation
            if greeks_data.volatility < 0:
                return False
            
            # Check for reasonable ranges
            if greeks_data.volatility > self.max_volatility:
                return False
            # Allow very short time to expiry - we'll handle it in calculation
                
            return True
            
        except Exception:
            return False
    
    def _validate_inputs_detailed(self, greeks_data: GreeksData) -> list:
        """
        Detailed validation of input parameters with specific error messages.
        
        Args:
            greeks_data: GreeksData object to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        try:
            # Check underlying price
            if greeks_data.underlying_price is None:
                errors.append("Underlying price is required")
            elif greeks_data.underlying_price <= 0:
                errors.append(f"Underlying price must be positive, got {greeks_data.underlying_price}")
            elif greeks_data.underlying_price > 1000000:  # Reasonable upper bound
                errors.append(f"Underlying price too high: {greeks_data.underlying_price}")
            
            # Check strike price
            if greeks_data.strike is None:
                errors.append("Strike price is required")
            elif greeks_data.strike <= 0:
                errors.append(f"Strike price must be positive, got {greeks_data.strike}")
            elif greeks_data.strike > 1000000:  # Reasonable upper bound
                errors.append(f"Strike price too high: {greeks_data.strike}")
            
            # Check time to expiry
            if greeks_data.time_to_expiry is None:
                errors.append("Time to expiry is required")
            elif greeks_data.time_to_expiry <= 0:
                errors.append(f"Time to expiry must be positive, got {greeks_data.time_to_expiry}")
            elif greeks_data.time_to_expiry > 10:  # More than 10 years
                errors.append(f"Time to expiry too long: {greeks_data.time_to_expiry} years")
            
            # Check volatility
            if greeks_data.volatility is None:
                errors.append("Volatility is required")
            elif greeks_data.volatility < 0:
                errors.append(f"Volatility cannot be negative, got {greeks_data.volatility}")
            elif greeks_data.volatility > self.max_volatility:
                errors.append(f"Volatility too high: {greeks_data.volatility}, max allowed: {self.max_volatility}")
            
            # Check risk-free rate
            if greeks_data.risk_free_rate is None:
                errors.append("Risk-free rate is required")
            elif abs(greeks_data.risk_free_rate) > 1.0:  # More than 100%
                errors.append(f"Risk-free rate out of reasonable range: {greeks_data.risk_free_rate}")
            
            # Check option type
            if greeks_data.option_type is None:
                errors.append("Option type is required")
            elif greeks_data.option_type.lower() not in ['call', 'put']:
                # Handle common variations
                if greeks_data.option_type.lower() == 'calls':
                    greeks_data.option_type = 'call'
                elif greeks_data.option_type.lower() == 'puts':
                    greeks_data.option_type = 'put'
                else:
                    errors.append(f"Option type must be 'call' or 'put', got '{greeks_data.option_type}'")
            
            # Check for NaN or infinity values
            numeric_fields = [
                ('underlying_price', greeks_data.underlying_price),
                ('strike', greeks_data.strike),
                ('time_to_expiry', greeks_data.time_to_expiry),
                ('volatility', greeks_data.volatility),
                ('risk_free_rate', greeks_data.risk_free_rate)
            ]
            
            for field_name, value in numeric_fields:
                if value is not None:
                    if not (value == value):  # NaN check
                        errors.append(f"{field_name} cannot be NaN")
                    elif abs(value) == float('inf'):
                        errors.append(f"{field_name} cannot be infinite")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    def _validate_calculated_greeks(self, greeks_data: GreeksData) -> bool:
        """
        Validate calculated Greeks values for reasonableness.
        
        Args:
            greeks_data: GreeksData object with calculated Greeks
            
        Returns:
            True if all Greeks values are reasonable, False otherwise
        """
        try:
            # Check delta bounds
            if greeks_data.delta is not None:
                if greeks_data.option_type.lower() == 'call':
                    if not (0 <= greeks_data.delta <= 1):
                        logger.warning(f"Call delta out of bounds: {greeks_data.delta}")
                        return False
                else:  # put
                    if not (-1 <= greeks_data.delta <= 0):
                        logger.warning(f"Put delta out of bounds: {greeks_data.delta}")
                        return False
            
            # Check gamma (should be non-negative)
            if greeks_data.gamma is not None:
                if greeks_data.gamma < 0:
                    logger.warning(f"Gamma should be non-negative: {greeks_data.gamma}")
                    return False
                if greeks_data.gamma > 1000:  # Unreasonably high gamma
                    logger.warning(f"Gamma unreasonably high: {greeks_data.gamma}")
                    return False
            
            # Check vega (should be non-negative)
            if greeks_data.vega is not None:
                if greeks_data.vega < 0:
                    logger.warning(f"Vega should be non-negative: {greeks_data.vega}")
                    return False
                if greeks_data.vega > 1000:  # Unreasonably high vega
                    logger.warning(f"Vega unreasonably high: {greeks_data.vega}")
                    return False
            
            # Check for NaN or infinity in calculated values
            calculated_values = [
                ('delta', greeks_data.delta),
                ('gamma', greeks_data.gamma),
                ('theta', greeks_data.theta),
                ('vega', greeks_data.vega),
                ('rho', greeks_data.rho)
            ]
            
            for name, value in calculated_values:
                if value is not None:
                    if not (value == value):  # NaN check
                        logger.warning(f"Calculated {name} is NaN")
                        return False
                    if abs(value) == float('inf'):
                        logger.warning(f"Calculated {name} is infinite")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating calculated Greeks: {str(e)}")
            return False
    
    def _calculate_d1_d2(self, greeks_data: GreeksData) -> Tuple[float, float]:
        """Calculate d1 and d2 parameters for Black-Scholes formula."""
        S = greeks_data.underlying_price
        K = greeks_data.strike
        T = greeks_data.time_to_expiry
        r = greeks_data.risk_free_rate
        sigma = max(greeks_data.volatility, self.min_volatility)
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        return d1, d2
    
    def _calculate_call_delta(self, d1: float) -> float:
        """Calculate delta for call option."""
        try:
            return norm.cdf(d1)
        except Exception as e:
            logger.warning(f"Error calculating call delta: {str(e)}")
            return 0.0
    
    def _calculate_put_delta(self, d1: float) -> float:
        """Calculate delta for put option."""
        try:
            return norm.cdf(d1) - 1.0
        except Exception as e:
            logger.warning(f"Error calculating put delta: {str(e)}")
            return 0.0
    
    def _calculate_gamma(self, greeks_data: GreeksData, d1: float) -> float:
        """Calculate gamma (same for calls and puts)."""
        try:
            S = greeks_data.underlying_price
            T = greeks_data.time_to_expiry
            sigma = max(greeks_data.volatility, self.min_volatility)
            
            return norm.pdf(d1) / (S * sigma * math.sqrt(T))
        except Exception as e:
            logger.warning(f"Error calculating gamma: {str(e)}")
            return 0.0
    
    def _calculate_call_theta(self, greeks_data: GreeksData, d1: float, d2: float) -> float:
        """Calculate theta for call option."""
        try:
            S = greeks_data.underlying_price
            K = greeks_data.strike
            T = greeks_data.time_to_expiry
            r = greeks_data.risk_free_rate
            sigma = max(greeks_data.volatility, self.min_volatility)
            
            term1 = -(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
            term2 = -r * K * math.exp(-r * T) * norm.cdf(d2)
            
            return (term1 + term2) / 365  # Convert to daily theta
        except Exception as e:
            logger.warning(f"Error calculating call theta: {str(e)}")
            return 0.0
    
    def _calculate_put_theta(self, greeks_data: GreeksData, d1: float, d2: float) -> float:
        """Calculate theta for put option."""
        try:
            S = greeks_data.underlying_price
            K = greeks_data.strike
            T = greeks_data.time_to_expiry
            r = greeks_data.risk_free_rate
            sigma = max(greeks_data.volatility, self.min_volatility)
            
            term1 = -(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
            term2 = r * K * math.exp(-r * T) * norm.cdf(-d2)
            
            return (term1 + term2) / 365  # Convert to daily theta
        except Exception as e:
            logger.warning(f"Error calculating put theta: {str(e)}")
            return 0.0
    
    def _calculate_vega(self, greeks_data: GreeksData, d1: float) -> float:
        """Calculate vega (same for calls and puts)."""
        try:
            S = greeks_data.underlying_price
            T = greeks_data.time_to_expiry
            
            return S * norm.pdf(d1) * math.sqrt(T) / 100  # Divide by 100 for 1% vol change
        except Exception as e:
            logger.warning(f"Error calculating vega: {str(e)}")
            return 0.0
    
    def _calculate_rho(self, greeks_data: GreeksData, d2: float) -> float:
        """Calculate rho for option."""
        try:
            K = greeks_data.strike
            T = greeks_data.time_to_expiry
            r = greeks_data.risk_free_rate
            
            if greeks_data.option_type.lower() == 'call':
                return K * T * math.exp(-r * T) * norm.cdf(d2) / 100
            else:  # put option
                return -K * T * math.exp(-r * T) * norm.cdf(-d2) / 100
        except Exception as e:
            logger.warning(f"Error calculating rho: {str(e)}")
            return 0.0
    
    def calculate_batch_greeks(self, greeks_data_list: list) -> list:
        """
        Calculate Greeks for a batch of options data.
        
        Args:
            greeks_data_list: List of GreeksData objects
            
        Returns:
            List of GreeksData objects with calculated Greeks
        """
        try:
            logger.info(f"Calculating Greeks for {len(greeks_data_list)} options")
            
            calculated_data = []
            for data in greeks_data_list:
                calculated_data.append(self.calculate_all_greeks(data))
            
            return calculated_data
            
        except Exception as e:
            logger.error(f"Error in batch Greeks calculation: {str(e)}")
            return greeks_data_list
    
    def invalidate_cache(self, ticker: str = None):
        """
        Invalidate Greeks calculation cache for a specific ticker or all.
        
        Args:
            ticker: Ticker symbol to invalidate cache for, or None for all
        """
        if ticker:
            _cache_manager.invalidate_cache(pattern=ticker)
            logger.info(f"Invalidated Greeks cache for ticker: {ticker}")
        else:
            _cache_manager.invalidate_cache()
            logger.info("Invalidated all Greeks cache")
    
    def get_cache_stats(self) -> dict:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return _cache_manager.get_cache_stats()
    
    @staticmethod
    def clear_expired_cache():
        """Remove expired cache entries to free memory."""
        expired_keys = []
        for key in _cache_manager.cache.keys():
            if not _cache_manager.is_cache_valid(key):
                expired_keys.append(key)
        
        for key in expired_keys:
            _cache_manager.cache.pop(key, None)
            _cache_manager.cache_timestamps.pop(key, None)
        
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)