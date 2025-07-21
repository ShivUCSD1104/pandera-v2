"""
Input validation module for Greeks Landscape.

This module provides comprehensive validation for ticker symbols, date ranges,
and other input parameters with user-friendly error messages.
"""

import re
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple, Union
import logging

from .exceptions import ValidationError

logger = logging.getLogger(__name__)


class InputValidator:
    """
    Comprehensive input validator for Greeks Landscape parameters.
    
    Provides validation for ticker symbols, date ranges, and other parameters
    with detailed error messages for both logging and user display.
    """
    
    # Valid ticker symbol pattern (1-5 uppercase letters, optional numbers)
    TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}[0-9]*$')
    
    # Supported ticker symbols (can be expanded)
    SUPPORTED_TICKERS = {
        'AAPL', 'GOOGL', 'GOOG', 'MSFT', 'TSLA', 'NVDA', 'AMZN', 'META', 'NFLX', 'AMD',
        'INTC', 'CRM', 'ORCL', 'ADBE', 'PYPL', 'UBER', 'LYFT', 'SNAP', 'TWTR', 'SQ',
        'ROKU', 'ZM', 'DOCU', 'SHOP', 'SPOT', 'PINS', 'DKNG', 'PLTR', 'COIN', 'HOOD',
        'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO', 'VEA', 'VWO', 'BND', 'AGG'
    }
    
    # Valid Greeks view options
    VALID_GREEKS_VIEWS = {'Delta', 'Gamma', 'Theta', 'Vega', 'All'}
    
    def __init__(self):
        self.max_date_range_days = 365 * 2  # Maximum 2 years
        self.min_date_range_days = 1        # Minimum 1 day
        self.max_future_date_years = 3      # Maximum 3 years in future
    
    def validate_ticker(self, ticker: str) -> str:
        """
        Validate ticker symbol format and availability.
        
        Args:
            ticker: Stock ticker symbol to validate
            
        Returns:
            Normalized ticker symbol (uppercase)
            
        Raises:
            ValidationError: If ticker is invalid
        """
        if not ticker:
            raise ValidationError(
                "Ticker symbol is required",
                field="ticker",
                user_message="Please provide a valid ticker symbol (e.g., AAPL, GOOGL)"
            )
        
        # Normalize to uppercase
        ticker = ticker.strip().upper()
        
        # Check format
        if not self.TICKER_PATTERN.match(ticker):
            raise ValidationError(
                f"Invalid ticker format: {ticker}",
                field="ticker",
                user_message=f"'{ticker}' is not a valid ticker format. Use 1-5 uppercase letters (e.g., AAPL, GOOGL)"
            )
        
        # Check if ticker is in supported list (optional - can be disabled for broader support)
        if ticker not in self.SUPPORTED_TICKERS:
            logger.warning(f"Ticker {ticker} not in supported list, but allowing through")
            # Don't raise error - just log warning to allow broader ticker support
        
        return ticker
    
    def validate_greeks_view(self, greeks_view: str) -> str:
        """
        Validate Greeks view parameter.
        
        Args:
            greeks_view: Greeks view option to validate
            
        Returns:
            Validated Greeks view
            
        Raises:
            ValidationError: If Greeks view is invalid
        """
        if not greeks_view:
            return 'All'  # Default value
        
        if greeks_view not in self.VALID_GREEKS_VIEWS:
            raise ValidationError(
                f"Invalid Greeks view: {greeks_view}",
                field="greeks_view",
                user_message=f"Greeks view must be one of: {', '.join(self.VALID_GREEKS_VIEWS)}"
            )
        
        return greeks_view
    
    def validate_date_string(self, date_str: str, field_name: str) -> date:
        """
        Validate and parse date string.
        
        Args:
            date_str: Date string to validate (YYYY-MM-DD format)
            field_name: Name of the field for error messages
            
        Returns:
            Parsed date object
            
        Raises:
            ValidationError: If date format is invalid
        """
        if not date_str:
            return None
        
        try:
            # Try multiple date formats
            date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y%m%d']
            parsed_date = None
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt).date()
                    break
                except ValueError:
                    continue
            
            if parsed_date is None:
                raise ValueError("No valid format found")
            
            return parsed_date
            
        except ValueError:
            raise ValidationError(
                f"Invalid date format for {field_name}: {date_str}",
                field=field_name,
                user_message=f"Please use YYYY-MM-DD format for {field_name} (e.g., 2024-12-31)"
            )
    
    def validate_date_range(
        self, 
        start_date: Optional[Union[str, date]], 
        end_date: Optional[Union[str, date]]
    ) -> Tuple[Optional[date], Optional[date]]:
        """
        Validate date range for options data.
        
        Args:
            start_date: Start date (string or date object)
            end_date: End date (string or date object)
            
        Returns:
            Tuple of (validated_start_date, validated_end_date)
            
        Raises:
            ValidationError: If date range is invalid
        """
        # Parse dates if they are strings
        if isinstance(start_date, str):
            start_date = self.validate_date_string(start_date, "start_date")
        if isinstance(end_date, str):
            end_date = self.validate_date_string(end_date, "end_date")
        
        today = date.today()
        max_future_date = today + timedelta(days=self.max_future_date_years * 365)
        
        # Validate start date
        if start_date:
            if start_date > max_future_date:
                raise ValidationError(
                    f"Start date too far in future: {start_date}",
                    field="start_date",
                    user_message=f"Start date cannot be more than {self.max_future_date_years} years in the future"
                )
        
        # Validate end date
        if end_date:
            if end_date > max_future_date:
                raise ValidationError(
                    f"End date too far in future: {end_date}",
                    field="end_date", 
                    user_message=f"End date cannot be more than {self.max_future_date_years} years in the future"
                )
        
        # Validate date range relationship
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError(
                    f"Start date {start_date} is after end date {end_date}",
                    field="date_range",
                    user_message="Start date must be before or equal to end date"
                )
            
            # Check date range is not too large
            date_diff = (end_date - start_date).days
            if date_diff > self.max_date_range_days:
                raise ValidationError(
                    f"Date range too large: {date_diff} days",
                    field="date_range",
                    user_message=f"Date range cannot exceed {self.max_date_range_days} days ({self.max_date_range_days // 365} years)"
                )
            
            if date_diff < self.min_date_range_days:
                raise ValidationError(
                    f"Date range too small: {date_diff} days",
                    field="date_range",
                    user_message=f"Date range must be at least {self.min_date_range_days} day(s)"
                )
        
        return start_date, end_date
    
    def validate_numerical_parameter(
        self, 
        value: Union[str, int, float], 
        param_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        allow_zero: bool = True
    ) -> float:
        """
        Validate numerical parameters.
        
        Args:
            value: Value to validate
            param_name: Parameter name for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            allow_zero: Whether zero is allowed
            
        Returns:
            Validated numerical value
            
        Raises:
            ValidationError: If value is invalid
        """
        if value is None:
            raise ValidationError(
                f"{param_name} is required",
                field=param_name,
                user_message=f"Please provide a valid {param_name}"
            )
        
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"Invalid {param_name}: {value}",
                field=param_name,
                user_message=f"{param_name} must be a valid number"
            )
        
        # Check for NaN or infinity
        if not (num_value == num_value):  # NaN check
            raise ValidationError(
                f"{param_name} cannot be NaN",
                field=param_name,
                user_message=f"{param_name} must be a valid number"
            )
        
        if abs(num_value) == float('inf'):
            raise ValidationError(
                f"{param_name} cannot be infinite",
                field=param_name,
                user_message=f"{param_name} must be a finite number"
            )
        
        # Check zero
        if not allow_zero and num_value == 0:
            raise ValidationError(
                f"{param_name} cannot be zero",
                field=param_name,
                user_message=f"{param_name} must be greater than zero"
            )
        
        # Check range
        if min_value is not None and num_value < min_value:
            raise ValidationError(
                f"{param_name} {num_value} below minimum {min_value}",
                field=param_name,
                user_message=f"{param_name} must be at least {min_value}"
            )
        
        if max_value is not None and num_value > max_value:
            raise ValidationError(
                f"{param_name} {num_value} above maximum {max_value}",
                field=param_name,
                user_message=f"{param_name} must be at most {max_value}"
            )
        
        return num_value
    
    def validate_all_parameters(
        self,
        ticker: str,
        greeks_view: str = 'All',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict:
        """
        Validate all input parameters for Greeks Landscape.
        
        Args:
            ticker: Stock ticker symbol
            greeks_view: Greeks view option
            start_date: Start date string
            end_date: End date string
            
        Returns:
            Dictionary of validated parameters
            
        Raises:
            ValidationError: If any parameter is invalid
        """
        try:
            validated_params = {}
            
            # Validate ticker
            validated_params['ticker'] = self.validate_ticker(ticker)
            
            # Validate Greeks view
            validated_params['greeks_view'] = self.validate_greeks_view(greeks_view)
            
            # Validate date range
            start_date_obj, end_date_obj = self.validate_date_range(start_date, end_date)
            validated_params['start_date'] = start_date_obj
            validated_params['end_date'] = end_date_obj
            
            logger.info(f"Successfully validated parameters: {validated_params}")
            return validated_params
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during validation: {str(e)}")
            raise ValidationError(
                f"Parameter validation failed: {str(e)}",
                user_message="Invalid parameters provided. Please check your inputs and try again."
            )
    
    def get_validation_summary(self) -> dict:
        """
        Get summary of validation rules for documentation/help.
        
        Returns:
            Dictionary containing validation rules and constraints
        """
        return {
            'ticker': {
                'format': 'Uppercase letters (1-5 characters), optional numbers',
                'examples': ['AAPL', 'GOOGL', 'MSFT'],
                'supported_count': len(self.SUPPORTED_TICKERS)
            },
            'greeks_view': {
                'options': list(self.VALID_GREEKS_VIEWS),
                'default': 'All'
            },
            'date_range': {
                'format': 'YYYY-MM-DD',
                'max_range_days': self.max_date_range_days,
                'max_future_years': self.max_future_date_years,
                'examples': ['2024-01-01', '2024-12-31']
            }
        }


# Global validator instance
validator = InputValidator()