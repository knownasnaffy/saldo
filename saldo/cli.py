"""
Command-line interface for the Saldo balance tracking application.

Provides Click-based CLI commands for setup, transaction management, and balance queries.
"""

import click
from typing import Optional

from .transaction_manager import TransactionManager
from .exceptions import SaldoError, ValidationError, ConfigurationError, DatabaseError


class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        # Look up the command the normal way
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        # Try aliases
        matches = [
            c
            for c, cmd in self.commands.items()
            if cmd_name in getattr(cmd, "aliases", [])
        ]
        if matches:
            return self.commands[matches[0]]
        return None


@click.group(cls=AliasedGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option("0.1.0", "-v", "--version", prog_name="saldo")
def cli():
    """Saldo - A command-line balance tracking application for ironing service transactions."""
    pass


@cli.command()
@click.option("-r", "--rate", type=float, help="Rate per clothing item")
@click.option(
    "-b",
    "--balance",
    type=float,
    help="Initial balance (positive = owed, negative = credit)",
)
def setup(rate: Optional[float], balance: Optional[float]):
    """Initialize the application with ironing service rate and current balance.

    \b
    This command sets up your account configuration including:
      - Fixed rate per clothing item
      - Initial balance (positive if you owe money, negative if you have credit)

    \b
    Example:
      $ saldo setup --rate 2.50 --balance 10.00
      $ saldo setup  # Interactive prompts
    """
    try:
        transaction_manager = TransactionManager()

        # Check if configuration already exists
        try:
            existing_config = transaction_manager.db_manager.get_configuration()
            if existing_config:
                click.echo("⚠️  Configuration already exists!")
                click.echo(
                    f"Current rate: ₹{existing_config['rate_per_item']:.2f} per item"
                )
                click.echo(
                    f"Initial balance: ₹{existing_config['initial_balance']:.2f}"
                )

                if not click.confirm(
                    "Do you want to overwrite the existing configuration?"
                ):
                    click.echo("Setup cancelled.")
                    return
        except DatabaseError:
            # Database might not be initialized yet, continue with setup
            pass

        # Get rate from user if not provided
        if rate is None:
            while True:
                try:
                    rate_input = click.prompt(
                        "Enter the rate per clothing item (e.g., 2.50)", type=str
                    )
                    rate_input = rate_input.strip()

                    # Check for empty input
                    if not rate_input:
                        click.echo("❌ Rate cannot be empty. Please try again.")
                        continue

                    rate = float(rate_input)

                    if rate <= 0:
                        click.echo(
                            "❌ Rate must be a positive number. Please try again."
                        )
                        continue

                    # Check for unusually high rates
                    if rate > 1000:
                        if not click.confirm(
                            f"⚠️  Rate ₹{rate:.2f} seems very high. Are you sure this is correct?"
                        ):
                            continue

                    break
                except ValueError:
                    click.echo(
                        "❌ Please enter a valid number (e.g., 2.50). Please try again."
                    )
                    continue

        # Validate rate
        if rate <= 0:
            raise ValidationError("Rate must be a positive number")

        # Get initial balance from user if not provided
        if balance is None:
            while True:
                try:
                    balance_input = click.prompt(
                        "Enter your current balance (positive if you owe money, negative if you have credit, 0 for new account)",
                        type=str,
                        default="0",
                    )
                    balance_input = balance_input.strip()

                    # Handle empty input (use default)
                    if not balance_input:
                        balance = 0.0
                        break

                    balance = float(balance_input)

                    # Check for unusually large balances
                    if abs(balance) > 100000:
                        if not click.confirm(
                            f"⚠️  Balance ₹{abs(balance):.2f} seems very large. Are you sure this is correct?"
                        ):
                            continue

                    break
                except ValueError:
                    click.echo(
                        "❌ Please enter a valid number (e.g., 10.50, -5.25, or 0). Please try again."
                    )
                    continue

        # Setup account with validated inputs
        transaction_manager.setup_account(rate, balance)

        # Display success message
        click.echo("✅ Account setup completed successfully!")
        click.echo(f"Rate per item: ₹{rate:.2f}")

        if balance > 0:
            click.echo(f"Initial balance: ₹{balance:.2f} (you owe)")
        elif balance < 0:
            click.echo(f"Initial balance: ₹{abs(balance):.2f} (you have credit)")
        else:
            click.echo("Initial balance: ₹0.00 (starting fresh)")

        click.echo("\nYou can now use 'saldo add-transaction' to record transactions.")

    except ValidationError as e:
        click.echo(f"❌ Validation Error: {e}", err=True)
        raise click.ClickException(str(e))
    except ConfigurationError as e:
        click.echo(f"❌ Configuration Error: {e}", err=True)
        raise click.ClickException(str(e))
    except DatabaseError as e:
        click.echo(f"❌ Database Error: {e}", err=True)
        raise click.ClickException(str(e))
    except SaldoError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.ClickException(str(e))
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        raise click.ClickException(f"Unexpected error: {e}")


@cli.command("add-transaction")
@click.option("-i", "--items", type=int, help="Number of clothing items")
@click.option("-p", "--payment", type=float, help="Payment amount")
def add_transaction(items: Optional[int], payment: Optional[float]):
    """Add a new ironing transaction with items and payment.

    \b
    This command records a new transaction including:
      - Number of clothing items processed
      - Payment amount made
      - Automatically calculates cost and updates balance

    \b
    Example:
      $ saldo add-transaction --items 5 --payment 10.00
      $ saldo add-transaction  # Interactive prompts
    """
    try:
        transaction_manager = TransactionManager()

        # Check if configuration exists
        try:
            config = transaction_manager.db_manager.get_configuration()
            if not config:
                click.echo("❌ No configuration found. Please run 'saldo setup' first.")
                raise click.ClickException("Configuration required")
        except DatabaseError as e:
            click.echo(f"❌ Database Error: {e}", err=True)
            raise click.ClickException(str(e))

        # Get current balance to show context
        current_balance = transaction_manager.get_current_balance()
        rate = config["rate_per_item"]

        # Get number of items from user if not provided
        if items is None:
            while True:
                try:
                    items_input = click.prompt(
                        "Enter the number of clothing items processed", type=str
                    )
                    items_input = items_input.strip()

                    # Check for empty input
                    if not items_input:
                        click.echo(
                            "❌ Number of items cannot be empty. Please try again."
                        )
                        continue

                    items = int(items_input)

                    if items < 0:
                        click.echo(
                            "❌ Number of items cannot be negative. Please try again."
                        )
                        continue

                    # Check for unusually large item counts
                    if items > 1000:
                        if not click.confirm(
                            f"⚠️  {items} items seems like a lot. Are you sure this is correct?"
                        ):
                            continue

                    break
                except ValueError:
                    click.echo(
                        "❌ Please enter a valid whole number (e.g., 5, 10, 0). Please try again."
                    )
                    continue

        # Validate items
        if items < 0:
            raise ValidationError("Number of items cannot be negative")

        # Calculate and display cost information
        cost = transaction_manager.calculate_cost(items)
        total_due = current_balance + cost

        click.echo("\n📊 Transaction Summary:")
        click.echo(f"Items processed: {items}")
        click.echo(f"Cost per item: ₹{rate:.2f}")
        click.echo(f"Total cost: ₹{cost:.2f}")
        click.echo(f"Previous balance: ₹{current_balance:.2f}")
        click.echo(f"Total amount due: ₹{total_due:.2f}")

        # Get payment amount from user if not provided
        if payment is None:
            while True:
                try:
                    payment_input = click.prompt(
                        f"Enter payment amount (total due: ₹{total_due:.2f})", type=str
                    )
                    payment_input = payment_input.strip()

                    # Check for empty input
                    if not payment_input:
                        click.echo(
                            "❌ Payment amount cannot be empty. Please try again."
                        )
                        continue

                    payment = float(payment_input)

                    # Check for unusually large payments
                    if abs(payment) > 100000:
                        if not click.confirm(
                            f"⚠️  Payment amount ₹{abs(payment):.2f} seems very large. Are you sure this is correct?"
                        ):
                            continue

                    # Warn about negative payments (refunds)
                    if payment < 0:
                        if not click.confirm(
                            f"⚠️  Negative payment (₹{abs(payment):.2f} refund). Is this correct?"
                        ):
                            continue

                    break
                except ValueError:
                    click.echo(
                        "❌ Please enter a valid number (e.g., 10.50, 0, -5.25). Please try again."
                    )
                    continue

        # Process the transaction
        transaction_result = transaction_manager.add_transaction(items, payment)

        # Display results
        new_balance = transaction_result["balance_after"]
        click.echo("\n✅ Transaction recorded successfully!")
        click.echo(f"Payment received: ₹{payment:.2f}")

        if new_balance > 0:
            click.echo(f"New balance: ₹{new_balance:.2f} (you owe)")
        elif new_balance < 0:
            click.echo(f"New balance: ₹{abs(new_balance):.2f} (you have credit)")
        else:
            click.echo("New balance: ₹0.00 (all settled)")

        # Show change information
        change = payment - cost
        if change > 0:
            click.echo(f"Overpayment: ₹{change:.2f} (applied as credit)")
        elif change < 0:
            click.echo(f"Underpayment: ₹{abs(change):.2f} (added to balance)")

    except ValidationError as e:
        click.echo(f"❌ Validation Error: {e}", err=True)
        raise click.ClickException(str(e))
    except ConfigurationError as e:
        click.echo(f"❌ Configuration Error: {e}", err=True)
        raise click.ClickException(str(e))
    except DatabaseError as e:
        click.echo(f"❌ Database Error: {e}", err=True)
        raise click.ClickException(str(e))
    except SaldoError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.ClickException(str(e))
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        raise click.ClickException(f"Unexpected error: {e}")


add_transaction.aliases = ["add"]


@cli.command()
@click.option(
    "-d", "--detailed", is_flag=True, help="Show detailed transaction history"
)
@click.option(
    "-l",
    "--limit",
    type=int,
    default=10,
    help="Number of recent transactions to show (default: 10)",
)
def balance(detailed: bool, limit: int):
    """Display current balance and rate information.

    \b
    Shows your current balance with the ironing service, including:
      - Current balance amount and direction (owed/credit)
      - Configured rate per item
      - Optional transaction history with --detailed flag

    \b
    Example:
      $ saldo balance
      $ saldo balance --detailed
      $ saldo balance --detailed --limit 5
    """
    try:
        transaction_manager = TransactionManager()

        # Check if configuration exists
        try:
            config = transaction_manager.db_manager.get_configuration()
            if not config:
                click.echo("❌ No configuration found. Please run 'saldo setup' first.")
                raise click.ClickException("Configuration required")
        except DatabaseError as e:
            click.echo(f"❌ Database Error: {e}", err=True)
            raise click.ClickException(str(e))

        # Get current balance and configuration
        current_balance = transaction_manager.get_current_balance()
        rate = config["rate_per_item"]

        # Display header
        click.echo("💰 Saldo Balance Summary")
        click.echo("=" * 25)

        # Display rate information
        click.echo(f"Rate per item: ₹{rate:.2f}")

        # Display balance with clear indication of direction
        if current_balance > 0:
            click.echo(f"Current balance: ₹{current_balance:.2f} (you owe)")
            click.echo("💳 You have an outstanding balance to pay.")
        elif current_balance < 0:
            click.echo(
                f"Current balance: ₹{abs(current_balance):.2f} (you have credit)"
            )
            click.echo("✨ You have credit available for future transactions.")
        else:
            click.echo("Current balance: ₹0.00 (all settled)")
            click.echo("✅ Your account is fully settled.")

        # Show detailed transaction history if requested
        if detailed:
            try:
                transactions = transaction_manager.db_manager.get_transactions(
                    limit=limit
                )

                if transactions:
                    click.echo(
                        f"\n📋 Recent Transactions (last {min(len(transactions), limit)}):"
                    )
                    click.echo("-" * 70)
                    click.echo(
                        f"{'Date':<12} {'Items':<6} {'Cost':<8} {'Payment':<8} {'Balance':<10}"
                    )
                    click.echo("-" * 70)

                    for transaction in transactions:
                        # Parse date from timestamp
                        date_str = transaction["created_at"][:10]  # YYYY-MM-DD format
                        items = transaction["items"]
                        cost = transaction["cost"]
                        payment = transaction["payment"]
                        balance = transaction["balance_after"]

                        click.echo(
                            f"{date_str:<12} {items:<6} ₹{cost:<7.2f} ₹{payment:<7.2f} ₹{balance:<9.2f}"
                        )

                    click.echo("-" * 70)

                    # Show summary statistics
                    total_items = sum(t["items"] for t in transactions)
                    total_cost = sum(t["cost"] for t in transactions)
                    total_payments = sum(t["payment"] for t in transactions)

                    click.echo(f"\n📊 Summary (last {len(transactions)} transactions):")
                    click.echo(f"Total items processed: {total_items}")
                    click.echo(f"Total cost: ₹{total_cost:.2f}")
                    click.echo(f"Total payments: ₹{total_payments:.2f}")

                else:
                    click.echo("\n📋 No transactions found.")
                    click.echo(
                        "Use 'saldo add-transaction' to record your first transaction."
                    )

            except DatabaseError as e:
                click.echo(f"\n⚠️  Could not retrieve transaction history: {e}")

        else:
            # Show hint about detailed view
            click.echo(
                "\n💡 Use 'saldo balance --detailed' to see transaction history."
            )

    except ConfigurationError as e:
        click.echo(f"❌ Configuration Error: {e}", err=True)
        raise click.ClickException(str(e))
    except DatabaseError as e:
        click.echo(f"❌ Database Error: {e}", err=True)
        raise click.ClickException(str(e))
    except SaldoError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.ClickException(str(e))
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        raise click.ClickException(f"Unexpected error: {e}")


balance.aliases = ["bal"]


def validate_rate_option(ctx, param, value):
    """Validate rate option with user-friendly error messages."""
    if value is None:
        return value

    try:
        # Click already converted to float, but let's add additional validation
        if not isinstance(value, (int, float)):
            raise click.BadParameter("Rate must be a valid number (e.g., 2.50, 3.75)")

        # Check for NaN or infinity
        if not (value == value) or value == float("inf") or value == float("-inf"):
            raise click.BadParameter("Rate must be a finite number")

        return value
    except (ValueError, TypeError):
        raise click.BadParameter("Rate must be a valid number (e.g., 2.50, 3.75)")


@cli.command()
@click.option(
    "-r",
    "--rate",
    type=float,
    callback=validate_rate_option,
    help="New rate per clothing item",
)
@click.option("--no-confirm", is_flag=True, help="Skip confirmation prompt")
def config(rate: Optional[float], no_confirm: bool):
    """View or update configuration settings.

    \b
    This command allows you to:
      - View current configuration (rate, initial balance, creation date)
      - Update the rate per clothing item
      - Historical transactions remain unchanged when rate is updated

    \b
    Examples:
      $ saldo config                    # View current configuration
      $ saldo config --rate 3.50       # Update rate with confirmation
      $ saldo config -r 3.50 --no-confirm  # Update rate without confirmation

    \b
    Note: Changing the rate only affects future transactions.
    All historical transactions and their costs remain unchanged.
    """
    try:
        transaction_manager = TransactionManager()

        # Check if configuration exists with enhanced error handling
        try:
            existing_config = transaction_manager.db_manager.get_configuration()
            if not existing_config:
                click.echo("❌ No configuration found. Please run 'saldo setup' first.")
                click.echo("💡 Use 'saldo setup --help' for setup instructions.")
                raise click.ClickException("Configuration required")
        except DatabaseError as e:
            if "locked" in str(e).lower():
                click.echo(
                    "❌ Database is currently locked by another process.", err=True
                )
                click.echo(
                    "💡 Please close other instances of Saldo and try again.", err=True
                )
            elif "permission" in str(e).lower() or "access" in str(e).lower():
                click.echo(
                    "❌ Database access denied. Check file permissions.", err=True
                )
                click.echo("💡 Ensure you have write access to ~/.saldo/", err=True)
            elif "disk" in str(e).lower() or "space" in str(e).lower():
                click.echo(
                    "❌ Insufficient disk space for database operation.", err=True
                )
                click.echo("💡 Please free up disk space and try again.", err=True)
            else:
                click.echo(f"❌ Database Error: {e}", err=True)
                click.echo(
                    "💡 Try restarting the application or check database integrity.",
                    err=True,
                )
            raise click.ClickException(str(e))

        # If no rate provided, display current configuration
        if rate is None:
            try:
                config_display = transaction_manager.get_configuration_display()
            except ConfigurationError as e:
                click.echo(
                    "❌ Configuration Error: Cannot retrieve configuration.", err=True
                )
                click.echo(
                    "💡 Please run 'saldo setup' to initialize configuration.", err=True
                )
                raise click.ClickException(str(e))
            except DatabaseError as e:
                click.echo("❌ Database Error: Cannot access configuration.", err=True)
                click.echo(
                    "💡 Please check database connectivity and try again.", err=True
                )
                raise click.ClickException(str(e))

            click.echo("⚙️  Current Configuration")
            click.echo("=" * 25)
            click.echo(f"Rate per item: ₹{config_display['rate_per_item']:.2f}")
            click.echo(f"Initial balance: ₹{config_display['initial_balance']:.2f}")
            click.echo(f"Created: {config_display['created_at']}")

            try:
                current_balance = transaction_manager.get_current_balance()
                if current_balance > 0:
                    click.echo(f"Current balance: ₹{current_balance:.2f} (you owe)")
                elif current_balance < 0:
                    click.echo(
                        f"Current balance: ₹{abs(current_balance):.2f} (you have credit)"
                    )
                else:
                    click.echo("Current balance: ₹0.00 (all settled)")
            except DatabaseError as e:
                click.echo("⚠️  Could not retrieve current balance.", err=True)
                click.echo(f"Database error: {e}", err=True)

            click.echo("\n💡 Use 'saldo config --rate <amount>' to update the rate.")
            click.echo("💡 Example: saldo config --rate 3.50")
            return

        # Comprehensive rate validation
        if not isinstance(rate, (int, float)):
            click.echo("❌ Rate must be a valid number (e.g., 2.50, 3.75).")
            click.echo("💡 Examples: --rate 2.50 or --rate 3.00")
            raise click.ClickException("Invalid rate format")

        if rate <= 0:
            click.echo("❌ Rate must be a positive number greater than zero.")
            click.echo("💡 Example: --rate 2.50")
            raise click.ClickException("Invalid rate value")

        # Check for extremely small rates (likely input errors)
        if rate < 0.01:
            click.echo("❌ Rate seems too small. Minimum rate is ₹0.01.")
            click.echo("💡 Did you mean a larger amount? Example: --rate 2.50")
            raise click.ClickException("Rate too small")

        # Check for extremely high rates with enhanced confirmation
        if rate > 1000:
            if not no_confirm:
                click.echo(f"⚠️  Rate ₹{rate:.2f} seems unusually high.")
                click.echo("💡 Most ironing services charge between ₹1-50 per item.")
                if not click.confirm("Are you sure this rate is correct?"):
                    click.echo("Rate update cancelled.")
                    return
            else:
                # Even with --no-confirm, log a warning for very high rates
                click.echo(f"⚠️  Warning: Using very high rate of ₹{rate:.2f} per item.")

        # Check for moderately high rates (100-1000) with softer warning
        elif rate > 100:
            if not no_confirm:
                click.echo(f"⚠️  Rate ₹{rate:.2f} is quite high.")
                if not click.confirm("Is this rate correct?"):
                    click.echo("Rate update cancelled.")
                    return

        # Display current vs new rate information
        current_rate = existing_config["rate_per_item"]
        click.echo("📊 Rate Update Summary")
        click.echo("=" * 22)
        click.echo(f"Current rate: ₹{current_rate:.2f} per item")
        click.echo(f"New rate: ₹{rate:.2f} per item")

        if rate > current_rate:
            change = rate - current_rate
            click.echo(
                f"Increase: ₹{change:.2f} per item (+{(change/current_rate)*100:.1f}%)"
            )
        elif rate < current_rate:
            change = current_rate - rate
            click.echo(
                f"Decrease: ₹{change:.2f} per item (-{(change/current_rate)*100:.1f}%)"
            )
        else:
            click.echo("No change in rate.")
            return

        # Confirmation prompt unless --no-confirm is used
        if not no_confirm:
            click.echo("\n📋 Transaction Independence Information:")
            click.echo("=" * 40)
            click.echo("✅ All historical transactions will remain unchanged")
            click.echo("✅ Past transaction costs will keep their original values")
            click.echo("✅ Your transaction history will stay accurate")
            click.echo("🔮 Only future transactions will use the new rate")
            click.echo("💡 This ensures your financial records remain consistent")

            if not click.confirm("\nDo you want to update the rate?"):
                click.echo("Rate update cancelled.")
                return

        # Show transaction independence information even with --no-confirm
        if no_confirm:
            click.echo("\n📋 Transaction Independence Information:")
            click.echo("=" * 40)
            click.echo("✅ All historical transactions will remain unchanged")
            click.echo("✅ Past transaction costs will keep their original values")
            click.echo("🔮 Future transactions will use the new rate")

        # Update the rate with enhanced error handling
        try:
            update_result = transaction_manager.update_rate(rate)
        except ValidationError as e:
            if "unusually high" in str(e):
                click.echo("❌ Rate validation failed: Rate is too high.", err=True)
                click.echo("💡 Please verify the rate amount and try again.", err=True)
            elif "positive" in str(e):
                click.echo(
                    "❌ Rate validation failed: Rate must be positive.", err=True
                )
                click.echo("💡 Example: --rate 2.50", err=True)
            else:
                click.echo(f"❌ Rate validation failed: {e}", err=True)
            raise click.ClickException(str(e))
        except DatabaseError as e:
            if "locked" in str(e).lower():
                click.echo("❌ Cannot update rate: Database is locked.", err=True)
                click.echo(
                    "💡 Please close other instances of Saldo and try again.", err=True
                )
            elif "constraint" in str(e).lower():
                click.echo("❌ Cannot update rate: Invalid rate value.", err=True)
                click.echo("💡 Rate must be a positive number.", err=True)
            else:
                click.echo(f"❌ Failed to update rate: {e}", err=True)
                click.echo(
                    "💡 Please check database connectivity and try again.", err=True
                )
            raise click.ClickException(str(e))

        # Display success message with detailed transaction independence confirmation
        click.echo("\n✅ Rate updated successfully!")
        click.echo(f"New rate: ₹{update_result['new_rate']:.2f} per item")

        click.echo("\n📋 Transaction Independence Confirmed:")
        click.echo("=" * 35)
        click.echo("✅ All historical transactions remain unchanged")
        click.echo("✅ Past costs and balances are preserved exactly")
        click.echo("✅ Your financial history maintains complete accuracy")
        click.echo("🔮 Future transactions will use the new rate")
        click.echo("💡 You can safely view your transaction history anytime")

    except ValidationError as e:
        # ValidationError already handled above in specific cases, this is fallback
        click.echo(f"❌ Validation Error: {e}", err=True)
        if "rate" in str(e).lower():
            click.echo(
                "💡 Please provide a valid positive rate (e.g., --rate 2.50)", err=True
            )
        raise click.ClickException(str(e))
    except ConfigurationError as e:
        # ConfigurationError already handled above in specific cases, this is fallback
        click.echo(f"❌ Configuration Error: {e}", err=True)
        if "not found" in str(e).lower():
            click.echo(
                "💡 Run 'saldo setup' to initialize your configuration.", err=True
            )
        raise click.ClickException(str(e))
    except DatabaseError as e:
        # DatabaseError already handled above in specific cases, this is fallback
        click.echo(f"❌ Database Error: {e}", err=True)
        click.echo("💡 Please check database connectivity and permissions.", err=True)
        raise click.ClickException(str(e))
    except SaldoError as e:
        click.echo(f"❌ Error: {e}", err=True)
        click.echo("💡 Please check your input and try again.", err=True)
        raise click.ClickException(str(e))
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        click.echo("💡 Please report this issue if it persists.", err=True)
        raise click.ClickException(f"Unexpected error: {e}")


if __name__ == "__main__":
    cli()
