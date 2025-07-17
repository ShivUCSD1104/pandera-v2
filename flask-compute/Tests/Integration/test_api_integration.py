#!/usr/bin/env python3
"""
Test script for Greeks Landscape API integration.
"""

import sys
import os
import json
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime, date

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_greeks_landscape_api():
    """Test the Greeks Landscape API endpoint."""
    try:
        # Mock the database connection before importing
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///:memory:'}):
            # Add the current directory to Python path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, current_dir)
            
            # Import Flask app
            from app import app
            
            logger.info("Testing Greeks Landscape API endpoint...")
            
            # Create test client
            with app.test_client() as client:
                # Mock the database calls
                with patch('GreeksLandscape.data.SessionLocal') as mock_session_local:
                    # Set up mock session
                    mock_session = MagicMock()
                    mock_session_local.return_value = mock_session
                    
                    # Mock underlying price data
                    mock_underlying = MagicMock()
                    mock_underlying.close = 150.0
                    mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_underlying
                    
                    # Mock options data
                    mock_option = MagicMock()
                    mock_option.strike = 150.0
                    mock_option.expiration_date = date(2025, 9, 15)
                    mock_option.option_type = 'call'
                    mock_option.bid = 8.0
                    mock_option.ask = 8.5
                    mock_option.last_price = 8.25
                    
                    mock_session.query.return_value.filter.return_value.all.return_value = [mock_option]
                    
                    # Test API request
                    test_payload = {
                        "graphType": "GreeksLandscape",
                        "parameters": {
                            "Ticker": "AAPL",
                            "Greeks View": "All"
                        }
                    }
                    
                    response = client.post('/compute', 
                                         data=json.dumps(test_payload),
                                         content_type='application/json')
                    
                    # Check response
                    if response.status_code == 200:
                        response_data = response.get_json()
                        if 'plotly_json' in response_data:
                            # Try to parse the plotly JSON
                            plotly_data = json.loads(response_data['plotly_json'])
                            if 'data' in plotly_data and 'layout' in plotly_data:
                                logger.info("✓ Greeks Landscape API endpoint working correctly")
                                logger.info(f"Response status: {response.status_code}")
                                logger.info(f"Number of traces: {len(plotly_data['data'])}")
                                return True
                            else:
                                logger.error("Invalid Plotly JSON structure")
                                return False
                        else:
                            logger.error("Missing plotly_json in response")
                            return False
                    else:
                        logger.error(f"API request failed with status {response.status_code}")
                        logger.error(f"Response: {response.get_json()}")
                        return False
            
    except Exception as e:
        logger.error(f"Exception during API test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_greeks_landscape_error_handling():
    """Test error handling for Greeks Landscape API."""
    try:
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///:memory:'}):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, current_dir)
            
            from app import app
            
            logger.info("Testing Greeks Landscape error handling...")
            
            with app.test_client() as client:
                # Mock database to return no data (should trigger data_error)
                with patch('GreeksLandscape.data.SessionLocal') as mock_session_local:
                    mock_session = MagicMock()
                    mock_session_local.return_value = mock_session
                    
                    # Mock no underlying data
                    mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
                    
                    test_payload = {
                        "graphType": "GreeksLandscape",
                        "parameters": {
                            "Ticker": "INVALID",
                            "Greeks View": "All"
                        }
                    }
                    
                    response = client.post('/compute', 
                                         data=json.dumps(test_payload),
                                         content_type='application/json')
                    
                    # Should return 404 for data error
                    if response.status_code == 404:
                        response_data = response.get_json()
                        if 'error' in response_data:
                            logger.info("✓ Error handling working correctly")
                            logger.info(f"Error response: {response_data['error']}")
                            return True
                        else:
                            logger.error("Missing error message in response")
                            return False
                    else:
                        logger.error(f"Expected 404, got {response.status_code}")
                        return False
                        
    except Exception as e:
        logger.error(f"Exception during error handling test: {str(e)}")
        return False

if __name__ == "__main__":
    success1 = test_greeks_landscape_api()
    success2 = test_greeks_landscape_error_handling()
    
    if success1 and success2:
        print("✓ All Greeks Landscape API tests passed!")
        sys.exit(0)
    else:
        print("✗ Some Greeks Landscape API tests failed!")
        sys.exit(1)