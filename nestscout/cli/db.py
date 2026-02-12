"""DB CLI commands — init, seed, reset."""

import click
from rich.console import Console

console = Console()


def _get_app():
    """Create or get the Flask app for CLI context."""
    from nestscout import create_app
    return create_app()


@click.group("db")
def db_cli():
    """Database management commands."""
    pass


@db_cli.command("init")
def init_db():
    """Create all database tables (dev only — use migrations in prod)."""
    app = _get_app()
    with app.app_context():
        from nestscout.extensions import db
        import nestscout.models  # noqa: F401 — Ensure all models are loaded for create_all

        db.create_all()
        console.print("✅ Database tables created.", style="green")


@db_cli.command("seed")
def seed_db():
    """Seed the database with sample data."""
    app = _get_app()
    with app.app_context():
        from nestscout.extensions import db
        from nestscout.models import POICategory, DataSource

        # Seed POI categories
        default_categories = [
            {"name": "Café", "icon": "☕", "color": "#8B4513"},
            {"name": "Restaurant", "icon": "🍽️", "color": "#FF6347"},
            {"name": "Supermarket", "icon": "🛒", "color": "#228B22"},
            {"name": "School", "icon": "🏫", "color": "#4169E1"},
            {"name": "Hospital", "icon": "🏥", "color": "#DC143C"},
            {"name": "Pharmacy", "icon": "💊", "color": "#00CED1"},
            {"name": "Gym", "icon": "🏋️", "color": "#FF8C00"},
            {"name": "Park", "icon": "🌳", "color": "#32CD32"},
            {"name": "Metro Station", "icon": "🚇", "color": "#6A5ACD"},
            {"name": "Bus Stop", "icon": "🚌", "color": "#DAA520"},
            {"name": "Shopping Mall", "icon": "🏬", "color": "#FF69B4"},
            {"name": "Bank", "icon": "🏦", "color": "#2F4F4F"},
            {"name": "Post Office", "icon": "📮", "color": "#B22222"},
            {"name": "Kindergarten", "icon": "👶", "color": "#FFB6C1"},
            {"name": "University", "icon": "🎓", "color": "#191970"},
            {"name": "Clinic", "icon": "🩺", "color": "#20B2AA"},
            {"name": "Nightlife", "icon": "🍸", "color": "#8A2BE2"},
            {"name": "Bakery", "icon": "🥖", "color": "#DEB887"},
        ]

        for cat_data in default_categories:
            from sqlalchemy import select
            existing = db.session.execute(
                select(POICategory).where(POICategory.name == cat_data["name"])
            ).scalar_one_or_none()
            if not existing:
                db.session.add(POICategory(**cat_data))

        # Seed default data sources
        default_sources = [
            {"name": "Manual Entry", "source_type": "manual", "is_active": True},
            {"name": "CSV Import", "source_type": "csv", "is_active": True},
            {"name": "URL Import", "source_type": "api", "is_active": True},
        ]

        for src_data in default_sources:
            existing = db.session.execute(
                select(DataSource).where(DataSource.name == src_data["name"])
            ).scalar_one_or_none()
            if not existing:
                db.session.add(DataSource(**src_data))

        db.session.commit()
        console.print("✅ Database seeded with default categories and data sources.", style="green")


@db_cli.command("reset")
@click.confirmation_option(prompt="⚠️  This will DROP all tables and recreate them. Continue?")
def reset_db():
    """Drop all tables, recreate, and seed."""
    app = _get_app()
    with app.app_context():
        from nestscout.extensions import db
        import nestscout.models  # noqa: F401

        db.drop_all()
        console.print("🗑️  All tables dropped.", style="yellow")

        db.create_all()
        console.print("✅ Tables recreated.", style="green")

    # Re-seed
    from nestscout.cli.db import seed_db
    seed_db.callback()
