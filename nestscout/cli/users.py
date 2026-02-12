"""User CLI commands — create and list users."""

import click
from rich.console import Console
from rich.table import Table

console = Console()


def _get_app():
    from nestscout import create_app
    return create_app()


@click.group("users")
def users_cli():
    """User management commands."""
    pass


@users_cli.command("create")
@click.option("--username", prompt="Username", help="Unique username")
@click.option("--email", prompt="Email", help="Email address")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Password")
@click.option("--role", type=click.Choice(["user", "contributor", "admin"]), default="user")
def create_user(username: str, email: str, password: str, role: str):
    """Create a new user account."""
    app = _get_app()
    with app.app_context():
        from nestscout.services.auth_service import AuthService
        try:
            user = AuthService.register(username=username, email=email, password=password, role=role)
            console.print(f"✅ User created: {user.username} ({user.email}) [role={user.role}]", style="green")
        except ValueError as e:
            console.print(f"❌ Error: {e}", style="red")


@users_cli.command("list")
def list_users():
    """List all registered users."""
    app = _get_app()
    with app.app_context():
        from nestscout.services.auth_service import AuthService
        users = AuthService.list_users()

        if not users:
            console.print("No users found.", style="yellow")
            return

        table = Table(title="Users")
        table.add_column("ID", style="cyan")
        table.add_column("Username", style="green")
        table.add_column("Email")
        table.add_column("Role", style="magenta")
        table.add_column("Active")
        table.add_column("Created")

        for u in users:
            table.add_row(
                str(u.id), u.username, u.email, u.role,
                "✓" if u.is_active else "✗",
                u.created_at.strftime("%Y-%m-%d") if u.created_at else "-",
            )

        console.print(table)
