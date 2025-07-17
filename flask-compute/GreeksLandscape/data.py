"""
Data fetching and processing module for Greeks calculations.

This module handles fetching options data and integrating with Greeks calculations,
including caching mechanisms for performance optimization.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import numpy as np
import pandas as pd
import os
import sys
from math import log, sqrt, exp
from scipy.stats import norm

# Add parent directory to path for database imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from db import SessionLocal, OptionData, UnderlyingData, engine
from .exceptions import DataNotAvailableError, DatabaseError, ValidationError
from .performance_monitor import performance_monitor, monitor_performance

logger = logging.getLogger(__name__)


@dataclass
class GreeksData:
    """Data structure for storing calculated Greeks values."""
    strike: float
    expiry: datetime
    time_to_expiry: float  # in years
    underlying_price: float
    risk_free_rate: float
    volatility: float
    option_type: str  # 'call' or 'put'
    
    # Greeks values
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None


@dataclass
class OptionsChainData:
    """Data structure for options chain information."""
    ticker: str
    underlying_price: float
    options: List[Dict[str, Any]]
    fetch_date: datetime


class GreeksDataFetcher:
    """
    Handles fetching options data and preparing it for Greeks calculations.
    
    This class integrates with the existing OptionData model and provides
    caching mechanisms for performance optimization.
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_expiry = timedelta(minutes=15)  # Cache for 15 minutes
        self.underlying_cache = {}
        self.underlying_cache_expiry = timedelta(minutes=1)  # Cache underlying prices for 1 minute
        
    @monitor_performance('options_data_fetch')
    def fetch_options_chain(
        self, 
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> OptionsChainData:
        """
        Fetch options chain data for a given ticker from the database.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date for options data
            end_date: End date for options data
            
        Returns:
            OptionsChainData object containing live options information
            
        Raises:
            DataNotAvailableError: When no options data is found
            DatabaseError: When database operations fail
        """
        try:
            logger.info(f"Fetching live options chain for {ticker}")
            
            # Check cache first
            cache_key = f"{ticker}_{start_date}_{end_date}"
            if self._is_cached_valid(cache_key):
                logger.info(f"Using cached data for {ticker}")
                return self.cache[cache_key]['data']
            
            # Fetch underlying price
            try:
                underlying_price = self._get_underlying_price(ticker)
            except ValueError as e:
                raise DataNotAvailableError(
                    f"No underlying price data for {ticker}: {str(e)}",
                    ticker=ticker,
                    user_message=f"No price data available for {ticker}. Please verify the ticker symbol."
                )
            except Exception as e:
                raise DatabaseError(
                    f"Database error fetching underlying price for {ticker}: {str(e)}",
                    user_message="Database connection error. Please try again later."
                )
            
            # Fetch options data from database
            try:
                options_list = self._get_options_data(ticker, start_date, end_date)
            except Exception as e:
                raise DatabaseError(
                    f"Database error fetching options data for {ticker}: {str(e)}",
                    user_message="Unable to fetch options data. Please try again later."
                )
            
            if not options_list:
                raise DataNotAvailableError(
                    f"No options data found for {ticker}",
                    ticker=ticker,
                    user_message=f"No options data available for {ticker}. This ticker may not have listed options."
                )
            
            # Create options chain data
            options_data = OptionsChainData(
                ticker=ticker,
                underlying_price=underlying_price,
                options=options_list,
                fetch_date=datetime.now()
            )
            
            # Cache the result
            self.cache[cache_key] = {
                'data': options_data,
                'timestamp': datetime.now()
            }
            
            logger.info(f"Fetched {len(options_list)} options for {ticker}")
            return options_data
            
        except (DataNotAvailableError, DatabaseError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching options chain for {ticker}: {str(e)}")
            raise DatabaseError(
                f"Unexpected database error for {ticker}: {str(e)}",
                user_message="An unexpected error occurred while fetching data. Please try again."
            )
    
    def prepare_greeks_data(
        self, 
        options_chain: OptionsChainData,
        risk_free_rate: float = 0.05
    ) -> List[GreeksData]:
        """
        Prepare options data for Greeks calculations.
        
        Args:
            options_chain: Options chain data
            risk_free_rate: Risk-free interest rate (default 5%)
            
        Returns:
            List of GreeksData objects ready for calculation
        """
        try:
            greeks_data_list = []
            
            for option in options_chain.options:
                # Calculate time to expiry in years
                expiry_date = option.get('expiry')
                if isinstance(expiry_date, str):
                    expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                elif isinstance(expiry_date, datetime):
                    expiry_date = expiry_date.date()
                
                time_to_expiry = (expiry_date - datetime.now().date()).days / 365.0
                
                # Skip expired options
                if time_to_expiry <= 0:
                    continue
                
                greeks_data = GreeksData(
                    strike=float(option.get('strike', 0)),
                    expiry=expiry_date,
                    time_to_expiry=time_to_expiry,
                    underlying_price=options_chain.underlying_price,
                    risk_free_rate=risk_free_rate,
                    volatility=float(option.get('implied_volatility', 0.2)),
                    option_type=option.get('type', 'call').lower()
                )
                
                greeks_data_list.append(greeks_data)
            
            logger.info(f"Prepared {len(greeks_data_list)} options for Greeks calculation")
            return greeks_data_list
            
        except Exception as e:
            logger.error(f"Error preparing Greeks data: {str(e)}")
            raise
    
    def create_greeks_surface_data(
        self, 
        greeks_data_list: List[GreeksData]
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        """
        Create surface data arrays for 3D plotting.
        
        Args:
            greeks_data_list: List of GreeksData with calculated Greeks
            
        Returns:
            Tuple of (strikes_grid, expiries_grid, greeks_surfaces_dict)
        """
        try:
            if not greeks_data_list:
                return np.array([]), np.array([]), {}
            
            # Extract unique strikes and expiries
            strikes = sorted(list(set(data.strike for data in greeks_data_list)))
            expiries = sorted(list(set(data.time_to_expiry for data in greeks_data_list)))
            
            # Create meshgrid
            strikes_grid, expiries_grid = np.meshgrid(strikes, expiries)
            
            # Initialize Greeks surfaces
            greeks_surfaces = {
                'delta': np.zeros_like(strikes_grid),
                'gamma': np.zeros_like(strikes_grid),
                'theta': np.zeros_like(strikes_grid),
                'vega': np.zeros_like(strikes_grid)
            }
            
            # Fill in the Greeks values
            for data in greeks_data_list:
                try:
                    strike_idx = strikes.index(data.strike)
                    expiry_idx = expiries.index(data.time_to_expiry)
                    
                    if data.delta is not None:
                        greeks_surfaces['delta'][expiry_idx, strike_idx] = data.delta
                    if data.gamma is not None:
                        greeks_surfaces['gamma'][expiry_idx, strike_idx] = data.gamma
                    if data.theta is not None:
                        greeks_surfaces['theta'][expiry_idx, strike_idx] = data.theta
                    if data.vega is not None:
                        greeks_surfaces['vega'][expiry_idx, strike_idx] = data.vega
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error placing Greeks data point: {str(e)}")
                    continue
            
            return strikes_grid, expiries_grid, greeks_surfaces
            
        except Exception as e:
            logger.error(f"Error creating surface data: {str(e)}")
            raise
    
    def _get_underlying_price(self, ticker: str) -> float:
        """Fetch the latest underlying price from the database with caching."""
        try:
            # Check cache first
            if self._is_underlying_cached_valid(ticker):
                logger.debug(f"Using cached underlying price for {ticker}")
                return self.underlying_cache[ticker]['price']
            
            session = SessionLocal()
            record = session.query(UnderlyingData).filter(
                UnderlyingData.ticker == ticker
            ).order_by(UnderlyingData.date.desc()).first()
            session.close()
            
            if record:
                price = float(record.close)
                
                # Cache the result
                self.underlying_cache[ticker] = {
                    'price': price,
                    'timestamp': datetime.now()
                }
                
                logger.debug(f"Cached underlying price for {ticker}: ${price:.2f}")
                return price
            else:
                logger.warning(f"No underlying price data found for {ticker}")
                raise ValueError(f"No underlying price data available for {ticker}")
                
        except Exception as e:
            logger.error(f"Error fetching underlying price for {ticker}: {str(e)}")
            raise
    
    @monitor_performance('database_query')
    def _get_options_data(
        self, 
        ticker: str, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch options data from the database and calculate implied volatilities."""
        try:
            # Update database pool stats for monitoring
            performance_monitor.update_db_pool_stats(engine)
            
            session = SessionLocal()
            
            # Optimized query using composite indexes
            # Use idx_option_ticker_expiry for efficient filtering
            query = session.query(OptionData).filter(OptionData.ticker == ticker)
            
            # Apply date filters if provided - this will use idx_option_ticker_expiry index
            if start_date:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                query = query.filter(OptionData.expiration_date >= start_date_obj)
            if end_date:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                query = query.filter(OptionData.expiration_date <= end_date_obj)
            
            # Order by expiration_date and strike for better performance
            # This helps with index usage and makes processing more predictable
            query = query.order_by(OptionData.expiration_date, OptionData.strike)
            
            # Execute query and fetch all results
            records = query.all()
            session.close()
            
            if not records:
                logger.warning(f"No options data found for {ticker}")
                return []
            
            # Get underlying price for implied volatility calculations
            underlying_price = self._get_underlying_price(ticker)
            
            options_list = []
            for record in records:
                # Calculate time to expiry
                time_to_expiry = (record.expiration_date - datetime.now().date()).days / 365.0
                
                # Skip expired options
                if time_to_expiry <= 0:
                    continue
                
                # Calculate option price (mid of bid/ask or last price)
                bid = float(record.bid) if record.bid else 0
                ask = float(record.ask) if record.ask else 0
                last_price = float(record.last_price) if record.last_price else 0
                
                if bid > 0 and ask > 0:
                    option_price = (bid + ask) / 2
                elif last_price > 0:
                    option_price = last_price
                else:
                    continue  # Skip if no valid price
                
                # Calculate implied volatility
                implied_vol = self._calculate_implied_volatility(
                    option_price=option_price,
                    underlying_price=underlying_price,
                    strike=float(record.strike),
                    time_to_expiry=time_to_expiry,
                    option_type=record.option_type.lower(),
                    risk_free_rate=0.05
                )
                
                # Create option data dictionary
                option_data = {
                    'strike': float(record.strike),
                    'expiry': record.expiration_date,
                    'type': record.option_type.lower(),
                    'bid': bid,
                    'ask': ask,
                    'last_price': last_price,
                    'option_price': option_price,
                    'implied_volatility': implied_vol,
                    'time_to_expiry': time_to_expiry
                }
                
                options_list.append(option_data)
            
            logger.info(f"Processed {len(options_list)} valid options for {ticker}")
            return options_list
            
        except Exception as e:
            logger.error(f"Error fetching options data for {ticker}: {str(e)}")
            raise
    
    def _calculate_implied_volatility(
        self,
        option_price: float,
        underlying_price: float,
        strike: float,
        time_to_expiry: float,
        option_type: str,
        risk_free_rate: float = 0.05,
        tol: float = 1e-6,
        max_iter: int = 100
    ) -> float:
        """
        Calculate implied volatility using Newton-Raphson method.
        
        Args:
            option_price: Market price of the option
            underlying_price: Current underlying asset price
            strike: Strike price of the option
            time_to_expiry: Time to expiry in years
            option_type: 'call' or 'put'
            risk_free_rate: Risk-free interest rate
            tol: Convergence tolerance
            max_iter: Maximum iterations
            
        Returns:
            Implied volatility as a decimal (e.g., 0.20 for 20%)
        """
        try:
            # Check for intrinsic value floor
            if option_type == 'call':
                intrinsic_value = max(0.0, underlying_price - strike * exp(-risk_free_rate * time_to_expiry))
            else:  # put
                intrinsic_value = max(0.0, strike * exp(-risk_free_rate * time_to_expiry) - underlying_price)
            
            if option_price < intrinsic_value:
                logger.warning(f"Option price {option_price} below intrinsic value {intrinsic_value}")
                return 0.20  # Return default 20% volatility
            
            # Initial guess (20% volatility)
            sigma = 0.20
            
            for _ in range(max_iter):
                # Calculate option price with current volatility guess
                price_guess = self._black_scholes_price(
                    underlying_price, strike, time_to_expiry, risk_free_rate, sigma, option_type
                )
                
                diff = price_guess - option_price
                
                if abs(diff) < tol:
                    return max(sigma, 0.001)  # Minimum 0.1% volatility
                
                # Calculate vega for Newton-Raphson update
                vega = self._calculate_vega_for_iv(
                    underlying_price, strike, time_to_expiry, risk_free_rate, sigma
                )
                
                if vega < 1e-8:  # Avoid division by very small vega
                    break
                
                # Newton-Raphson update
                sigma -= diff / vega
                
                # Keep sigma in reasonable range
                sigma = max(min(sigma, 5.0), 0.001)  # Between 0.1% and 500%
            
            return max(sigma, 0.001)  # Return last iteration with minimum bound
            
        except Exception as e:
            logger.warning(f"Error calculating implied volatility: {str(e)}")
            return 0.20  # Return default 20% volatility
    
    def _black_scholes_price(
        self, 
        S: float, 
        K: float, 
        T: float, 
        r: float, 
        sigma: float, 
        option_type: str
    ) -> float:
        """Calculate Black-Scholes option price."""
        try:
            if T <= 0 or sigma <= 0:
                return max(0.0, S - K) if option_type == 'call' else max(0.0, K - S)
            
            d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
            d2 = d1 - sigma * sqrt(T)
            
            if option_type == 'call':
                return S * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
            else:  # put
                return K * exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
                
        except Exception as e:
            logger.warning(f"Error in Black-Scholes calculation: {str(e)}")
            return 0.0
    
    def _calculate_vega_for_iv(
        self, 
        S: float, 
        K: float, 
        T: float, 
        r: float, 
        sigma: float
    ) -> float:
        """Calculate vega for implied volatility calculation."""
        try:
            if T <= 0 or sigma <= 0:
                return 0.0
            
            d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
            return S * norm.pdf(d1) * sqrt(T)
            
        except Exception as e:
            logger.warning(f"Error calculating vega: {str(e)}")
            return 0.0
    
    def _is_cached_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache[cache_key]['timestamp']
        return datetime.now() - cache_time < self.cache_expiry
    
    def _is_underlying_cached_valid(self, ticker: str) -> bool:
        """Check if cached underlying price is still valid."""
        if ticker not in self.underlying_cache:
            return False
        
        cache_time = self.underlying_cache[ticker]['timestamp']
        return datetime.now() - cache_time < self.underlying_cache_expiry
    
    def invalidate_options_cache(self, ticker: str = None):
        """
        Invalidate options data cache for stale data.
        
        Args:
            ticker: Specific ticker to invalidate, or None for all
        """
        if ticker:
            # Remove all cache entries for this ticker
            keys_to_remove = [key for key in self.cache.keys() if key.startswith(f"{ticker}_")]
            for key in keys_to_remove:
                self.cache.pop(key, None)
            
            # Also remove underlying price cache
            self.underlying_cache.pop(ticker, None)
            
            logger.info(f"Invalidated options cache for ticker: {ticker}")
        else:
            # Clear all caches
            self.cache.clear()
            self.underlying_cache.clear()
            logger.info("Invalidated all options cache")
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics for performance monitoring.
        
        Returns:
            Dictionary with cache performance metrics
        """
        total_options_cache = len(self.cache)
        valid_options_cache = sum(1 for key in self.cache.keys() if self._is_cached_valid(key))
        
        total_underlying_cache = len(self.underlying_cache)
        valid_underlying_cache = sum(1 for ticker in self.underlying_cache.keys() if self._is_underlying_cached_valid(ticker))
        
        return {
            'options_cache': {
                'total_entries': total_options_cache,
                'valid_entries': valid_options_cache,
                'expired_entries': total_options_cache - valid_options_cache
            },
            'underlying_cache': {
                'total_entries': total_underlying_cache,
                'valid_entries': valid_underlying_cache,
                'expired_entries': total_underlying_cache - valid_underlying_cache
            }
        }
    
    def clear_expired_cache(self):
        """Remove expired cache entries to free memory."""
        # Clear expired options cache
        expired_options_keys = [key for key in self.cache.keys() if not self._is_cached_valid(key)]
        for key in expired_options_keys:
            self.cache.pop(key, None)
        
        # Clear expired underlying cache
        expired_underlying_keys = [ticker for ticker in self.underlying_cache.keys() if not self._is_underlying_cached_valid(ticker)]
        for ticker in expired_underlying_keys:
            self.underlying_cache.pop(ticker, None)
        
        total_cleared = len(expired_options_keys) + len(expired_underlying_keys)
        if total_cleared > 0:
            logger.info(f"Cleared {total_cleared} expired cache entries ({len(expired_options_keys)} options, {len(expired_underlying_keys)} underlying)")
        
        return total_cleared