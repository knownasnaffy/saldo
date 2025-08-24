"""Custom exceptions for the Saldo balance tracking application."""


class SaldoError(Exception):
    """Base exception for all Saldo application errors.

    This is the parent class for all custom exceptions in the application.
    It provides a consistent interface for error handling throughout the system.
    """

    def __init__(self, message: str, details: str = None):
        """Initialize the exception with a message and optional details.

        Args:
            message: Primary error message
            details: Additional error details or context
        """
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self):
        """Return a formatted error message."""
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class DatabaseError(SaldoError):
    """Exception raised for database operation errors.

    This includes connection failures, schema issues, query errors,
    and any other database-related problems.
    """

    pass


class ValidationError(SaldoError):
    """Exception raised for input validation errors.

    This includes invalid user input, data format errors,
    and business rule violations.
    """

    pass


class ConfigurationError(SaldoError):
    """Exception raised for configuration and setup errors.

    This includes missing configuration, invalid setup parameters,
    and application initialization problems.
    """

    pass
