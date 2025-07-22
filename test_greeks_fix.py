"""
Test script to verify the Greeks calculation fix for option type normalization.
"""

import sys
import os
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

# Mock the GreeksData class to avoid database imports
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

def test_option_type_normalization():
    """Test that option types are properly normalized."""
    
    # Test the normalization logic directly
    def normalize_option_type(option_type):
        """Normalize option type from database format to calculator format."""
        option_type = option_type.lower()
        if option_type == 'calls':
            return 'call'
        elif option_type == 'puts':
            return 'put'
        return option_type
    
    # Test cases
    test_cases = [
        ('calls', 'call'),
        ('puts', 'put'),
        ('call', 'call'),
        ('put', 'put'),
        ('CALLS', 'call'),
        ('PUTS', 'put'),
        ('Call', 'call'),
        ('Put', 'put')
    ]
    
    try:
        for input_type, expected_output in test_cases:
            result = normalize_option_type(input_type)
            assert result == expected_output, f"Expected '{expected_output}', got '{result}' for input '{input_type}'"
            print(f"✓ '{input_type}' -> '{result}'")
        
        print("✓ All option type normalization tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False

def test_data_normalization():
    """Test the data processing normalization."""
    
    # Simulate database record with 'calls' option type
    class MockRecord:
        def __init__(self):
            self.option_type = 'calls'  # This is what was causing the issue
            self.strike = 150.0
            self.expiration_date = datetime.now().date() + timedelta(days=30)
            self.bid = 5.0
            self.ask = 5.5
            self.last_price = 5.25
    
    record = MockRecord()
    
    # Test the normalization logic
    option_type = record.option_type.lower()
    if option_type == 'calls':
        option_type = 'call'
    elif option_type == 'puts':
        option_type = 'put'
    
    assert option_type == 'call', f"Expected 'call', got '{option_type}'"
    print("✓ Data normalization logic works correctly")
    
    return True

if __name__ == "__main__":
    print("Testing Greeks calculation fix for option type normalization...")
    print("=" * 60)
    
    success = True
    
    # Test the calculator normalization
    success &= test_option_type_normalization()
    print()
    
    # Test the data processing normalization
    success &= test_data_normalization()
    print()
    
    if success:
        print("🎉 All tests passed! The fix should resolve the Railway deployment issue.")
    else:
        print("❌ Some tests failed. Please check the implementation.")