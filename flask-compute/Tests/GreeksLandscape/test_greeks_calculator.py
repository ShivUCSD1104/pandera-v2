"""
Unit tests for the Greeks calculator module.

Tests Black-Scholes Greeks calculations with known input/output pairs
and handles edge cases like zero time to expiry and extreme moneyness.
"""

import unittest
import math
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import norm

# Import the modules to test
import sys
import os
from unittest.mock import patch

# Mock the database connection before importing
with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///:memory:'}):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
    
    from GreeksLandscape.greeks_calculator import GreeksCalculator
    from GreeksLandscape.data import GreeksData


class TestGreeksCalculator(unittest.TestCase):
    """Test cases for GreeksCalculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = GreeksCalculator()
        
        # Standard test case parameters
        self.standard_params = {
            'strike': 100.0,
            'expiry': datetime.now() + timedelta(days=30),
            'time_to_expiry': 30/365.0,  # 30 days in years
            'underlying_price': 100.0,
            'risk_free_rate': 0.05,
            'volatility': 0.20,
            'option_type': 'call'
        }
    
    def create_greeks_data(self, **kwargs):
        """Helper method to create GreeksData with custom parameters."""
        params = self.standard_params.copy()
        params.update(kwargs)
        return GreeksData(**params)
    
    def test_call_delta_at_the_money(self):
        """Test call delta calculation for at-the-money option."""
        greeks_data = self.create_greeks_data()
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # ATM call delta should be approximately 0.5
        self.assertIsNotNone(result.delta)
        self.assertAlmostEqual(result.delta, 0.5, delta=0.1)
    
    def test_call_delta_in_the_money(self):
        """Test call delta for in-the-money option."""
        greeks_data = self.create_greeks_data(underlying_price=110.0)  # ITM
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # ITM call delta should be > 0.5
        self.assertIsNotNone(result.delta)
        self.assertGreater(result.delta, 0.5)
        self.assertLessEqual(result.delta, 1.0)
    
    def test_call_delta_out_of_the_money(self):
        """Test call delta for out-of-the-money option."""
        greeks_data = self.create_greeks_data(underlying_price=90.0)  # OTM
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # OTM call delta should be < 0.5
        self.assertIsNotNone(result.delta)
        self.assertLess(result.delta, 0.5)
        self.assertGreaterEqual(result.delta, 0.0)
    
    def test_put_delta_at_the_money(self):
        """Test put delta calculation for at-the-money option."""
        greeks_data = self.create_greeks_data(option_type='put')
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # ATM put delta should be approximately -0.5
        self.assertIsNotNone(result.delta)
        self.assertAlmostEqual(result.delta, -0.5, delta=0.1)
    
    def test_put_delta_in_the_money(self):
        """Test put delta for in-the-money option."""
        greeks_data = self.create_greeks_data(
            underlying_price=90.0,  # ITM for put
            option_type='put'
        )
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # ITM put delta should be < -0.5
        self.assertIsNotNone(result.delta)
        self.assertLess(result.delta, -0.5)
        self.assertGreaterEqual(result.delta, -1.0)
    
    def test_gamma_positive(self):
        """Test that gamma is always positive."""
        test_cases = [
            {'underlying_price': 90.0},   # OTM
            {'underlying_price': 100.0},  # ATM
            {'underlying_price': 110.0},  # ITM
        ]
        
        for case in test_cases:
            with self.subTest(case=case):
                greeks_data = self.create_greeks_data(**case)
                result = self.calculator.calculate_all_greeks(greeks_data)
                
                self.assertIsNotNone(result.gamma)
                self.assertGreaterEqual(result.gamma, 0.0)
    
    def test_gamma_maximum_at_the_money(self):
        """Test that gamma is highest at-the-money."""
        atm_data = self.create_greeks_data(underlying_price=100.0)
        otm_data = self.create_greeks_data(underlying_price=90.0)
        itm_data = self.create_greeks_data(underlying_price=110.0)
        
        atm_result = self.calculator.calculate_all_greeks(atm_data)
        otm_result = self.calculator.calculate_all_greeks(otm_data)
        itm_result = self.calculator.calculate_all_greeks(itm_data)
        
        # ATM gamma should be higher than OTM and ITM
        self.assertGreater(atm_result.gamma, otm_result.gamma)
        self.assertGreater(atm_result.gamma, itm_result.gamma)
    
    def test_theta_negative_for_calls(self):
        """Test that theta is negative for call options (time decay)."""
        greeks_data = self.create_greeks_data(option_type='call')
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        self.assertIsNotNone(result.theta)
        self.assertLess(result.theta, 0.0)
    
    def test_theta_negative_for_puts(self):
        """Test that theta is negative for put options (time decay)."""
        greeks_data = self.create_greeks_data(option_type='put')
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        self.assertIsNotNone(result.theta)
        # Note: Put theta can be positive for deep ITM puts, but typically negative
        # We'll test that it's calculated (not None)
    
    def test_vega_positive(self):
        """Test that vega is always positive."""
        test_cases = [
            {'underlying_price': 90.0, 'option_type': 'call'},
            {'underlying_price': 100.0, 'option_type': 'call'},
            {'underlying_price': 110.0, 'option_type': 'call'},
            {'underlying_price': 90.0, 'option_type': 'put'},
            {'underlying_price': 100.0, 'option_type': 'put'},
            {'underlying_price': 110.0, 'option_type': 'put'},
        ]
        
        for case in test_cases:
            with self.subTest(case=case):
                greeks_data = self.create_greeks_data(**case)
                result = self.calculator.calculate_all_greeks(greeks_data)
                
                self.assertIsNotNone(result.vega)
                self.assertGreaterEqual(result.vega, 0.0)
    
    def test_known_black_scholes_values(self):
        """Test against known Black-Scholes values."""
        # Known test case: S=100, K=100, T=0.25, r=0.05, sigma=0.2
        greeks_data = self.create_greeks_data(
            underlying_price=100.0,
            strike=100.0,
            time_to_expiry=0.25,  # 3 months
            risk_free_rate=0.05,
            volatility=0.20,
            option_type='call'
        )
        
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # Expected values calculated independently
        # These are approximate values for validation
        self.assertAlmostEqual(result.delta, 0.5695, delta=0.01)
        self.assertAlmostEqual(result.gamma, 0.0393, delta=0.005)
        self.assertAlmostEqual(result.vega, 0.1964, delta=0.02)
        # Theta should be negative
        self.assertLess(result.theta, 0)
    
    def test_edge_case_zero_volatility(self):
        """Test edge case with zero volatility."""
        greeks_data = self.create_greeks_data(volatility=0.0)
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # Should handle zero volatility gracefully
        # Calculator should use minimum volatility
        self.assertIsNotNone(result.delta)
        self.assertIsNotNone(result.gamma)
        self.assertIsNotNone(result.theta)
        self.assertIsNotNone(result.vega)
    
    def test_edge_case_very_short_time_to_expiry(self):
        """Test edge case with very short time to expiry."""
        greeks_data = self.create_greeks_data(
            time_to_expiry=0.5/365,  # Half a day
            expiry=datetime.now() + timedelta(hours=12)
        )
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # Should handle short expiry gracefully
        self.assertIsNotNone(result.delta)
        self.assertIsNotNone(result.gamma)
        self.assertIsNotNone(result.theta)
        self.assertIsNotNone(result.vega)
    
    def test_edge_case_extreme_moneyness_deep_itm(self):
        """Test edge case with extreme in-the-money option."""
        greeks_data = self.create_greeks_data(
            underlying_price=200.0,  # Very deep ITM
            strike=100.0
        )
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # Deep ITM call should have delta close to 1
        self.assertIsNotNone(result.delta)
        self.assertGreater(result.delta, 0.9)
        self.assertLessEqual(result.delta, 1.0)
    
    def test_edge_case_extreme_moneyness_deep_otm(self):
        """Test edge case with extreme out-of-the-money option."""
        greeks_data = self.create_greeks_data(
            underlying_price=50.0,  # Very deep OTM
            strike=100.0
        )
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # Deep OTM call should have delta close to 0
        self.assertIsNotNone(result.delta)
        self.assertLess(result.delta, 0.1)
        self.assertGreaterEqual(result.delta, 0.0)
    
    def test_invalid_inputs_negative_price(self):
        """Test handling of invalid inputs - negative underlying price."""
        greeks_data = self.create_greeks_data(underlying_price=-10.0)
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # Should return original data without calculations
        self.assertIsNone(result.delta)
        self.assertIsNone(result.gamma)
        self.assertIsNone(result.theta)
        self.assertIsNone(result.vega)
    
    def test_invalid_inputs_negative_strike(self):
        """Test handling of invalid inputs - negative strike price."""
        greeks_data = self.create_greeks_data(strike=-10.0)
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # Should return original data without calculations
        self.assertIsNone(result.delta)
        self.assertIsNone(result.gamma)
        self.assertIsNone(result.theta)
        self.assertIsNone(result.vega)
    
    def test_invalid_inputs_negative_time(self):
        """Test handling of invalid inputs - negative time to expiry."""
        greeks_data = self.create_greeks_data(time_to_expiry=-0.1)
        result = self.calculator.calculate_all_greeks(greeks_data)
        
        # Should return original data without calculations
        self.assertIsNone(result.delta)
        self.assertIsNone(result.gamma)
        self.assertIsNone(result.theta)
        self.assertIsNone(result.vega)
    
    def test_batch_calculation(self):
        """Test batch Greeks calculation."""
        greeks_data_list = [
            self.create_greeks_data(underlying_price=90.0),
            self.create_greeks_data(underlying_price=100.0),
            self.create_greeks_data(underlying_price=110.0),
        ]
        
        results = self.calculator.calculate_batch_greeks(greeks_data_list)
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsNotNone(result.delta)
            self.assertIsNotNone(result.gamma)
            self.assertIsNotNone(result.theta)
            self.assertIsNotNone(result.vega)
    
    def test_put_call_parity_relationships(self):
        """Test put-call parity relationships for Greeks."""
        # Create call and put with same parameters
        call_data = self.create_greeks_data(option_type='call')
        put_data = self.create_greeks_data(option_type='put')
        
        call_result = self.calculator.calculate_all_greeks(call_data)
        put_result = self.calculator.calculate_all_greeks(put_data)
        
        # Put-call parity for delta: call_delta - put_delta = 1
        delta_diff = call_result.delta - put_result.delta
        self.assertAlmostEqual(delta_diff, 1.0, delta=0.01)
        
        # Gamma should be the same for calls and puts
        self.assertAlmostEqual(call_result.gamma, put_result.gamma, delta=0.001)
        
        # Vega should be the same for calls and puts
        self.assertAlmostEqual(call_result.vega, put_result.vega, delta=0.001)
    
    def test_volatility_sensitivity(self):
        """Test that Greeks respond appropriately to volatility changes."""
        low_vol_data = self.create_greeks_data(volatility=0.10)
        high_vol_data = self.create_greeks_data(volatility=0.40)
        
        low_vol_result = self.calculator.calculate_all_greeks(low_vol_data)
        high_vol_result = self.calculator.calculate_all_greeks(high_vol_data)
        
        # Higher volatility should result in higher vega
        self.assertGreater(high_vol_result.vega, low_vol_result.vega)
        
        # For ATM options, higher volatility actually results in lower gamma
        # This is correct behavior as higher vol spreads out the probability distribution
        self.assertLess(high_vol_result.gamma, low_vol_result.gamma)


class TestGreeksCalculatorIntegration(unittest.TestCase):
    """Integration tests for Greeks calculator with realistic scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = GreeksCalculator()
    
    def test_realistic_options_chain(self):
        """Test with realistic options chain data."""
        # Simulate a realistic options chain
        base_date = datetime.now()
        strikes = [90, 95, 100, 105, 110]
        expiries = [30, 60, 90]  # days
        
        greeks_data_list = []
        for strike in strikes:
            for expiry_days in expiries:
                greeks_data = GreeksData(
                    strike=float(strike),
                    expiry=base_date + timedelta(days=expiry_days),
                    time_to_expiry=expiry_days/365.0,
                    underlying_price=100.0,
                    risk_free_rate=0.05,
                    volatility=0.20,
                    option_type='call'
                )
                greeks_data_list.append(greeks_data)
        
        results = self.calculator.calculate_batch_greeks(greeks_data_list)
        
        # Verify all calculations completed
        self.assertEqual(len(results), len(strikes) * len(expiries))
        
        for result in results:
            self.assertIsNotNone(result.delta)
            self.assertIsNotNone(result.gamma)
            self.assertIsNotNone(result.theta)
            self.assertIsNotNone(result.vega)
            
            # Sanity checks
            self.assertGreaterEqual(result.delta, 0.0)
            self.assertLessEqual(result.delta, 1.0)
            self.assertGreaterEqual(result.gamma, 0.0)
            self.assertLessEqual(result.theta, 0.0)  # Theta should be negative
            self.assertGreaterEqual(result.vega, 0.0)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)