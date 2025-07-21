"""
API Integration tests for Greeks Landscape functionality.

This test suite focuses on API-level integration testing without browser dependencies:
1. Complete API request/response cycles
2. Parameter validation and processing
3. Data flow from API to visualization
4. Error handling scenarios

Requirements: 4.4, 4.5
"""

import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

# Mock the database connection before importing
with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///:memory:'}):
    from app import app


class TestGreeksLandscapeAPIIntegration(unittest.TestCase):
    """API Integration tests for Greeks Landscape functionality."""
    
    def setUp(self):
        """Set up test fixtures for each test."""
        self.app = app.test_client()
        self.app.testing = True
        
        self.test_ticker = 'AAPL'
        self.start_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        self.end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Standard test payload
        self.base_payload = {
            'graphType': 'GreeksLandscape',
            'parameters': {
                'Ticker': self.test_ticker,
                'Greeks View': 'All',
                'Start Date': self.start_date,
                'End Date': self.end_date
            }
        }
    
    def test_complete_api_request_response_cycle(self):
        """Test complete API request/response cycle with Greeks Landscape."""
        with patch('GreeksLandscape.main.generate_greeks_landscape_html') as mock_generate:
            # Mock successful response
            mock_plotly_json = {
                'data': [
                    {
                        'type': 'surface',
                        'x': [100, 105, 110, 115, 120],
                        'y': [0.1, 0.2, 0.3, 0.4, 0.5],
                        'z': [
                            [0.5, 0.6, 0.7, 0.8, 0.9],
                            [0.4, 0.5, 0.6, 0.7, 0.8],
                            [0.3, 0.4, 0.5, 0.6, 0.7],
                            [0.2, 0.3, 0.4, 0.5, 0.6],
                            [0.1, 0.2, 0.3, 0.4, 0.5]
                        ],
                        'name': 'Delta Surface',
                        'colorscale': 'Viridis'
                    }
                ],
                'layout': {
                    'title': 'Options Greeks Landscape - AAPL',
                    'scene': {
                        'xaxis': {'title': 'Strike Price'},
                        'yaxis': {'title': 'Time to Expiry (Years)'},
                        'zaxis': {'title': 'Delta Value'}
                    },
                    'width': 800,
                    'height': 600
                }
            }
            mock_generate.return_value = json.dumps(mock_plotly_json)
            
            # Make API request
            response = self.app.post('/compute',
                                   json=self.base_payload,
                                   content_type='application/json')
            
            # Verify response
            self.assertEqual(response.status_code, 200)
            response_data = response.get_json()
            
            # Verify response structure
            self.assertIn('plotly_json', response_data)
            
            # Parse and verify plotly JSON
            plotly_data = json.loads(response_data['plotly_json'])
            self.assertIn('data', plotly_data)
            self.assertIn('layout', plotly_data)
            
            # Verify data structure
            self.assertEqual(len(plotly_data['data']), 1)
            surface_data = plotly_data['data'][0]
            self.assertEqual(surface_data['type'], 'surface')
            self.assertEqual(surface_data['name'], 'Delta Surface')
            self.assertIn('x', surface_data)
            self.assertIn('y', surface_data)
            self.assertIn('z', surface_data)
            
            # Verify layout structure
            layout = plotly_data['layout']
            self.assertEqual(layout['title'], 'Options Greeks Landscape - AAPL')
            self.assertIn('scene', layout)
            
            # Verify function was called with correct parameters
            mock_generate.assert_called_once_with(
                self.test_ticker,
                'All',
                self.start_date,
                self.end_date
            )
    
    def test_parameter_validation_and_defaults(self):
        """Test parameter validation and default value handling."""
        test_cases = [
            # Test with minimal parameters
            {
                'payload': {
                    'graphType': 'GreeksLandscape',
                    'parameters': {'Ticker': 'GOOGL'}
                },
                'expected_ticker': 'GOOGL',
                'expected_greeks_view': 'All'  # Default value
            },
            # Test with empty parameters
            {
                'payload': {
                    'graphType': 'GreeksLandscape',
                    'parameters': {}
                },
                'expected_ticker': 'AAPL',  # Default value
                'expected_greeks_view': 'All'  # Default value
            },
            # Test with all parameters
            {
                'payload': {
                    'graphType': 'GreeksLandscape',
                    'parameters': {
                        'Ticker': 'MSFT',
                        'Greeks View': 'Delta',
                        'Start Date': '2025-02-01',
                        'End Date': '2025-12-31'
                    }
                },
                'expected_ticker': 'MSFT',
                'expected_greeks_view': 'Delta'
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            with self.subTest(test_case=i):
                with patch('GreeksLandscape.main.generate_greeks_landscape_html') as mock_generate:
                    mock_generate.return_value = '{"data": [], "layout": {}}'
                    
                    response = self.app.post('/compute',
                                           json=test_case['payload'],
                                           content_type='application/json')
                    
                    self.assertEqual(response.status_code, 200)
                    
                    # Verify function was called with expected parameters
                    call_args = mock_generate.call_args[0]
                    self.assertEqual(call_args[0], test_case['expected_ticker'])
                    self.assertEqual(call_args[1], test_case['expected_greeks_view'])
    
    def test_different_greeks_views(self):
        """Test API with different Greeks View parameters."""
        greeks_views = ['Delta', 'Gamma', 'Theta', 'Vega', 'All']
        
        for greeks_view in greeks_views:
            with self.subTest(greeks_view=greeks_view):
                payload = self.base_payload.copy()
                payload['parameters']['Greeks View'] = greeks_view
                
                with patch('GreeksLandscape.main.generate_greeks_landscape_html') as mock_generate:
                    # Mock different response based on Greeks view
                    mock_response = {
                        'data': [{
                            'type': 'surface',
                            'name': f'{greeks_view} Surface',
                            'x': [100, 110, 120],
                            'y': [0.1, 0.2, 0.3],
                            'z': [[0.1, 0.2, 0.3], [0.2, 0.3, 0.4], [0.3, 0.4, 0.5]]
                        }],
                        'layout': {'title': f'Greeks Landscape - {greeks_view}'}
                    }
                    mock_generate.return_value = json.dumps(mock_response)
                    
                    response = self.app.post('/compute',
                                           json=payload,
                                           content_type='application/json')
                    
                    self.assertEqual(response.status_code, 200)
                    
                    # Verify correct Greeks view was passed
                    call_args = mock_generate.call_args[0]
                    self.assertEqual(call_args[1], greeks_view)
                    
                    # Verify response contains expected Greeks view
                    response_data = response.get_json()
                    plotly_data = json.loads(response_data['plotly_json'])
                    self.assertEqual(plotly_data['data'][0]['name'], f'{greeks_view} Surface')
    
    def test_different_tickers(self):
        """Test API with different ticker symbols."""
        tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
        
        for ticker in tickers:
            with self.subTest(ticker=ticker):
                payload = self.base_payload.copy()
                payload['parameters']['Ticker'] = ticker
                
                with patch('GreeksLandscape.main.generate_greeks_landscape_html') as mock_generate:
                    mock_response = {
                        'data': [{'type': 'surface', 'name': 'Delta Surface'}],
                        'layout': {'title': f'Options Greeks Landscape - {ticker}'}
                    }
                    mock_generate.return_value = json.dumps(mock_response)
                    
                    response = self.app.post('/compute',
                                           json=payload,
                                           content_type='application/json')
                    
                    self.assertEqual(response.status_code, 200)
                    
                    # Verify correct ticker was passed
                    call_args = mock_generate.call_args[0]
                    self.assertEqual(call_args[0], ticker)
    
    def test_date_range_handling(self):
        """Test API with different date ranges."""
        date_ranges = [
            {
                'start': '2025-01-01',
                'end': '2025-12-31',
                'description': 'Full year'
            },
            {
                'start': '2025-02-01',
                'end': '2025-05-01',
                'description': 'Quarter'
            },
            {
                'start': '2025-07-15',
                'end': '2025-08-15',
                'description': 'One month'
            }
        ]
        
        for date_range in date_ranges:
            with self.subTest(description=date_range['description']):
                payload = self.base_payload.copy()
                payload['parameters']['Start Date'] = date_range['start']
                payload['parameters']['End Date'] = date_range['end']
                
                with patch('GreeksLandscape.main.generate_greeks_landscape_html') as mock_generate:
                    mock_generate.return_value = '{"data": [], "layout": {}}'
                    
                    response = self.app.post('/compute',
                                           json=payload,
                                           content_type='application/json')
                    
                    self.assertEqual(response.status_code, 200)
                    
                    # Verify correct dates were passed
                    call_args = mock_generate.call_args[0]
                    self.assertEqual(call_args[2], date_range['start'])
                    self.assertEqual(call_args[3], date_range['end'])
    
    def test_error_handling_scenarios(self):
        """Test various error handling scenarios."""
        # Test with missing request body
        response = self.app.post('/compute', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        response_data = response.get_json()
        self.assertIn('error', response_data)
        
        # Test with invalid JSON
        response = self.app.post('/compute',
                               data='invalid json',
                               content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        # Test with missing graphType
        payload = {'parameters': {'Ticker': 'AAPL'}}
        response = self.app.post('/compute',
                               json=payload,
                               content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        # Test with invalid graphType
        payload = {
            'graphType': 'InvalidType',
            'parameters': {'Ticker': 'AAPL'}
        }
        response = self.app.post('/compute',
                               json=payload,
                               content_type='application/json')
        self.assertEqual(response.status_code, 400)
    
    def test_data_processing_error_handling(self):
        """Test error handling in data processing."""
        with patch('GreeksLandscape.main.generate_greeks_landscape_html') as mock_generate:
            # Mock data processing error
            mock_generate.side_effect = Exception("Data processing failed")
            
            response = self.app.post('/compute',
                                   json=self.base_payload,
                                   content_type='application/json')
            
            # Should return 500 for internal server error
            self.assertEqual(response.status_code, 500)
            response_data = response.get_json()
            self.assertIn('error', response_data)
    
    def test_data_not_available_error_handling(self):
        """Test handling when data is not available."""
        with patch('GreeksLandscape.main.generate_greeks_landscape_html') as mock_generate:
            # Mock data not available error
            error_response = {
                'error': 'No options data available for ticker INVALID',
                'type': 'data_error'
            }
            mock_generate.return_value = json.dumps(error_response)
            
            payload = self.base_payload.copy()
            payload['parameters']['Ticker'] = 'INVALID'
            
            response = self.app.post('/compute',
                                   json=payload,
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 200)  # Still returns 200 but with error in JSON
            response_data = response.get_json()
            
            # Parse the plotly_json to check for error
            plotly_data = json.loads(response_data['plotly_json'])
            self.assertIn('error', plotly_data)
            self.assertEqual(plotly_data['type'], 'data_error')
    
    def test_response_format_consistency(self):
        """Test that API response format is consistent."""
        with patch('GreeksLandscape.main.generate_greeks_landscape_html') as mock_generate:
            mock_generate.return_value = '{"data": [], "layout": {}}'
            
            response = self.app.post('/compute',
                                   json=self.base_payload,
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            response_data = response.get_json()
            
            # Verify response structure
            self.assertIsInstance(response_data, dict)
            self.assertIn('plotly_json', response_data)
            
            # Verify plotly_json is valid JSON string
            plotly_json = response_data['plotly_json']
            self.assertIsInstance(plotly_json, str)
            
            # Verify it can be parsed as JSON
            plotly_data = json.loads(plotly_json)
            self.assertIsInstance(plotly_data, dict)
    
    def test_concurrent_requests_handling(self):
        """Test handling of concurrent API requests."""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request(ticker):
            try:
                payload = self.base_payload.copy()
                payload['parameters']['Ticker'] = ticker
                
                with patch('GreeksLandscape.main.generate_greeks_landscape_html') as mock_generate:
                    mock_generate.return_value = f'{{"data": [], "layout": {{"title": "Greeks - {ticker}"}}}}'
                    
                    response = self.app.post('/compute',
                                           json=payload,
                                           content_type='application/json')
                    
                    results.append({
                        'ticker': ticker,
                        'status_code': response.status_code,
                        'response': response.get_json()
                    })
            except Exception as e:
                errors.append({'ticker': ticker, 'error': str(e)})
        
        # Create multiple threads for concurrent requests
        tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
        threads = []
        
        for ticker in tickers:
            thread = threading.Thread(target=make_request, args=(ticker,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), len(tickers))
        
        for result in results:
            self.assertEqual(result['status_code'], 200)
            self.assertIn('plotly_json', result['response'])
    
    def test_large_payload_handling(self):
        """Test handling of large request payloads."""
        # Create a payload with many parameters
        large_payload = {
            'graphType': 'GreeksLandscape',
            'parameters': {
                'Ticker': 'AAPL',
                'Greeks View': 'All',
                'Start Date': self.start_date,
                'End Date': self.end_date,
                # Add many additional parameters
                **{f'extra_param_{i}': f'value_{i}' for i in range(100)}
            }
        }
        
        with patch('GreeksLandscape.main.generate_greeks_landscape_html') as mock_generate:
            mock_generate.return_value = '{"data": [], "layout": {}}'
            
            response = self.app.post('/compute',
                                   json=large_payload,
                                   content_type='application/json')
            
            # Should handle large payload gracefully
            self.assertEqual(response.status_code, 200)
            
            # Verify only relevant parameters were passed to the function
            call_args = mock_generate.call_args[0]
            self.assertEqual(call_args[0], 'AAPL')  # Ticker
            self.assertEqual(call_args[1], 'All')   # Greeks View


if __name__ == '__main__':
    unittest.main(verbosity=2)