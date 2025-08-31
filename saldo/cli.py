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

    This command sets up your account configuration including:
    - Fixed rate per clothing item
    - Initial balance (positive if you owe money, negative if you have credit)

    Example:
        saldo setup --rate 2.50 --balance 10.00
        saldo setup  # Interactive prompts
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

    This command records a new transaction including:
    - Number of clothing items processed
    - Payment amount made
    - Automatically calculates cost and updates balance

    Example:
        saldo add-transaction --items 5 --payment 10.00
        saldo add-transaction  # Interactive prompts
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

    Shows your current balance with the ironing service, including:
    - Current balance amount and direction (owed/credit)
    - Configured rate per item
    - Optional transaction history with --detailed flag

    Example:
        saldo balance
        saldo balance --detailed
        saldo balance --detailed --limit 5
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

if __name__ == "__main__":
    cli()
