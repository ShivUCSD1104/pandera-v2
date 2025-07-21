"""
Comprehensive tests for error handling and validation in Greeks Landscape module.

This module tests input validation, error scenarios, edge cases, and user-friendly
error messages for the Greeks Landscape functionality.
"""

import unittest
import logging
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
if grandparent_dir not in sys.path:
    sys.path.insert(0, grandparent_dir)

from GreeksLandscape.main import generate_greeks_landscape_html
from GreeksLandscape.validators import validator, InputValidator
from GreeksLandscape.exceptions import (
    ValidationError, DataNotAvailableError, CalculationError, 
    DatabaseError, GreeksLandscapeError
)
from GreeksLandscape.data import GreeksDataFetcher, GreeksData
from GreeksLandscape.greeks_calculator import GreeksCalculator

# Disable logging during tests to reduce noise
logging.disable(logging.CRITICAL)


class TestInputValidation(unittest.TestCase):
    """Test input validation functionality."""
    
    def setUp(self):
        self.validator = InputValidator()
    
    def test_valid_ticker_symbols(self):
        """Test validation of valid ticker symbols."""
        valid_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'SPY']
        
        for ticker in valid_tickers:
            with self.subTest(ticker=ticker):
                result = self.validator.validate_ticker(ticker)
                self.assertEqual(result, ticker.upper())
    
    def test_invalid_ticker_symbols(self):
        """Test validation of invalid ticker symbols."""
        invalid_tickers = [
            ('', 'empty string'),
            ('   ', 'whitespace only'),
            ('123', 'numbers only'),
            ('TOOLONG', 'too long'),
            ('aa', 'lowercase'),
            ('A@PL', 'special characters'),
            (None, 'None value')
        ]
        
        for ticker, description in invalid_tickers:
            with self.subTest(ticker=ticker, description=description):
                with self.assertRaises(ValidationError) as context:
                    self.validator.validate_ticker(ticker)
                
                error = context.exception
                self.assertEqual(error.error_type, 'validation_error')
                self.assertIsNotNone(error.user_message)
                self.assertEqual(error.field, 'ticker')
    
    def test_greeks_view_validation(self):
        """Test validation of Greeks view parameters."""
        valid_views = ['Delta', 'Gamma', 'Theta', 'Vega', 'All']
        
        for view in valid_views:
            with self.subTest(view=view):
                result = self.validator.validate_greeks_view(view)
                self.assertEqual(result, view)
        
        # Test default value
        result = self.validator.validate_greeks_view('')
        self.assertEqual(result, 'All')
        
        result = self.validator.validate_greeks_view(None)
        self.assertEqual(result, 'All')
        
        # Test invalid view
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_greeks_view('InvalidView')
        
        error = context.exception
        self.assertEqual(error.error_type, 'validation_error')
        self.assertEqual(error.field, 'greeks_view')
    
    def test_date_string_validation(self):
        """Test validation of date strings."""
        valid_dates = [
            ('2024-01-01', date(2024, 1, 1)),
            ('2024-12-31', date(2024, 12, 31)),
            ('01/01/2024', date(2024, 1, 1)),
            ('31/12/2024', date(2024, 12, 31)),
            ('20240101', date(2024, 1, 1))
        ]
        
        for date_str, expected_date in valid_dates:
            with self.subTest(date_str=date_str):
                result = self.validator.validate_date_string(date_str, 'test_date')
                self.assertEqual(result, expected_date)
        
        # Test invalid dates
        invalid_dates = [
            'invalid-date',
            '2024-13-01',  # Invalid month
            '2024-01-32',  # Invalid day
            '24-01-01',    # Invalid year format
            'not-a-date'
        ]
        
        for date_str in invalid_dates:
            with self.subTest(date_str=date_str):
                with self.assertRaises(ValidationError) as context:
                    self.validator.validate_date_string(date_str, 'test_date')
                
                error = context.exception
                self.assertEqual(error.error_type, 'validation_error')
                self.assertEqual(error.field, 'test_date')
    
    def test_date_range_validation(self):
        """Test validation of date ranges."""
        today = date.today()
        future_date = today + timedelta(days=30)
        far_future = today + timedelta(days=365 * 4)  # 4 years in future
        
        # Valid date range
        start_date, end_date = self.validator.validate_date_range(
            today.strftime('%Y-%m-%d'),
            future_date.strftime('%Y-%m-%d')
        )
        self.assertEqual(start_date, today)
        self.assertEqual(end_date, future_date)
        
        # Test start date after end date
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_date_range(
                future_date.strftime('%Y-%m-%d'),
                today.strftime('%Y-%m-%d')
            )
        
        error = context.exception
        self.assertEqual(error.field, 'date_range')
        
        # Test date too far in future
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_date_range(
                far_future.strftime('%Y-%m-%d'),
                None
            )
        
        error = context.exception
        self.assertEqual(error.field, 'start_date')
    
    def test_numerical_parameter_validation(self):
        """Test validation of numerical parameters."""
        # Valid numbers
        valid_values = [1.0, 100, '50.5', '0']
        
        for value in valid_values:
            with self.subTest(value=value):
                result = self.validator.validate_numerical_parameter(
                    value, 'test_param', min_value=0, max_value=1000
                )
                self.assertIsInstance(result, float)
                self.assertGreaterEqual(result, 0)
                self.assertLessEqual(result, 1000)
        
        # Invalid numbers
        invalid_values = [
            ('not_a_number', 'string'),
            (None, 'None'),
            (float('nan'), 'NaN'),
            (float('inf'), 'infinity'),
            (-1, 'below minimum'),
            (1001, 'above maximum')
        ]
        
        for value, description in invalid_values:
            with self.subTest(value=value, description=description):
                with self.assertRaises(ValidationError):
                    self.validator.validate_numerical_parameter(
                        value, 'test_param', min_value=0, max_value=1000
                    )
    
    def test_all_parameters_validation(self):
        """Test comprehensive parameter validation."""
        # Valid parameters
        valid_params = self.validator.validate_all_parameters(
            ticker='AAPL',
            greeks_view='Delta',
            start_date='2024-01-01',
            end_date='2024-12-31'
        )
        
        self.assertEqual(valid_params['ticker'], 'AAPL')
        self.assertEqual(valid_params['greeks_view'], 'Delta')
        self.assertEqual(valid_params['start_date'], date(2024, 1, 1))
        self.assertEqual(valid_params['end_date'], date(2024, 12, 31))
        
        # Invalid ticker should raise ValidationError
        with self.assertRaises(ValidationError):
            self.validator.validate_all_parameters(
                ticker='INVALID@TICKER',
                greeks_view='All'
            )


