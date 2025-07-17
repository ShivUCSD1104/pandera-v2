"""
Basic unit tests to verify test infrastructure is working.

These tests don't require complex imports or database connections,
making them ideal for testing the test runner infrastructure.
"""

import pytest
import time
import math
from datetime import datetime


class TestBasicMath:
    """Test basic mathematical operations."""
    
    def test_addition(self):
        """Test basic addition."""
        assert 2 + 2 == 4
        assert 1 + 1 == 2
        assert 0 + 0 == 0
    
    def test_multiplication(self):
        """Test basic multiplication."""
        assert 3 * 4 == 12
        assert 2 * 2 == 4
        assert 5 * 0 == 0
    
    def test_division(self):
        """Test basic division."""
        assert 10 / 2 == 5
        assert 9 / 3 == 3
        
        # Test division by zero
        with pytest.raises(ZeroDivisionError):
            10 / 0


class TestStringOperations:
    """Test string operations."""
    
    def test_string_concatenation(self):
        """Test string concatenation."""
        assert "hello" + " " + "world" == "hello world"
        assert "test" + "" == "test"
    
    def test_string_formatting(self):
        """Test string formatting."""
        name = "Flask Compute"
        version = "1.0"
        
        formatted = f"{name} v{version}"
        assert formatted == "Flask Compute v1.0"
    
    def test_string_methods(self):
        """Test string methods."""
        test_string = "  Hello World  "
        
        assert test_string.strip() == "Hello World"
        assert test_string.lower().strip() == "hello world"
        assert test_string.upper().strip() == "HELLO WORLD"


class TestListOperations:
    """Test list operations."""
    
    def test_list_creation(self):
        """Test list creation and basic operations."""
        test_list = [1, 2, 3, 4, 5]
        
        assert len(test_list) == 5
        assert test_list[0] == 1
        assert test_list[-1] == 5
    
    def test_list_methods(self):
        """Test list methods."""
        test_list = [3, 1, 4, 1, 5]
        
        # Test sorting
        sorted_list = sorted(test_list)
        assert sorted_list == [1, 1, 3, 4, 5]
        
        # Test append
        test_list.append(6)
        assert 6 in test_list
        assert len(test_list) == 6
    
    def test_list_comprehension(self):
        """Test list comprehensions."""
        numbers = [1, 2, 3, 4, 5]
        squares = [x**2 for x in numbers]
        
        assert squares == [1, 4, 9, 16, 25]
        
        # Test filtering
        evens = [x for x in numbers if x % 2 == 0]
        assert evens == [2, 4]


class TestDictOperations:
    """Test dictionary operations."""
    
    def test_dict_creation(self):
        """Test dictionary creation and access."""
        test_dict = {
            'name': 'Greeks Calculator',
            'version': '1.0',
            'features': ['caching', 'performance monitoring']
        }
        
        assert test_dict['name'] == 'Greeks Calculator'
        assert test_dict['version'] == '1.0'
        assert len(test_dict['features']) == 2
    
    def test_dict_methods(self):
        """Test dictionary methods."""
        test_dict = {'a': 1, 'b': 2, 'c': 3}
        
        # Test keys, values, items
        assert list(test_dict.keys()) == ['a', 'b', 'c']
        assert list(test_dict.values()) == [1, 2, 3]
        assert ('a', 1) in test_dict.items()
        
        # Test get method
        assert test_dict.get('a') == 1
        assert test_dict.get('d', 'default') == 'default'


class TestDateTimeOperations:
    """Test datetime operations."""
    
    def test_datetime_creation(self):
        """Test datetime creation."""
        now = datetime.now()
        
        assert isinstance(now, datetime)
        assert now.year >= 2024
    
    def test_datetime_formatting(self):
        """Test datetime formatting."""
        test_date = datetime(2024, 12, 25, 10, 30, 0)
        
        formatted = test_date.strftime('%Y-%m-%d %H:%M:%S')
        assert formatted == '2024-12-25 10:30:00'
    
    def test_datetime_comparison(self):
        """Test datetime comparison."""
        date1 = datetime(2024, 1, 1)
        date2 = datetime(2024, 12, 31)
        
        assert date1 < date2
        assert date2 > date1
        assert date1 != date2


class TestMathOperations:
    """Test mathematical operations."""
    
    def test_basic_math_functions(self):
        """Test basic math functions."""
        assert math.sqrt(16) == 4
        assert math.pow(2, 3) == 8
        assert abs(-5) == 5
    
    def test_trigonometric_functions(self):
        """Test trigonometric functions."""
        # Test with known values
        assert abs(math.sin(0) - 0) < 0.001
        assert abs(math.cos(0) - 1) < 0.001
        assert abs(math.tan(0) - 0) < 0.001
    
    def test_logarithmic_functions(self):
        """Test logarithmic functions."""
        assert abs(math.log(math.e) - 1) < 0.001
        assert abs(math.log10(100) - 2) < 0.001
        assert abs(math.exp(0) - 1) < 0.001


@pytest.mark.performance
class TestPerformanceBasics:
    """Basic performance tests."""
    
    def test_simple_loop_performance(self):
        """Test simple loop performance."""
        start_time = time.time()
        
        # Simple computation
        result = sum(range(10000))
        
        duration = time.time() - start_time
        
        # Should complete quickly
        assert duration < 0.1  # Less than 100ms
        assert result == 49995000  # Expected sum
    
    def test_list_creation_performance(self):
        """Test list creation performance."""
        start_time = time.time()
        
        # Create large list
        large_list = list(range(100000))
        
        duration = time.time() - start_time
        
        # Should complete quickly
        assert duration < 0.5  # Less than 500ms
        assert len(large_list) == 100000


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_exception_raising(self):
        """Test that exceptions are raised correctly."""
        with pytest.raises(ValueError):
            int("not_a_number")
        
        with pytest.raises(KeyError):
            test_dict = {'a': 1}
            _ = test_dict['b']
        
        with pytest.raises(IndexError):
            test_list = [1, 2, 3]
            _ = test_list[10]
    
    def test_exception_messages(self):
        """Test exception messages."""
        with pytest.raises(ValueError, match="invalid literal"):
            int("not_a_number")
    
    def test_try_except_handling(self):
        """Test try-except handling."""
        def safe_divide(a, b):
            try:
                return a / b
            except ZeroDivisionError:
                return None
        
        assert safe_divide(10, 2) == 5
        assert safe_divide(10, 0) is None


class TestFixturesAndParametrization:
    """Test pytest fixtures and parametrization."""
    
    @pytest.fixture
    def sample_data(self):
        """Provide sample data for tests."""
        return {
            'numbers': [1, 2, 3, 4, 5],
            'strings': ['hello', 'world', 'test'],
            'config': {'debug': True, 'version': '1.0'}
        }
    
    def test_fixture_usage(self, sample_data):
        """Test using fixtures."""
        assert len(sample_data['numbers']) == 5
        assert 'hello' in sample_data['strings']
        assert sample_data['config']['debug'] is True
    
    @pytest.mark.parametrize("input_value,expected", [
        (1, 1),
        (2, 4),
        (3, 9),
        (4, 16),
        (5, 25)
    ])
    def test_parametrized_square(self, input_value, expected):
        """Test parametrized square function."""
        assert input_value ** 2 == expected
    
    @pytest.mark.parametrize("text,expected_length", [
        ("hello", 5),
        ("world", 5),
        ("test", 4),
        ("", 0)
    ])
    def test_parametrized_string_length(self, text, expected_length):
        """Test parametrized string length."""
        assert len(text) == expected_length