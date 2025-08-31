# Design Document

## Overview

The config command feature adds configuration management capabilities to the Saldo CLI application. This command allows users to view current configuration settings and update the rate per clothing item after initial setup. The design ensures consistency with existing CLI patterns while maintaining data integrity for historical transactions.

## Architecture

The config command follows the established layered architecture pattern:

- **CLI Layer**: New `config` command in `cli.py` with Click decorators and user interaction
- **Business Logic Layer**: New methods in `TransactionManager` for configuration updates
- **Data Access Layer**: New method in `DatabaseManager` for updating configuration
- **Data Storage**: Utilizes existing `configuration` table in SQLite database

## Components and Interfaces

### CLI Command Interface

```python
@cli.command()
@click.option("-r", "--rate", type=float, help="New rate per clothing item")
@click.option("--no-confirm", is_flag=True, help="Skip confirmation prompt")
def config(rate: Optional[float], no_confirm: bool):
    """View or update configuration settings."""
```

**Command Behaviors:**

- `saldo config` - Display current configuration
- `saldo config --rate 3.50` - Update rate with confirmation
- `saldo config --rate 3.50 --no-confirm` - Update rate without confirmation

### TransactionManager Extensions

```python
def update_rate(self, new_rate: float) -> Dict[str, Any]:
    """Update the rate per item in configuration."""

def get_configuration_display(self) -> Dict[str, Any]:
    """Get configuration data formatted for display."""
```

### DatabaseManager Extensions

```python
def update_configuration_rate(self, new_rate: float) -> None:
    """Update only the rate_per_item in the configuration table."""
```

## Data Models

### Configuration Update Flow

The configuration update process maintains data integrity:

1. **Validation**: New rate must be positive and reasonable
2. **Current State Retrieval**: Get existing configuration for comparison
3. **User Confirmation**: Display current vs new rate (unless --no-confirm)
4. **Database Update**: Update only the `rate_per_item` field
5. **Success Confirmation**: Display updated configuration

### Database Schema Impact

No schema changes required. The existing `configuration` table supports rate updates:

```sql
-- Existing table structure (no changes needed)
CREATE TABLE configuration (
    id INTEGER PRIMARY KEY,
    rate_per_item REAL NOT NULL CHECK(rate_per_item > 0),
    initial_balance REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Update Strategy**: Use UPDATE statement to modify only `rate_per_item` field, preserving `initial_balance` and `created_at`.

## Error Handling

### Validation Errors

- **Invalid Rate Format**: Clear error message with examples
- **Non-positive Rate**: Error message explaining rate must be positive
- **Extremely High Rate**: Confirmation prompt (>1000) unless --no-confirm
- **Missing Configuration**: Error directing user to run `saldo setup` first

### Database Errors

- **Connection Issues**: Standard database error handling with user-friendly messages
- **Constraint Violations**: Specific error messages for rate validation failures
- **Transaction Failures**: Rollback and clear error reporting

### User Experience Errors

- **Confirmation Declined**: Clean cancellation message
- **Invalid Options**: Help text display for incorrect usage

## Testing Strategy

### Unit Tests

**TransactionManager Tests** (`test_transaction_manager.py`):

- `test_update_rate_valid()` - Successful rate update
- `test_update_rate_invalid_negative()` - Negative rate rejection
- `test_update_rate_invalid_zero()` - Zero rate rejection
- `test_update_rate_no_config()` - Missing configuration error
- `test_get_configuration_display()` - Configuration formatting

**DatabaseManager Tests** (`test_database.py`):

- `test_update_configuration_rate()` - Database update operation
- `test_update_configuration_rate_preserves_balance()` - Initial balance preservation
- `test_update_configuration_rate_invalid()` - Constraint validation

### CLI Tests

**CLI Integration Tests** (`test_cli.py`):

- `test_config_display()` - Configuration display functionality
- `test_config_update_with_confirmation()` - Rate update with user confirmation
- `test_config_update_no_confirm()` - Rate update with --no-confirm flag
- `test_config_update_invalid_rate()` - Invalid rate handling
- `test_config_no_configuration()` - Missing configuration error
- `test_config_user_declines()` - Confirmation declined scenario

### Integration Tests

**End-to-End Workflow Tests** (`test_integration.py`):

- `test_rate_change_affects_future_transactions()` - Verify new rate applies to future transactions
- `test_rate_change_preserves_historical_transactions()` - Verify historical data integrity
- `test_config_workflow_complete()` - Full configuration management workflow

## Implementation Considerations

### Consistency with Existing Patterns

1. **CLI Options**: Follow existing short/long option patterns (`-r, --rate`)
2. **Error Messages**: Use consistent emoji and formatting (❌, ⚠️, ✅)
3. **Currency Display**: Use ₹ symbol and 2 decimal places consistently
4. **Validation**: Apply same validation patterns as setup command
5. **Confirmation Prompts**: Use existing click.confirm patterns

### Data Integrity Safeguards

1. **Transaction Independence**: Historical transactions remain unchanged
2. **Configuration Atomicity**: Rate updates are atomic database operations
3. **Validation Consistency**: Same validation rules as initial setup
4. **Rollback Safety**: Database transactions with proper error handling

### User Experience Design

1. **Clear Information Display**: Show current and new rates before confirmation
2. **Helpful Error Messages**: Guide users to correct actions
3. **Consistent Formatting**: Match existing command output styles
4. **Confirmation Safety**: Prevent accidental changes with confirmation prompts
5. **Test Automation Support**: --no-confirm flag for automated testing

### Performance Considerations

1. **Single Query Updates**: Use UPDATE statements instead of DELETE/INSERT
2. **Minimal Database Calls**: Batch configuration retrieval and updates
3. **Efficient Validation**: Validate before database operations
4. **Connection Reuse**: Leverage existing DatabaseManager connection patterns
