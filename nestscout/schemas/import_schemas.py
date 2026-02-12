"""Import schemas — CSV upload and URL import validation."""

from marshmallow import Schema, fields, validate


class CSVImportSchema(Schema):
    """Metadata for a CSV/Excel bulk import."""
    source_name = fields.Str(load_default="csv_import")
    operation = fields.Str(validate=validate.OneOf(["sale", "rent"]), load_default="sale")
    currency = fields.Str(load_default="EUR")
    city = fields.Str()


class URLImportSchema(Schema):
    """URL-based import request."""
    url = fields.Url(required=True)
    source_name = fields.Str(load_default="url_import")