class TestDataFetchingErrors(unittest.TestCase):
    """Test error handling in data fetching operations."""
    
    def setUp(self):
        self.data_fetcher = GreeksDataFetcher()
    
    @patch('GreeksLandscape.data.SessionLocal')
    def test_database_connection_error(self, mock_session):
        """Test handling of database connection errors."""
        # Mock database connection failure
        mock_session.side_effect = Exception("Database connection failed")
        
        with self.assertRaises(DatabaseError) as context:
            self.data_fetcher.fetch_options_chain('AAPL')
        
        error = context.exception
        self.assertEqual(error.error_type, 'database_error')
        self.assertIn('Database connection error', error.user_message)
    
    @patch('GreeksLandscape.data.SessionLocal')
    def test_no_underlying_price_data(self, mock_session):
        """Test handling when no underlying price data is available."""
        # Mock empty query result for underlying data
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        with self.assertRaises(DataNotAvailableError) as context:
            self.data_fetcher.fetch_options_chain('INVALID_TICKER')
        
        error = context.exception
        self.assertEqual(error.error_type, 'data_error')
        self.assertIn('No price data available', error.user_message)
    
    @patch('GreeksLandscape.data.SessionLocal')
    def test_no_options_data(self, mock_session):
        """Test handling when no options data is available."""
        # Mock underlying price but no options data
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        
        # Mock underlying price query
        mock_underlying = MagicMock()
        mock_underlying.close = 100.0
        mock_session_instance.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_underlying
        
        # Mock empty options query
        mock_session_instance.query.return_value.filter.return_value.all.return_value = []
        
        with self.assertRaises(DataNotAvailableError) as context:
            self.data_fetcher.fetch_options_chain('NO_OPTIONS_TICKER')
        
        error = context.exception
        self.assertEqual(error.error_type, 'data_error')
        self.assertIn('No options data available', error.user_message)
    
    def test_invalid_options_data_preparation(self):
        """Test handling of invalid options data during preparation."""
        from GreeksLandscape.data import OptionsChainData
        
        # Create options chain with invalid data
        invalid_options = [
            {'strike': 'invalid', 'expiry': '2024-01-01', 'type': 'call'},
            {'strike': 100, 'expiry': 'invalid_date', 'type': 'call'},
            {'strike': -50, 'expiry': '2024-01-01', 'type': 'call'}  # Negative strike
        ]
        
        options_chain = OptionsChainData(
            ticker='TEST',
            underlying_price=100.0,
            options=invalid_options,
            fetch_date=datetime.now()
        )
        
        # Should handle invalid data gracefully
        result = self.data_fetcher.prepare_greeks_data(options_chain)
        
        # Should return empty list or filtered valid data
        self.assertIsInstance(result, list)


