"""
Custom exceptions for Greeks Landscape module.

This module defines specific exception types for better error handling
and user-friendly error messages.
"""


class GreeksLandscapeError(Exception):
    """Base exception for Greeks Landscape module."""
    
    def __init__(self, message: str, error_type: str = "general_error", user_message: str = None):
        super().__init__(message)
        self.error_type = error_type
        self.user_message = user_message or message


class ValidationError(GreeksLandscapeError):
    """Exception raised for input validation errors."""
    
    def __init__(self, message: str, field: str = None, user_message: str = None):
        super().__init__(
            message, 
            error_type="validation_error",
            user_message=user_message or f"Invalid input: {message}"
        )
        self.field = field


class DataNotAvailableError(GreeksLandscapeError):
    """Exception raised when required data is not available."""
    
    def __init__(self, message: str, ticker: str = None, user_message: str = None):
        super().__init__(
            message,
            error_type="data_error", 
            user_message=user_message or f"Data not available: {message}"
        )
        self.ticker = ticker


class CalculationError(GreeksLandscapeError):
    """Exception raised when Greeks calculations fail."""
    
    def __init__(self, message: str, user_message: str = None):
        super().__init__(
            message,
            error_type="calculation_error",
            user_message=user_message or "Unable to calculate Greeks. Please check your parameters and try again."
        )


class DatabaseError(GreeksLandscapeError):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str, user_message: str = None):
        super().__init__(
            message,
            error_type="database_error",
            user_message=user_message or "Database connection error. Please try again later."
        )


class CacheError(GreeksLandscapeError):
    """Exception raised for caching-related errors."""
    
    def __init__(self, message: str, user_message: str = None):
        super().__init__(
            message,
            error_type="cache_error",
            user_message=user_message or "Caching error occurred. Data may be slower to load."
        )