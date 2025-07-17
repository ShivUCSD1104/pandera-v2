"""
Integration test for live data fetching in Greeks calculator.

This test verifies that the GreeksDataFetcher can successfully fetch
live options data from the database and prepare it for Greeks calculations.
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, date

# Mock the database connection before importing
with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///:memory:'}):
    # Add parent directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
    
    from GreeksLandscape.data import GreeksDataFetcher, OptionsChainData, GreeksData


class TestLiveDataIntegration(unittest.TestCase):
    """Test live data integration for Greeks calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = GreeksDataFetcher()
    
    @patch('GreeksLandscape.data.SessionLocal')
    def test_fetch_underlying_price(self, mock_session_local):
        """Test fetching underlying price from database."""
        # Mock database session and query
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        # Mock underlying data record
        mock_record = MagicMock()
        mock_record.close = 150.50
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_record
        
        # Test the method
        price = self.fetcher._get_underlying_price('AAPL')
        
        # Verify result
        self.assertEqual(price, 150.50)
        mock_session.close.assert_called_once()
    
    @patch('GreeksLandscape.data.SessionLocal')
    def test_fetch_options_data(self, mock_session_local):
        """Test fetching options data from database."""
        # Mock database session and query
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        # Mock options data records
        mock_record1 = MagicMock()
        mock_record1.strike = 150.0
        mock_record1.expiration_date = date(2025, 8, 15)  # Future date
        mock_record1.option_type = 'call'
        mock_record1.bid = 5.0
        mock_record1.ask = 5.5
        mock_record1.last_price = 5.25
        
        mock_record2 = MagicMock()
        mock_record2.strike = 155.0
        mock_record2.expiration_date = date(2025, 8, 15)
        mock_record2.option_type = 'put'
        mock_record2.bid = 3.0
        mock_record2.ask = 3.5
        mock_record2.last_price = 3.25
        
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_record1, mock_record2]
        
        # Mock underlying price call
        with patch.object(self.fetcher, '_get_underlying_price', return_value=152.0):
            options_list = self.fetcher._get_options_data('AAPL')
        
        # Verify results
        self.assertEqual(len(options_list), 2)
        
        # Check first option (call)
        call_option = options_list[0]
        self.assertEqual(call_option['strike'], 150.0)
        self.assertEqual(call_option['type'], 'call')
        self.assertEqual(call_option['option_price'], 5.25)  # Mid of bid/ask
        self.assertGreater(call_option['time_to_expiry'], 0)
        self.assertIsInstance(call_option['implied_volatility'], float)
        
        # Check second option (put)
        put_option = options_list[1]
        self.assertEqual(put_option['strike'], 155.0)
        self.assertEqual(put_option['type'], 'put')
        self.assertEqual(put_option['option_price'], 3.25)  # Mid of bid/ask
    
    def test_implied_volatility_calculation(self):
        """Test implied volatility calculation."""
        # Test with known values
        implied_vol = self.fetcher._calculate_implied_volatility(
            option_price=10.0,
            underlying_price=100.0,
            strike=100.0,
            time_to_expiry=0.25,  # 3 months
            option_type='call',
            risk_free_rate=0.05
        )
        
        # Should return a reasonable volatility value
        self.assertGreater(implied_vol, 0.0)
        self.assertLess(implied_vol, 5.0)  # Less than 500%
        self.assertIsInstance(implied_vol, float)
    
    def test_implied_volatility_edge_cases(self):
        """Test implied volatility calculation edge cases."""
        # Test with option price below intrinsic value
        implied_vol = self.fetcher._calculate_implied_volatility(
            option_price=0.5,  # Very low price
            underlying_price=100.0,
            strike=90.0,  # Deep ITM call
            time_to_expiry=0.25,
            option_type='call',
            risk_free_rate=0.05
        )
        
        # Should return default volatility
        self.assertEqual(implied_vol, 0.20)
    
    def test_black_scholes_price_calculation(self):
        """Test Black-Scholes price calculation."""
        # Test call option
        call_price = self.fetcher._black_scholes_price(
            S=100.0, K=100.0, T=0.25, r=0.05, sigma=0.20, option_type='call'
        )
        
        # Test put option
        put_price = self.fetcher._black_scholes_price(
            S=100.0, K=100.0, T=0.25, r=0.05, sigma=0.20, option_type='put'
        )
        
        # Both should be positive
        self.assertGreater(call_price, 0)
        self.assertGreater(put_price, 0)
        
        # Call should be worth more than put for ATM options with positive rates
        self.assertGreater(call_price, put_price)
    
    @patch('GreeksLandscape.data.SessionLocal')
    def test_full_integration_flow(self, mock_session_local):
        """Test the complete flow from database to Greeks data preparation."""
        # Mock database responses
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        # Mock underlying price query
        mock_underlying = MagicMock()
        mock_underlying.close = 150.0
        
        # Mock options data query
        mock_option = MagicMock()
        mock_option.strike = 150.0
        mock_option.expiration_date = date(2025, 9, 15)
        mock_option.option_type = 'call'
        mock_option.bid = 8.0
        mock_option.ask = 8.5
        mock_option.last_price = 8.25
        
        # Set up query chain for underlying price
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_underlying
        
        # Set up query chain for options data
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_option]
        
        # Test the complete flow
        options_chain = self.fetcher.fetch_options_chain('AAPL')
        
        # Verify options chain data
        self.assertIsInstance(options_chain, OptionsChainData)
        self.assertEqual(options_chain.ticker, 'AAPL')
        self.assertEqual(options_chain.underlying_price, 150.0)
        self.assertGreater(len(options_chain.options), 0)
        
        # Test Greeks data preparation
        greeks_data_list = self.fetcher.prepare_greeks_data(options_chain)
        
        # Verify Greeks data preparation
        self.assertGreater(len(greeks_data_list), 0)
        
        for greeks_data in greeks_data_list:
            self.assertIsInstance(greeks_data, GreeksData)
            self.assertEqual(greeks_data.underlying_price, 150.0)
            self.assertGreater(greeks_data.time_to_expiry, 0)
            self.assertGreater(greeks_data.volatility, 0)
    
    def test_caching_mechanism(self):
        """Test that caching works correctly."""
        # Test cache miss
        self.assertFalse(self.fetcher._is_cached_valid('test_key'))
        
        # Add item to cache
        self.fetcher.cache['test_key'] = {
            'data': 'test_data',
            'timestamp': datetime.now()
        }
        
        # Test cache hit
        self.assertTrue(self.fetcher._is_cached_valid('test_key'))
        
        # Test cache expiry
        old_timestamp = datetime.now() - self.fetcher.cache_expiry - self.fetcher.cache_expiry
        self.fetcher.cache['expired_key'] = {
            'data': 'expired_data',
            'timestamp': old_timestamp
        }
        
        self.assertFalse(self.fetcher._is_cached_valid('expired_key'))


if __name__ == '__main__':
    unittest.main(verbosity=2)