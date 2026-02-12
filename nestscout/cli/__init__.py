"""NestScout CLI — main entry point.

Registered as `nestscout` command via pyproject.toml entry points.
"""

import click

from nestscout.cli.db import db_cli
from nestscout.cli.users import users_cli
from nestscout.cli.properties import properties_cli
from nestscout.cli.pois import pois_cli
from nestscout.cli.scoring import scoring_cli
from nestscout.cli.ai import ai_cli


@click.group()
@click.version_option(version="0.1.0", prog_name="nestscout")
def cli():
    """🏠 NestScout — AI-powered real estate intelligence platform."""
    pass


cli.add_command(db_cli, "db")
cli.add_command(users_cli, "users")
cli.add_command(properties_cli, "properties")
cli.add_command(pois_cli, "pois")
cli.add_command(scoring_cli, "scoring")
cli.add_command(ai_cli, "ai")


if __name__ == "__main__":
    cli()