class TestGreeksCalculationErrors(unittest.TestCase):
    """Test error handling in Greeks calculations."""
    
    def setUp(self):
        self.calculator = GreeksCalculator()
    
    def test_invalid_greeks_data_input(self):
        """Test handling of invalid GreeksData input."""
        # Test with None values
        invalid_data = GreeksData(
            strike=None,
            expiry=datetime.now().date(),
            time_to_expiry=0.25,
            underlying_price=100.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type='call'
        )
        
        with self.assertRaises(ValidationError) as context:
            self.calculator.calculate_all_greeks(invalid_data)
        
        error = context.exception
        self.assertEqual(error.error_type, 'validation_error')
    
    def test_zero_time_to_expiry(self):
        """Test handling of zero or negative time to expiry."""
        invalid_data = GreeksData(
            strike=100.0,
            expiry=datetime.now().date(),
            time_to_expiry=0.0,  # Zero time to expiry
            underlying_price=100.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type='call'
        )
        
        with self.assertRaises(ValidationError) as context:
            self.calculator.calculate_all_greeks(invalid_data)
        
        error = context.exception
        self.assertEqual(error.error_type, 'validation_error')
    
    def test_extreme_volatility_values(self):
        """Test handling of extreme volatility values."""
        # Test very high volatility
        high_vol_data = GreeksData(
            strike=100.0,
            expiry=datetime.now().date() + timedelta(days=30),
            time_to_expiry=30/365,
            underlying_price=100.0,
            risk_free_rate=0.05,
            volatility=10.0,  # 1000% volatility
            option_type='call'
        )
        
        with self.assertRaises(ValidationError) as context:
            self.calculator.calculate_all_greeks(high_vol_data)
        
        error = context.exception
        self.assertEqual(error.error_type, 'validation_error')
    
    def test_negative_prices(self):
        """Test handling of negative prices."""
        invalid_data = GreeksData(
            strike=-100.0,  # Negative strike
            expiry=datetime.now().date() + timedelta(days=30),
            time_to_expiry=30/365,
            underlying_price=100.0,
            risk_free_rate=0.05,
            volatility=0.2,
            option_type='call'
        )
        
        with self.assertRaises(ValidationError) as context:
            self.calculator.calculate_all_greeks(invalid_data)
        
        error = context.exception
        self.assertEqual(error.error_type, 'validation_error')


