# Requirements Document

## Introduction

Saldo is a command-line balance tracking application designed to manage financial transactions with an ironing service provider. The application allows users to track clothing items processed, calculate costs based on a fixed rate, manage payments, and maintain an accurate running balance. The system is designed for single-user operation on Linux systems with persistent data storage.

## Requirements

### Requirement 1

**User Story:** As a user, I want to initialize the application with my ironing service rate and current balance, so that I can start tracking transactions from a known baseline.

#### Acceptance Criteria

1. WHEN the user runs the setup command for the first time THEN the system SHALL prompt for the fixed rate per clothing item
2. WHEN the user provides a rate THEN the system SHALL validate it is a positive number
3. WHEN the user runs the setup command THEN the system SHALL prompt for any existing balance due
4. WHEN the user provides an initial balance THEN the system SHALL accept positive (owed) or negative (credit) values
5. WHEN setup is complete THEN the system SHALL create a SQLite database to store configuration and transactions
6. WHEN setup has already been completed THEN the system SHALL prevent re-initialization without explicit confirmation

### Requirement 2

**User Story:** As a user, I want to add new ironing transactions with the number of clothes and payment amount, so that I can track what I owe or am owed.

#### Acceptance Criteria

1. WHEN the user runs the add-transaction command THEN the system SHALL prompt for the number of clothing items
2. WHEN the user provides the number of items THEN the system SHALL calculate the total cost using the configured rate
3. WHEN the cost is calculated THEN the system SHALL display the amount due including any previous balance
4. WHEN the amount due is displayed THEN the system SHALL prompt for the payment amount being made
5. WHEN the user provides a payment amount THEN the system SHALL record the transaction with timestamp, items, cost, and payment
6. WHEN the transaction is recorded THEN the system SHALL update the running balance (previous balance + cost - payment)
7. WHEN the transaction is complete THEN the system SHALL display the new balance to the user

### Requirement 3

**User Story:** As a user, I want to check my current balance, so that I know how much I owe or am owed by the ironing service.

#### Acceptance Criteria

1. WHEN the user runs the balance command THEN the system SHALL display the current balance amount
2. WHEN displaying the balance THEN the system SHALL clearly indicate if the amount is owed to or by the user
3. WHEN displaying the balance THEN the system SHALL show the configured rate per item
4. WHEN the user requests detailed balance information THEN the system SHALL display recent transaction history
5. WHEN no transactions exist THEN the system SHALL display only the initial balance from setup

### Requirement 4

**User Story:** As a user, I want my transaction data to be persistently stored, so that I don't lose my balance history between application runs.

#### Acceptance Criteria

1. WHEN the application starts THEN the system SHALL connect to the SQLite database file
2. WHEN the database doesn't exist THEN the system SHALL create it with the required schema
3. WHEN transactions are added THEN the system SHALL store them with complete audit information
4. WHEN the application is restarted THEN the system SHALL restore the previous balance and configuration
5. IF the database file is corrupted THEN the system SHALL display an appropriate error message

### Requirement 5

**User Story:** As a user, I want clear error messages and input validation, so that I can use the application without confusion or data corruption.

#### Acceptance Criteria

1. WHEN the user provides invalid input THEN the system SHALL display a clear error message and prompt again
2. WHEN the user provides non-numeric values for rates or amounts THEN the system SHALL reject the input with explanation
3. WHEN the user provides negative values for clothing items THEN the system SHALL reject the input
4. WHEN database operations fail THEN the system SHALL display appropriate error messages without crashing
5. WHEN the user runs commands before setup THEN the system SHALL guide them to run setup first
