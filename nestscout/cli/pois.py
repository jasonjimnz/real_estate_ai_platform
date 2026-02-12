"""POI / Business CLI commands — list, add, bulk-import."""

import click
from rich.console import Console
from rich.table import Table

console = Console()


def _get_app():
    from nestscout import create_app
    return create_app()


@click.group("pois")
def pois_cli():
    """POI / business management commands."""
    pass


@pois_cli.command("list")
@click.option("--category", type=int, help="Filter by category ID")
@click.option("--limit", default=50, type=int, help="Number of results")
def list_pois(category, limit):
    """List POIs/businesses."""
    app = _get_app()
    with app.app_context():
        from nestscout.services.poi_service import POIService

        result = POIService.list_pois(category_id=category, per_page=limit)

        if not result["items"]:
            console.print("No POIs found.", style="yellow")
            return

        table = Table(title=f"Points of Interest ({result['total']} total)")
        table.add_column("ID", style="cyan")
        table.add_column("Name", max_width=35)
        table.add_column("Category", style="magenta")
        table.add_column("Rating", justify="right")
        table.add_column("Address", max_width=30)

        for p in result["items"]:
            table.add_row(
                str(p["id"]),
                p["name"],
                p.get("category_name", "-"),
                f"{p['rating']:.1f}" if p.get("rating") else "-",
                p.get("address", "-") or "-",
            )

        console.print(table)


@pois_cli.command("categories")
def list_categories():
    """List all POI categories."""
    app = _get_app()
    with app.app_context():
        from nestscout.services.poi_service import POIService
        cats = POIService.list_categories()

        if not cats:
            console.print("No categories found. Run 'nestscout db seed' first.", style="yellow")
            return

        table = Table(title="POI Categories")
        table.add_column("ID", style="cyan")
        table.add_column("Icon")
        table.add_column("Name", style="green")
        table.add_column("Color")

        for c in cats:
            table.add_row(str(c.id), c.icon or "-", c.name, c.color or "-")

        console.print(table)


@pois_cli.command("add")
@click.option("--name", prompt="Business/POI name", help="Name of the business or POI")
@click.option("--category", "category_name", prompt="Category", help="Category name (auto-created if new)")
@click.option("--address", prompt="Address", help="Full address")
@click.option("--lat", "latitude", type=float, default=None, help="Latitude")
@click.option("--lng", "longitude", type=float, default=None, help="Longitude")
@click.option("--rating", type=float, default=None, help="Rating (0-5)")
def add_poi(name, category_name, address, latitude, longitude, rating):
    """Add a single POI/business interactively."""
    app = _get_app()
    with app.app_context():
        from nestscout.services.poi_service import POIService

        # Resolve category
        cat = POIService.get_or_create_category(category_name)

        data = {
            "name": name,
            "category_id": cat.id,
            "address": address,
        }
        if latitude is not None:
            data["latitude"] = latitude
        if longitude is not None:
            data["longitude"] = longitude
        if rating is not None:
            data["rating"] = rating

        poi = POIService.create(data)
        console.print(
            f"✅ POI created with ID {poi.id}: {poi.name} [{cat.name}]",
            style="green",
        )


@pois_cli.command("bulk-import")
@click.argument("filepath", type=click.Path(exists=True))
def bulk_import_pois(filepath):
    """Bulk import POIs/businesses from a CSV or Excel file.

    FILEPATH: Path to the CSV or XLSX file.

    Expected columns: name, category, latitude, longitude, address, rating
    """
    app = _get_app()
    with app.app_context():
        from nestscout.services.import_service import ImportService

        console.print(f"📥 Importing POIs/businesses from: {filepath}", style="blue")

        result = ImportService.import_pois_csv(filepath)

        if result["success"]:
            console.print(
                f"✅ Import complete: {result['created']} created, "
                f"{result['skipped']} skipped (out of {result['total_parsed']} parsed)",
                style="green",
            )
        else:
            console.print(f"❌ Import failed: {result.get('error', 'Unknown error')}", style="red")
