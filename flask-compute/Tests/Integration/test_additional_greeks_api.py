#!/usr/bin/env python3
"""
Additional test cases for Greeks Landscape API integration.
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

def test_different_greeks_views():
    """Test different Greeks view parameters."""
    try:
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///:memory:'}):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, current_dir)
            
            from app import app
            
            logger.info("Testing different Greeks views...")
            
            with app.test_client() as client:
                with patch('GreeksLandscape.data.SessionLocal') as mock_session_local:
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
                    
                    # Test different Greeks views
                    views_to_test = ['Delta', 'Gamma', 'Theta', 'Vega', 'All']
                    
                    for view in views_to_test:
                        test_payload = {
                            "graphType": "GreeksLandscape",
                            "parameters": {
                                "Ticker": "AAPL",
                                "Greeks View": view
                            }
                        }
                        
                        response = client.post('/compute', 
                                             data=json.dumps(test_payload),
                                             content_type='application/json')
                        
                        if response.status_code == 200:
                            response_data = response.get_json()
                            if 'plotly_json' in response_data:
                                plotly_data = json.loads(response_data['plotly_json'])
                                logger.info(f"✓ Greeks view '{view}' working correctly")
                            else:
                                logger.error(f"Missing plotly_json for view '{view}'")
                                return False
                        else:
                            logger.error(f"API request failed for view '{view}' with status {response.status_code}")
                            return False
                    
                    return True
            
    except Exception as e:
        logger.error(f"Exception during Greeks views test: {str(e)}")
        return False

def test_different_tickers():
    """Test different ticker symbols."""
    try:
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///:memory:'}):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, current_dir)
            
            from app import app
            
            logger.info("Testing different ticker symbols...")
            
            with app.test_client() as client:
                with patch('GreeksLandscape.data.SessionLocal') as mock_session_local:
                    mock_session = MagicMock()
                    mock_session_local.return_value = mock_session
                    
                    # Mock underlying price data
                    mock_underlying = MagicMock()
                    mock_underlying.close = 200.0
                    mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_underlying
                    
                    # Mock options data
                    mock_option = MagicMock()
                    mock_option.strike = 200.0
                    mock_option.expiration_date = date(2025, 12, 15)
                    mock_option.option_type = 'put'
                    mock_option.bid = 5.0
                    mock_option.ask = 5.5
                    mock_option.last_price = 5.25
                    
                    mock_session.query.return_value.filter.return_value.all.return_value = [mock_option]
                    
                    # Test different tickers
                    tickers_to_test = ['GOOGL', 'MSFT', 'TSLA', 'NVDA']
                    
                    for ticker in tickers_to_test:
                        test_payload = {
                            "graphType": "GreeksLandscape",
                            "parameters": {
                                "Ticker": ticker,
                                "Greeks View": "Delta"
                            }
                        }
                        
                        response = client.post('/compute', 
                                             data=json.dumps(test_payload),
                                             content_type='application/json')
                        
                        if response.status_code == 200:
                            response_data = response.get_json()
                            if 'plotly_json' in response_data:
                                logger.info(f"✓ Ticker '{ticker}' working correctly")
                            else:
                                logger.error(f"Missing plotly_json for ticker '{ticker}'")
                                return False
                        else:
                            logger.error(f"API request failed for ticker '{ticker}' with status {response.status_code}")
                            return False
                    
                    return True
            
    except Exception as e:
        logger.error(f"Exception during ticker test: {str(e)}")
        return False

def test_missing_parameters():
    """Test API behavior with missing parameters."""
    try:
        with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///:memory:'}):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, current_dir)
            
            from app import app
            
            logger.info("Testing missing parameters...")
            
            with app.test_client() as client:
                with patch('GreeksLandscape.data.SessionLocal') as mock_session_local:
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
                    
                    # Test with minimal parameters (should use defaults)
                    test_payload = {
                        "graphType": "GreeksLandscape",
                        "parameters": {}
                    }
                    
                    response = client.post('/compute', 
                                         data=json.dumps(test_payload),
                                         content_type='application/json')
                    
                    if response.status_code == 200:
                        response_data = response.get_json()
                        if 'plotly_json' in response_data:
                            logger.info("✓ Default parameters working correctly")
                            return True
                        else:
                            logger.error("Missing plotly_json with default parameters")
                            return False
                    else:
                        logger.error(f"API request failed with default parameters, status {response.status_code}")
                        return False
            
    except Exception as e:
        logger.error(f"Exception during missing parameters test: {str(e)}")
        return False

if __name__ == "__main__":
    success1 = test_different_greeks_views()
    success2 = test_different_tickers()
    success3 = test_missing_parameters()
    
    if success1 and success2 and success3:
        print("✓ All additional Greeks Landscape API tests passed!")
        sys.exit(0)
    else:
        print("✗ Some additional Greeks Landscape API tests failed!")
        sys.exit(1)