"""Unit tests for custom exceptions."""

import pytest
from saldo.exceptions import SaldoError, DatabaseError, ValidationError, ConfigurationError


class TestSaldoError:
    """Test cases for base SaldoError exception."""
    
    def test_basic_error_creation(self):
        """Test creating a basic SaldoError."""
        error = SaldoError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details is None
    
    def test_error_with_details(self):
        """Test creating SaldoError with details."""
        error = SaldoError("Test error", "Additional details")
        
        assert str(error) == "Test error: Additional details"
        assert error.message == "Test error"
        assert error.details == "Additional details"
    
    def test_error_inheritance(self):
        """Test that SaldoError inherits from Exception."""
        error = SaldoError("Test")
        assert isinstance(error, Exception)
    
    def test_error_raising(self):
        """Test raising and catching SaldoError."""
        with pytest.raises(SaldoError) as exc_info:
            raise SaldoError("Test error")
        
        assert str(exc_info.value) == "Test error"


class TestDatabaseError:
    """Test cases for DatabaseError exception."""
    
    def test_database_error_creation(self):
        """Test creating a DatabaseError."""
        error = DatabaseError("Database connection failed")
        
        assert str(error) == "Database connection failed"
        assert error.message == "Database connection failed"
        assert isinstance(error, SaldoError)
    
    def test_database_error_with_details(self):
        """Test DatabaseError with details."""
        error = DatabaseError("Query failed", "Table does not exist")
        
        assert str(error) == "Query failed: Table does not exist"
        assert error.details == "Table does not exist"
    
    def test_database_error_inheritance(self):
        """Test DatabaseError inheritance chain."""
        error = DatabaseError("Test")
        assert isinstance(error, DatabaseError)
        assert isinstance(error, SaldoError)
        assert isinstance(error, Exception)
    
    def test_database_error_raising(self):
        """Test raising and catching DatabaseError."""
        with pytest.raises(DatabaseError) as exc_info:
            raise DatabaseError("Connection timeout")
        
        assert "Connection timeout" in str(exc_info.value)
        
        # Should also be catchable as SaldoError
        with pytest.raises(SaldoError):
            raise DatabaseError("Connection timeout")


class TestValidationError:
    """Test cases for ValidationError exception."""
    
    def test_validation_error_creation(self):
        """Test creating a ValidationError."""
        error = ValidationError("Invalid input provided")
        
        assert str(error) == "Invalid input provided"
        assert error.message == "Invalid input provided"
        assert isinstance(error, SaldoError)
    
    def test_validation_error_with_details(self):
        """Test ValidationError with details."""
        error = ValidationError("Invalid rate", "Rate must be positive")
        
        assert str(error) == "Invalid rate: Rate must be positive"
        assert error.details == "Rate must be positive"
    
    def test_validation_error_inheritance(self):
        """Test ValidationError inheritance chain."""
        error = ValidationError("Test")
        assert isinstance(error, ValidationError)
        assert isinstance(error, SaldoError)
        assert isinstance(error, Exception)
    
    def test_validation_error_raising(self):
        """Test raising and catching ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Invalid number format")
        
        assert "Invalid number format" in str(exc_info.value)
        
        # Should also be catchable as SaldoError
        with pytest.raises(SaldoError):
            raise ValidationError("Invalid number format")


class TestConfigurationError:
    """Test cases for ConfigurationError exception."""
    
    def test_configuration_error_creation(self):
        """Test creating a ConfigurationError."""
        error = ConfigurationError("Setup not completed")
        
        assert str(error) == "Setup not completed"
        assert error.message == "Setup not completed"
        assert isinstance(error, SaldoError)
    
    def test_configuration_error_with_details(self):
        """Test ConfigurationError with details."""
        error = ConfigurationError("Missing config", "Run setup command first")
        
        assert str(error) == "Missing config: Run setup command first"
        assert error.details == "Run setup command first"
    
    def test_configuration_error_inheritance(self):
        """Test ConfigurationError inheritance chain."""
        error = ConfigurationError("Test")
        assert isinstance(error, ConfigurationError)
        assert isinstance(error, SaldoError)
        assert isinstance(error, Exception)
    
    def test_configuration_error_raising(self):
        """Test raising and catching ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Database not initialized")
        
        assert "Database not initialized" in str(exc_info.value)
        
        # Should also be catchable as SaldoError
        with pytest.raises(SaldoError):
            raise ConfigurationError("Database not initialized")


class TestExceptionHierarchy:
    """Test cases for exception hierarchy behavior."""
    
    def test_catch_all_saldo_errors(self):
        """Test catching all Saldo errors with base exception."""
        errors = [
            DatabaseError("DB error"),
            ValidationError("Validation error"),
            ConfigurationError("Config error"),
            SaldoError("Base error")
        ]
        
        for error in errors:
            with pytest.raises(SaldoError):
                raise error
    
    def test_specific_error_catching(self):
        """Test catching specific error types."""
        # DatabaseError should not be caught as ValidationError
        with pytest.raises(DatabaseError):
            try:
                raise DatabaseError("DB error")
            except ValidationError:
                pytest.fail("DatabaseError should not be caught as ValidationError")
            except DatabaseError:
                raise
    
    def test_error_message_consistency(self):
        """Test that all error types handle messages consistently."""
        message = "Test message"
        details = "Test details"
        
        errors = [
            SaldoError(message, details),
            DatabaseError(message, details),
            ValidationError(message, details),
            ConfigurationError(message, details)
        ]
        
        for error in errors:
            assert error.message == message
            assert error.details == details
            assert str(error) == f"{message}: {details}"