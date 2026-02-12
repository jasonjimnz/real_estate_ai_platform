"""Scoring CLI commands — compute and recalculate scores."""

import click
from rich.console import Console
from rich.table import Table

console = Console()


def _get_app():
    from nestscout import create_app
    return create_app()


@click.group("scoring")
def scoring_cli():
    """Property scoring commands."""
    pass


@scoring_cli.command("compute")
@click.argument("profile_id", type=int)
def compute_scores(profile_id):
    """Compute scores for all properties against a search profile.

    PROFILE_ID: The search profile ID to score against.
    """
    app = _get_app()
    with app.app_context():
        from nestscout.services.scoring_service import ScoringService

        console.print(f"⏳ Computing scores for profile {profile_id}...", style="blue")
        count = ScoringService.compute_scores(profile_id)

        if count > 0:
            console.print(f"✅ Scored {count} properties.", style="green")
        else:
            console.print("⚠️  No properties scored. Check that the profile exists and has rules.", style="yellow")


@scoring_cli.command("ranked")
@click.argument("profile_id", type=int)
@click.option("--limit", default=20, type=int, help="Number of results")
def show_ranked(profile_id, limit):
    """Show properties ranked by score for a profile.

    PROFILE_ID: The search profile ID.
    """
    app = _get_app()
    with app.app_context():
        from nestscout.services.scoring_service import ScoringService

        ranked = ScoringService.get_ranked_properties(profile_id)

        if not ranked:
            console.print("No scores found. Run 'nestscout scoring compute' first.", style="yellow")
            return

        table = Table(title=f"Properties Ranked by Profile {profile_id}")
        table.add_column("Rank", style="cyan", justify="right")
        table.add_column("Score", style="green bold", justify="right")
        table.add_column("ID")
        table.add_column("Title", max_width=35)
        table.add_column("Price", justify="right")
        table.add_column("City")

        for i, p in enumerate(ranked[:limit], 1):
            score = p.get("score", {})
            price_str = f"{p['price']:,.0f}" if p.get("price") else "-"
            table.add_row(
                str(i),
                f"{score.get('total_score', 0):.1f}",
                str(p["id"]),
                p["title"][:35],
                price_str,
                p.get("city", "-"),
            )

        console.print(table)


@scoring_cli.command("recalc")
@click.confirmation_option(prompt="Recalculate scores for ALL profiles?")
def recalculate_all():
    """Recalculate scores for all active profiles."""
    app = _get_app()
    with app.app_context():
        from sqlalchemy import select
        from nestscout.extensions import db
        from nestscout.models.search_profile import SearchProfile
        from nestscout.services.scoring_service import ScoringService

        profiles = list(db.session.execute(select(SearchProfile)).scalars())

        if not profiles:
            console.print("No profiles found.", style="yellow")
            return

        total = 0
        for profile in profiles:
            count = ScoringService.compute_scores(profile.id)
            total += count
            console.print(f"  Profile '{profile.name}' (ID {profile.id}): {count} properties scored")

        console.print(f"\n✅ Recalculation complete: {total} total scores updated.", style="green")
