"""Unit tests for data models."""

import pytest
from datetime import datetime
from saldo.models import Configuration, Transaction


class TestConfiguration:
    """Test cases for Configuration dataclass."""

    def test_valid_configuration_creation(self):
        """Test creating a valid configuration."""
        now = datetime.now()
        config = Configuration(rate_per_item=2.5, initial_balance=10.0, created_at=now)

        assert config.rate_per_item == 2.5
        assert config.initial_balance == 10.0
        assert config.created_at == now

    def test_configuration_with_negative_balance(self):
        """Test configuration with negative initial balance (credit)."""
        config = Configuration(
            rate_per_item=2.0, initial_balance=-15.0, created_at=datetime.now()
        )

        assert config.initial_balance == -15.0

    def test_configuration_with_zero_balance(self):
        """Test configuration with zero initial balance."""
        config = Configuration(
            rate_per_item=1.5, initial_balance=0.0, created_at=datetime.now()
        )

        assert config.initial_balance == 0.0

    def test_invalid_rate_zero(self):
        """Test that zero rate raises ValueError."""
        with pytest.raises(ValueError, match="Rate per item must be positive"):
            Configuration(
                rate_per_item=0.0, initial_balance=10.0, created_at=datetime.now()
            )

    def test_invalid_rate_negative(self):
        """Test that negative rate raises ValueError."""
        with pytest.raises(ValueError, match="Rate per item must be positive"):
            Configuration(
                rate_per_item=-1.0, initial_balance=10.0, created_at=datetime.now()
            )

    def test_invalid_rate_type(self):
        """Test that non-numeric rate raises TypeError."""
        with pytest.raises(TypeError, match="Rate per item must be a number"):
            Configuration(
                rate_per_item="invalid", initial_balance=10.0, created_at=datetime.now()
            )

    def test_invalid_balance_type(self):
        """Test that non-numeric balance raises TypeError."""
        with pytest.raises(TypeError, match="Initial balance must be a number"):
            Configuration(
                rate_per_item=2.0, initial_balance="invalid", created_at=datetime.now()
            )


class TestTransaction:
    """Test cases for Transaction dataclass."""

    def test_valid_transaction_creation(self):
        """Test creating a valid transaction."""
        now = datetime.now()
        transaction = Transaction(
            items=5, cost=12.5, payment=10.0, balance_after=2.5, created_at=now
        )

        assert transaction.items == 5
        assert transaction.cost == 12.5
        assert transaction.payment == 10.0
        assert transaction.balance_after == 2.5
        assert transaction.created_at == now
        assert transaction.id is None

    def test_transaction_with_id(self):
        """Test transaction with ID set."""
        transaction = Transaction(
            id=123,
            items=3,
            cost=7.5,
            payment=7.5,
            balance_after=0.0,
            created_at=datetime.now(),
        )

        assert transaction.id == 123

    def test_transaction_with_zero_payment(self):
        """Test transaction with zero payment."""
        transaction = Transaction(
            items=2, cost=5.0, payment=0.0, balance_after=5.0, created_at=datetime.now()
        )

        assert transaction.payment == 0.0

    def test_transaction_with_negative_balance(self):
        """Test transaction resulting in negative balance (credit)."""
        transaction = Transaction(
            items=1,
            cost=2.0,
            payment=5.0,
            balance_after=-3.0,
            created_at=datetime.now(),
        )

        assert transaction.balance_after == -3.0

    def test_invalid_items_negative(self):
        """Test that negative items raises ValueError."""
        with pytest.raises(ValueError, match="Number of items cannot be negative"):
            Transaction(
                items=-1,
                cost=5.0,
                payment=5.0,
                balance_after=0.0,
                created_at=datetime.now(),
            )

    def test_invalid_items_type(self):
        """Test that non-integer items raises TypeError."""
        with pytest.raises(TypeError, match="Number of items must be an integer"):
            Transaction(
                items=2.5,
                cost=5.0,
                payment=5.0,
                balance_after=0.0,
                created_at=datetime.now(),
            )

    def test_invalid_cost_negative(self):
        """Test that negative cost raises ValueError."""
        with pytest.raises(ValueError, match="Cost cannot be negative"):
            Transaction(
                items=2,
                cost=-5.0,
                payment=5.0,
                balance_after=0.0,
                created_at=datetime.now(),
            )

    def test_invalid_cost_type(self):
        """Test that non-numeric cost raises TypeError."""
        with pytest.raises(TypeError, match="Cost must be a number"):
            Transaction(
                items=2,
                cost="invalid",
                payment=5.0,
                balance_after=0.0,
                created_at=datetime.now(),
            )

    def test_invalid_payment_type(self):
        """Test that non-numeric payment raises TypeError."""
        with pytest.raises(TypeError, match="Payment must be a number"):
            Transaction(
                items=2,
                cost=5.0,
                payment="invalid",
                balance_after=0.0,
                created_at=datetime.now(),
            )

    def test_invalid_balance_type(self):
        """Test that non-numeric balance raises TypeError."""
        with pytest.raises(TypeError, match="Balance after must be a number"):
            Transaction(
                items=2,
                cost=5.0,
                payment=5.0,
                balance_after="invalid",
                created_at=datetime.now(),
            )