class TestEndToEndErrorHandling(unittest.TestCase):
    """Test end-to-end error handling in the main function."""
    
    def test_invalid_ticker_error_response(self):
        """Test error response for invalid ticker."""
        result = generate_greeks_landscape_html(
            ticker='INVALID@TICKER',
            greeks_view='All'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
        self.assertIn('type', result)
        self.assertEqual(result['type'], 'validation_error')
        self.assertIn('field', result)
        self.assertEqual(result['field'], 'ticker')
    
    def test_invalid_greeks_view_error_response(self):
        """Test error response for invalid Greeks view."""
        result = generate_greeks_landscape_html(
            ticker='AAPL',
            greeks_view='InvalidView'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
        self.assertIn('type', result)
        self.assertEqual(result['type'], 'validation_error')
        self.assertEqual(result['field'], 'greeks_view')
    
    def test_invalid_date_range_error_response(self):
        """Test error response for invalid date range."""
        result = generate_greeks_landscape_html(
            ticker='AAPL',
            greeks_view='All',
            start_date='2024-12-31',
            end_date='2024-01-01'  # End before start
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
        self.assertIn('type', result)
        self.assertEqual(result['type'], 'validation_error')
        self.assertEqual(result['field'], 'date_range')
    
    @patch('GreeksLandscape.main.GreeksDataFetcher')
    def test_data_not_available_error_response(self, mock_fetcher_class):
        """Test error response when data is not available."""
        # Mock data fetcher to raise DataNotAvailableError
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch_options_chain.side_effect = DataNotAvailableError(
            "No data available",
            ticker="TEST",
            user_message="No options data available for TEST"
        )
        
        result = generate_greeks_landscape_html(
            ticker='TEST',
            greeks_view='All'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
        self.assertIn('type', result)
        self.assertEqual(result['type'], 'data_error')
        self.assertIn('No options data available', result['error'])
    
    @patch('GreeksLandscape.main.GreeksDataFetcher')
    def test_database_error_response(self, mock_fetcher_class):
        """Test error response for database errors."""
        # Mock data fetcher to raise DatabaseError
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch_options_chain.side_effect = DatabaseError(
            "Database connection failed",
            user_message="Database connection error. Please try again later."
        )
        
        result = generate_greeks_landscape_html(
            ticker='AAPL',
            greeks_view='All'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
        self.assertIn('type', result)
        self.assertEqual(result['type'], 'database_error')
        self.assertIn('Database connection error', result['error'])
    
    def test_user_friendly_error_messages(self):
        """Test that all error messages are user-friendly."""
        test_cases = [
            ('INVALID@TICKER', 'All', None, None),
            ('AAPL', 'InvalidView', None, None),
            ('AAPL', 'All', '2024-13-01', None),  # Invalid date
            ('AAPL', 'All', '2024-12-31', '2024-01-01'),  # Invalid range
        ]
        
        for ticker, view, start_date, end_date in test_cases:
            with self.subTest(ticker=ticker, view=view, start_date=start_date, end_date=end_date):
                result = generate_greeks_landscape_html(
                    ticker=ticker,
                    greeks_view=view,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if isinstance(result, dict) and 'error' in result:
                    error_message = result['error']
                    
                    # Check that error message is user-friendly
                    self.assertIsInstance(error_message, str)
                    self.assertGreater(len(error_message), 10)  # Not too short
                    self.assertNotIn('Exception', error_message)  # No technical terms
                    self.assertNotIn('Traceback', error_message)
                    self.assertNotIn('None', error_message)  # No None values


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_very_short_time_to_expiry(self):
        """Test handling of options with very short time to expiry."""
        tomorrow = datetime.now().date() + timedelta(days=1)
        
        result = generate_greeks_landscape_html(
            ticker='AAPL',
            greeks_view='All',
            start_date=tomorrow.strftime('%Y-%m-%d'),
            end_date=tomorrow.strftime('%Y-%m-%d')
        )
        
        # Should handle gracefully, either return data or appropriate error
        self.assertIsInstance(result, (dict, str))
    
    def test_very_long_time_to_expiry(self):
        """Test handling of options with very long time to expiry."""
        far_future = datetime.now().date() + timedelta(days=365 * 2)  # 2 years
        
        result = generate_greeks_landscape_html(
            ticker='AAPL',
            greeks_view='All',
            end_date=far_future.strftime('%Y-%m-%d')
        )
        
        # Should handle gracefully
        self.assertIsInstance(result, (dict, str))
    
    def test_empty_parameters(self):
        """Test handling of empty or None parameters."""
        # Test with minimal parameters
        result = generate_greeks_landscape_html(ticker='AAPL')
        
        # Should use defaults and work or return appropriate error
        self.assertIsInstance(result, (dict, str))
    
    def test_whitespace_parameters(self):
        """Test handling of parameters with whitespace."""
        result = generate_greeks_landscape_html(
            ticker='  AAPL  ',  # Whitespace around ticker
            greeks_view='  All  '
        )
        
        # Should handle whitespace gracefully
        self.assertIsInstance(result, (dict, str))


if __name__ == '__main__':
    # Configure test logging
    logging.basicConfig(level=logging.ERROR)
    
    # Run tests with detailed output
    unittest.main(verbosity=2)