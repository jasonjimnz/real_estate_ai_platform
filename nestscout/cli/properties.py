"""Property CLI commands — list, add, bulk-import."""

import click
from rich.console import Console
from rich.table import Table

console = Console()


def _get_app():
    from nestscout import create_app
    return create_app()


@click.group("properties")
def properties_cli():
    """Property management commands."""
    pass


@properties_cli.command("list")
@click.option("--city", help="Filter by city")
@click.option("--operation", type=click.Choice(["sale", "rent"]), help="Filter by operation")
@click.option("--min-price", type=float, help="Minimum price")
@click.option("--max-price", type=float, help="Maximum price")
@click.option("--limit", default=20, type=int, help="Number of results")
def list_properties(city, operation, min_price, max_price, limit):
    """List properties with optional filters."""
    app = _get_app()
    with app.app_context():
        from nestscout.services.property_service import PropertyService

        kwargs = {"per_page": limit}
        if city:
            kwargs["city"] = city
        if operation:
            kwargs["operation"] = operation
        if min_price:
            kwargs["min_price"] = min_price
        if max_price:
            kwargs["max_price"] = max_price

        result = PropertyService.list_properties(**kwargs)

        if not result["items"]:
            console.print("No properties found.", style="yellow")
            return

        table = Table(title=f"Properties ({result['total']} total)")
        table.add_column("ID", style="cyan")
        table.add_column("Title", max_width=40)
        table.add_column("Price", style="green", justify="right")
        table.add_column("Op", style="magenta")
        table.add_column("Beds")
        table.add_column("Area m²", justify="right")
        table.add_column("City")

        for p in result["items"]:
            price_str = f"{p['price']:,.0f} {p.get('currency', 'EUR')}" if p.get("price") else "-"
            table.add_row(
                str(p["id"]),
                p["title"][:40],
                price_str,
                p.get("operation", "-"),
                str(p.get("bedrooms", "-")),
                str(p.get("area_m2", "-")),
                p.get("city", "-"),
            )

        console.print(table)


@properties_cli.command("add")
@click.option("--title", prompt="Title", help="Property title")
@click.option("--price", type=float, prompt="Price", help="Listing price")
@click.option("--currency", default="EUR", help="Currency (default EUR)")
@click.option("--operation", type=click.Choice(["sale", "rent"]), default="sale", prompt="Operation")
@click.option("--bedrooms", type=int, prompt="Bedrooms", help="Number of bedrooms")
@click.option("--bathrooms", type=int, prompt="Bathrooms", help="Number of bathrooms")
@click.option("--area", "area_m2", type=float, prompt="Area (m²)", help="Area in m²")
@click.option("--address", prompt="Address", help="Full address")
@click.option("--city", prompt="City", help="City name")
@click.option("--lat", "latitude", type=float, default=None, help="Latitude")
@click.option("--lng", "longitude", type=float, default=None, help="Longitude")
def add_property(title, price, currency, operation, bedrooms, bathrooms, area_m2, address, city, latitude, longitude):
    """Add a single property interactively."""
    app = _get_app()
    with app.app_context():
        from nestscout.services.property_service import PropertyService

        data = {
            "title": title, "price": price, "currency": currency,
            "operation": operation, "bedrooms": bedrooms, "bathrooms": bathrooms,
            "area_m2": area_m2, "address": address, "city": city,
        }
        if latitude is not None:
            data["latitude"] = latitude
        if longitude is not None:
            data["longitude"] = longitude

        prop = PropertyService.create(data)
        console.print(f"✅ Property created with ID {prop.id}: {prop.title}", style="green")


@properties_cli.command("bulk-import")
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--city", help="Default city for all records")
@click.option("--currency", default="EUR", help="Default currency")
@click.option("--operation", type=click.Choice(["sale", "rent"]), default="sale", help="Default operation")
def bulk_import_properties(filepath, city, currency, operation):
    """Bulk import properties from a CSV or Excel file.

    FILEPATH: Path to the CSV or XLSX file.
    """
    app = _get_app()
    with app.app_context():
        from nestscout.services.import_service import ImportService

        defaults = {"currency": currency, "operation": operation}
        if city:
            defaults["city"] = city

        console.print(f"📥 Importing properties from: {filepath}", style="blue")

        result = ImportService.import_properties_csv(filepath, defaults=defaults)

        if result["success"]:
            console.print(
                f"✅ Import complete: {result['created']} created, "
                f"{result['skipped']} skipped (out of {result['total_parsed']} parsed)",
                style="green",
            )
        else:
            console.print(f"❌ Import failed: {result.get('error', 'Unknown error')}", style="red")
