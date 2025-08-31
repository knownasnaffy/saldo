# Requirements Document

## Introduction

This feature adds a configuration management command to the Saldo application, allowing users to update the rate per clothing item after the initial setup. The feature ensures that rate changes only affect future transactions while preserving the integrity of historical transaction records.

## Requirements

### Requirement 1

**User Story:** As a user, I want to update the rate per clothing item after initial setup, so that I can adjust pricing when the ironing service changes their rates.

#### Acceptance Criteria

1. WHEN the user runs `saldo config --rate <new_rate>` THEN the system SHALL update the rate_per_item in the configuration table
2. WHEN the user runs `saldo config --rate <new_rate>` AND the new rate is positive THEN the system SHALL save the new rate successfully
3. WHEN the user runs `saldo config --rate <new_rate>` AND the new rate is zero or negative THEN the system SHALL display an error message and not update the configuration
4. WHEN the user runs `saldo config --rate <new_rate>` AND no configuration exists THEN the system SHALL display an error message directing them to run setup first

### Requirement 2

**User Story:** As a user, I want to view the current configuration settings, so that I can verify the current rate and initial balance without making changes.

#### Acceptance Criteria

1. WHEN the user runs `saldo config` without options THEN the system SHALL display the current rate per item and initial balance
2. WHEN the user runs `saldo config` AND no configuration exists THEN the system SHALL display an error message directing them to run setup first
3. WHEN the user runs `saldo config` THEN the system SHALL display the configuration creation date
4. WHEN the user runs `saldo config` THEN the system SHALL format currency values consistently with other commands

### Requirement 3

**User Story:** As a user, I want confirmation when updating the rate, so that I can avoid accidental changes to my pricing configuration.

#### Acceptance Criteria

1. WHEN the user runs `saldo config --rate <new_rate>` THEN the system SHALL display the current rate and the new rate before making changes
2. WHEN the user runs `saldo config --rate <new_rate>` THEN the system SHALL prompt for confirmation before updating the configuration
3. WHEN the user confirms the rate change THEN the system SHALL update the configuration and display a success message
4. WHEN the user declines the rate change THEN the system SHALL cancel the operation without making changes
5. WHEN the user runs `saldo config --rate <new_rate> --no-confirm` THEN the system SHALL update the configuration without prompting for confirmation
6. WHEN the user runs `saldo config --rate <new_rate> --no-confirm` THEN the system SHALL still display the rate change information but skip the confirmation prompt

### Requirement 4

**User Story:** As a user, I want assurance that changing the rate won't affect my historical transactions, so that I can maintain accurate financial records.

#### Acceptance Criteria

1. WHEN the user updates the rate THEN the system SHALL not modify any existing transaction records
2. WHEN the user updates the rate THEN future transactions SHALL use the new rate for cost calculations
3. WHEN the user updates the rate THEN the system SHALL display a message explaining that historical transactions remain unchanged
4. WHEN the user views transaction history after a rate change THEN historical transactions SHALL show their original calculated costs

### Requirement 5

**User Story:** As a user, I want the config command to follow the same validation and error handling patterns as other commands, so that I have a consistent experience.

#### Acceptance Criteria

1. WHEN the user provides an invalid rate format THEN the system SHALL display a clear error message with examples
2. WHEN the user provides an extremely high rate THEN the system SHALL prompt for confirmation before proceeding
3. WHEN a database error occurs THEN the system SHALL display an appropriate error message and exit gracefully
4. WHEN the user provides the --help flag THEN the system SHALL display comprehensive usage information and examples
