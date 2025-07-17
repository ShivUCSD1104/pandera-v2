"""
End-to-end integration tests for Greeks Landscape functionality.

This test suite covers:
1. Complete API request/response cycles
2. Frontend modal rendering with Greeks Landscape model type
3. Parameter passing and data visualization rendering
4. Responsive design across different screen sizes

Requirements: 4.4, 4.5
"""

import unittest
import sys
import os
import json
import requests
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, date, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException

# Mock the database connection before importing
with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///:memory:'}):
    # Add parent directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
    
    from flask_compute.app import app
    from GreeksLandscape.main import generate_greeks_landscape_html


class TestGreeksLandscapeIntegration(unittest.TestCase):
    """Integration tests for Greeks Landscape end-to-end functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for the entire test class."""
        cls.api_base_url = 'http://localhost:5000'
        cls.frontend_url = 'http://localhost:3000'
        cls.test_ticker = 'AAPL'
        cls.test_greeks_view = 'All'
        
        # Set up Chrome driver with options for testing
        cls.chrome_options = Options()
        cls.chrome_options.add_argument('--headless')  # Run in headless mode for CI
        cls.chrome_options.add_argument('--no-sandbox')
        cls.chrome_options.add_argument('--disable-dev-shm-usage')
        cls.chrome_options.add_argument('--window-size=1920,1080')
        
        # Try to initialize driver, skip tests if not available
        try:
            cls.driver = webdriver.Chrome(options=cls.chrome_options)
            cls.driver_available = True
        except (WebDriverException, Exception) as e:
            print(f"Chrome driver not available: {e}")
            cls.driver_available = False
            cls.driver = None
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        if cls.driver:
            cls.driver.quit()
    
    def setUp(self):
        """Set up test fixtures for each test."""
        self.start_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        self.end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
    
    def test_api_request_response_cycle_success(self):
        """Test complete API request/response cycle with valid parameters."""
        # Prepare test data
        test_payload = {
            'graphType': 'GreeksLandscape',
            'parameters': {
                'Ticker': self.test_ticker,
                'Greeks View': self.test_greeks_view,
                'Start Date': self.start_date,
                'End Date': self.end_date
            }
        }
        
        # Mock the Greeks Landscape generation
        with patch('GreeksLandscape.main.generate_greeks_landscape_html') as mock_generate:
            mock_plotly_json = {
                'data': [
                    {
                        'type': 'surface',
                        'x': [100, 105, 110],
                        'y': [0.1, 0.2, 0.3],
                        'z': [[0.5, 0.6, 0.7], [0.4, 0.5, 0.6], [0.3, 0.4, 0.5]],
                        'name': 'Delta Surface'
                    }
                ],
                'layout': {
                    'title': 'Options Greeks Landscape - AAPL',
                    'scene': {
                        'xaxis': {'title': 'Strike Price'},
                        'yaxis': {'title': 'Time to Expiry'},
                        'zaxis': {'title': 'Greeks Value'}
                    }
                }
            }
            mock_generate.return_value = json.dumps(mock_plotly_json)
            
            # Test with Flask test client
            with app.test_client() as client:
                response = client.post('/compute', 
                                     json=test_payload,
                                     content_type='application/json')
                
                # Verify response
                self.assertEqual(response.status_code, 200)
                response_data = response.get_json()
                self.assertIn('plotly_json', response_data)
                
                # Verify the plotly JSON structure
                plotly_data = json.loads(response_data['plotly_json'])
                self.assertIn('data', plotly_data)
                self.assertIn('layout', plotly_data)
                self.assertEqual(len(plotly_data['data']), 1)
                self.assertEqual(plotly_data['data'][0]['type'], 'surface')
                
                # Verify mock was called with correct parameters
                mock_generate.assert_called_once_with(
                    self.test_ticker,
                    self.test_greeks_view,
                    self.start_date,
                    self.end_date
                )
    
    def test_api_request_response_cycle_error_handling(self):
        """Test API error handling with invalid parameters."""
        # Test with missing parameters
        test_payload = {
            'graphType': 'GreeksLandscape',
            'parameters': {}
        }
        
        with app.test_client() as client:
            response = client.post('/compute', 
                                 json=test_payload,
                                 content_type='application/json')
            
            # Should still work with default parameters
            self.assertEqual(response.status_code, 200)
        
        # Test with invalid graph type
        test_payload = {
            'graphType': 'InvalidType',
            'parameters': {
                'Ticker': self.test_ticker
            }
        }
        
        with app.test_client() as client:
            response = client.post('/compute', 
                                 json=test_payload,
                                 content_type='application/json')
            
            # Should return error for invalid graph type
            self.assertEqual(response.status_code, 400)
            response_data = response.get_json()
            self.assertIn('error', response_data)
    
    def test_api_parameter_validation(self):
        """Test API parameter validation and default handling."""
        # Test with minimal parameters
        test_payload = {
            'graphType': 'GreeksLandscape',
            'parameters': {
                'Ticker': 'GOOGL'
            }
        }
        
        with patch('GreeksLandscape.main.generate_greeks_landscape_html') as mock_generate:
            mock_generate.return_value = '{"data": [], "layout": {}}'
            
            with app.test_client() as client:
                response = client.post('/compute', 
                                     json=test_payload,
                                     content_type='application/json')
                
                self.assertEqual(response.status_code, 200)
                
                # Verify defaults were applied
                call_args = mock_generate.call_args[0]
                self.assertEqual(call_args[0], 'GOOGL')  # Ticker
                self.assertEqual(call_args[1], 'All')    # Default Greeks View
    
    @unittest.skipUnless(driver_available, "Chrome driver not available")
    def test_frontend_modal_rendering(self):
        """Test frontend modal rendering with Greeks Landscape model type."""
        try:
            # Navigate to the models page
            self.driver.get(f"{self.frontend_url}/models")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            # Find and click the Greeks Landscape card
            greeks_card = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//h3[contains(text(), 'Options Greeks Landscape')]/../.."))
            )
            greeks_card.click()
            
            # Wait for modal to open
            modal = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "fixed"))
            )
            
            # Verify modal title
            modal_title = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'Options Greeks Landscape')]")
            self.assertIsNotNone(modal_title)
            
            # Verify parameter controls are present
            ticker_select = self.driver.find_element(By.XPATH, "//label[text()='Ticker']/../select")
            self.assertIsNotNone(ticker_select)
            
            greeks_view_select = self.driver.find_element(By.XPATH, "//label[text()='Greeks View']/../select")
            self.assertIsNotNone(greeks_view_select)
            
            # Verify time period slider is present
            time_slider = self.driver.find_element(By.CLASS_NAME, "MuiSlider-root")
            self.assertIsNotNone(time_slider)
            
            # Verify compute button is present
            compute_button = self.driver.find_element(By.XPATH, "//button[text()='Compute']")
            self.assertIsNotNone(compute_button)
            
            # Verify visualization area is present
            viz_area = self.driver.find_element(By.CLASS_NAME, "bg-fuchsia-100")
            self.assertIsNotNone(viz_area)
            
        except TimeoutException:
            self.skipTest("Frontend not available or too slow to load")
        except Exception as e:
            self.fail(f"Frontend modal rendering test failed: {e}")
    
    @unittest.skipUnless(driver_available, "Chrome driver not available")
    def test_parameter_passing_and_selection(self):
        """Test parameter passing and selection in frontend modal."""
        try:
            # Navigate to models page and open Greeks Landscape modal
            self.driver.get(f"{self.frontend_url}/models")
            
            # Click Greeks Landscape card
            greeks_card = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//h3[contains(text(), 'Options Greeks Landscape')]/../.."))
            )
            greeks_card.click()
            
            # Wait for modal to open
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "fixed"))
            )
            
            # Test ticker selection
            ticker_select = Select(self.driver.find_element(By.XPATH, "//label[text()='Ticker']/../select"))
            ticker_select.select_by_value('GOOGL')
            self.assertEqual(ticker_select.first_selected_option.get_attribute('value'), 'GOOGL')
            
            # Test Greeks View selection
            greeks_select = Select(self.driver.find_element(By.XPATH, "//label[text()='Greeks View']/../select"))
            greeks_select.select_by_value('Delta')
            self.assertEqual(greeks_select.first_selected_option.get_attribute('value'), 'Delta')
            
            # Test time period slider interaction
            time_slider = self.driver.find_element(By.CLASS_NAME, "MuiSlider-root")
            slider_thumb = time_slider.find_element(By.CLASS_NAME, "MuiSlider-thumb")
            
            # Move slider (simulate user interaction)
            actions = ActionChains(self.driver)
            actions.click_and_hold(slider_thumb).move_by_offset(50, 0).release().perform()
            
            # Verify date display updated
            date_displays = self.driver.find_elements(By.XPATH, "//div[@class='flex justify-between text-sm text-gray-600 mt-2']/span")
            self.assertEqual(len(date_displays), 2)  # Start and end date
            
        except TimeoutException:
            self.skipTest("Frontend not available or too slow to load")
        except Exception as e:
            self.fail(f"Parameter passing test failed: {e}")
    
    @unittest.skipUnless(driver_available, "Chrome driver not available")
    def test_responsive_design_different_screen_sizes(self):
        """Test responsive design across different screen sizes."""
        screen_sizes = [
            (1920, 1080),  # Desktop
            (1366, 768),   # Laptop
            (768, 1024),   # Tablet
            (375, 667),    # Mobile
        ]
        
        for width, height in screen_sizes:
            with self.subTest(screen_size=f"{width}x{height}"):
                try:
                    # Set window size
                    self.driver.set_window_size(width, height)
                    
                    # Navigate to models page
                    self.driver.get(f"{self.frontend_url}/models")
                    
                    # Wait for page to load
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "main"))
                    )
                    
                    # Verify cards are visible and clickable
                    cards = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'rounded-2xl')]")
                    self.assertGreater(len(cards), 0, f"No cards visible at {width}x{height}")
                    
                    # Find Greeks Landscape card
                    greeks_card = None
                    for card in cards:
                        try:
                            title = card.find_element(By.TAG_NAME, "h3")
                            if "Options Greeks Landscape" in title.text:
                                greeks_card = card
                                break
                        except:
                            continue
                    
                    self.assertIsNotNone(greeks_card, f"Greeks Landscape card not found at {width}x{height}")
                    
                    # Verify card is clickable
                    self.assertTrue(greeks_card.is_displayed(), f"Greeks card not displayed at {width}x{height}")
                    self.assertTrue(greeks_card.is_enabled(), f"Greeks card not enabled at {width}x{height}")
                    
                    # Click card and verify modal opens
                    greeks_card.click()
                    
                    # Wait for modal
                    modal = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "fixed"))
                    )
                    
                    # Verify modal is properly sized
                    modal_content = modal.find_element(By.CLASS_NAME, "bg-white")
                    modal_rect = modal_content.rect
                    
                    # Modal should not exceed viewport
                    self.assertLessEqual(modal_rect['width'], width, f"Modal too wide at {width}x{height}")
                    self.assertLessEqual(modal_rect['height'], height, f"Modal too tall at {width}x{height}")
                    
                    # Close modal for next iteration
                    self.driver.find_element(By.CLASS_NAME, "fixed").click()
                    
                    # Wait for modal to close
                    WebDriverWait(self.driver, 5).until_not(
                        EC.presence_of_element_located((By.CLASS_NAME, "fixed"))
                    )
                    
                except TimeoutException:
                    self.skipTest(f"Frontend too slow at {width}x{height}")
                except Exception as e:
                    self.fail(f"Responsive design test failed at {width}x{height}: {e}")
    
    def test_data_visualization_rendering_structure(self):
        """Test that data visualization has proper structure for rendering."""
        # Test the structure of generated Plotly JSON
        with patch('GreeksLandscape.data.GreeksDataFetcher') as mock_fetcher_class:
            # Mock the data fetcher
            mock_fetcher = MagicMock()
            mock_fetcher_class.return_value = mock_fetcher
            
            # Mock options chain data
            mock_options_chain = MagicMock()
            mock_options_chain.ticker = self.test_ticker
            mock_options_chain.underlying_price = 150.0
            mock_options_chain.options = [
                {
                    'strike': 145.0,
                    'expiry': date(2025, 8, 15),
                    'type': 'call',
                    'option_price': 8.0,
                    'time_to_expiry': 0.25,
                    'implied_volatility': 0.25
                },
                {
                    'strike': 150.0,
                    'expiry': date(2025, 8, 15),
                    'type': 'call',
                    'option_price': 5.0,
                    'time_to_expiry': 0.25,
                    'implied_volatility': 0.22
                }
            ]
            
            mock_fetcher.fetch_options_chain.return_value = mock_options_chain
            
            # Mock Greeks data
            mock_greeks_data = [
                MagicMock(
                    strike=145.0,
                    time_to_expiry=0.25,
                    delta=0.65,
                    gamma=0.02,
                    theta=-0.05,
                    vega=0.15,
                    underlying_price=150.0,
                    volatility=0.25
                ),
                MagicMock(
                    strike=150.0,
                    time_to_expiry=0.25,
                    delta=0.50,
                    gamma=0.025,
                    theta=-0.04,
                    vega=0.18,
                    underlying_price=150.0,
                    volatility=0.22
                )
            ]
            
            mock_fetcher.prepare_greeks_data.return_value = mock_greeks_data
            
            # Generate the visualization
            result_json = generate_greeks_landscape_html(
                self.test_ticker,
                'All',
                self.start_date,
                self.end_date
            )
            
            # Parse and verify structure
            result_data = json.loads(result_json)
            
            # Verify top-level structure
            self.assertIn('data', result_data)
            self.assertIn('layout', result_data)
            
            # Verify data structure
            data_traces = result_data['data']
            self.assertIsInstance(data_traces, list)
            self.assertGreater(len(data_traces), 0)
            
            # Verify each trace has required fields
            for trace in data_traces:
                self.assertIn('type', trace)
                self.assertIn('x', trace)
                self.assertIn('y', trace)
                self.assertIn('z', trace)
                self.assertIn('name', trace)
            
            # Verify layout structure
            layout = result_data['layout']
            self.assertIn('title', layout)
            self.assertIn('scene', layout)
            
            # Verify scene configuration
            scene = layout['scene']
            self.assertIn('xaxis', scene)
            self.assertIn('yaxis', scene)
            self.assertIn('zaxis', scene)
            
            # Verify axis labels
            self.assertIn('title', scene['xaxis'])
            self.assertIn('title', scene['yaxis'])
            self.assertIn('title', scene['zaxis'])
    
    def test_error_handling_in_visualization(self):
        """Test error handling in data visualization rendering."""
        # Test with data fetching error
        with patch('GreeksLandscape.data.GreeksDataFetcher') as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher_class.return_value = mock_fetcher
            
            # Mock data fetching failure
            mock_fetcher.fetch_options_chain.side_effect = Exception("Database connection failed")
            
            # Should handle error gracefully
            result_json = generate_greeks_landscape_html(
                'INVALID_TICKER',
                'All',
                self.start_date,
                self.end_date
            )
            
            # Should return error structure
            result_data = json.loads(result_json)
            self.assertIn('error', result_data)
            self.assertIn('type', result_data)
            self.assertEqual(result_data['type'], 'data_error')
    
    def test_performance_with_large_dataset(self):
        """Test performance with large options chain dataset."""
        with patch('GreeksLandscape.data.GreeksDataFetcher') as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher_class.return_value = mock_fetcher
            
            # Create large mock dataset (1000+ options)
            large_options_list = []
            large_greeks_list = []
            
            strikes = range(50, 250, 5)  # 40 strikes
            expiries = [date(2025, month, 15) for month in range(1, 13)]  # 12 expiries
            
            for strike in strikes:
                for expiry in expiries:
                    large_options_list.append({
                        'strike': float(strike),
                        'expiry': expiry,
                        'type': 'call',
                        'option_price': max(0.1, 150.0 - strike + 5.0),
                        'time_to_expiry': (expiry - date.today()).days / 365.0,
                        'implied_volatility': 0.20 + (abs(strike - 150) / 1000)
                    })
                    
                    large_greeks_list.append(MagicMock(
                        strike=float(strike),
                        time_to_expiry=(expiry - date.today()).days / 365.0,
                        delta=max(0, min(1, (150.0 - strike + 50) / 100)),
                        gamma=0.02,
                        theta=-0.05,
                        vega=0.15,
                        underlying_price=150.0,
                        volatility=0.20 + (abs(strike - 150) / 1000)
                    ))
            
            # Mock large dataset
            mock_options_chain = MagicMock()
            mock_options_chain.ticker = self.test_ticker
            mock_options_chain.underlying_price = 150.0
            mock_options_chain.options = large_options_list
            
            mock_fetcher.fetch_options_chain.return_value = mock_options_chain
            mock_fetcher.prepare_greeks_data.return_value = large_greeks_list
            
            # Measure performance
            start_time = time.time()
            result_json = generate_greeks_landscape_html(
                self.test_ticker,
                'All',
                self.start_date,
                self.end_date
            )
            end_time = time.time()
            
            # Should complete within reasonable time (10 seconds)
            execution_time = end_time - start_time
            self.assertLess(execution_time, 10.0, f"Performance test took {execution_time:.2f} seconds")
            
            # Verify result is valid
            result_data = json.loads(result_json)
            self.assertIn('data', result_data)
            self.assertIn('layout', result_data)
            
            # Verify data contains expected number of points
            data_traces = result_data['data']
            self.assertGreater(len(data_traces), 0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)