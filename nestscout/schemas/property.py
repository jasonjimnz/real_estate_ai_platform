"""Property schemas — validation and serialisation."""

from marshmallow import Schema, fields, validate


class PropertyCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=500))
    description = fields.Str()
    price = fields.Float()
    currency = fields.Str(validate=validate.Length(max=3), load_default="EUR")
    operation = fields.Str(validate=validate.OneOf(["sale", "rent"]), load_default="sale")
    bedrooms = fields.Int()
    bathrooms = fields.Int()
    area_m2 = fields.Float()
    address = fields.Str()
    city = fields.Str()
    postal_code = fields.Str()
    latitude = fields.Float()
    longitude = fields.Float()
    external_id = fields.Str()
    raw_metadata = fields.Dict()
    data_source_id = fields.Int()


class PropertyBulkSchema(Schema):
    """Validates a list of properties for bulk import."""
    properties = fields.List(fields.Nested(PropertyCreateSchema), required=True)


class PropertyFilterSchema(Schema):
    """Query string filters for property listing."""
    city = fields.Str()
    operation = fields.Str(validate=validate.OneOf(["sale", "rent"]))
    min_price = fields.Float()
    max_price = fields.Float()
    min_bedrooms = fields.Int()
    max_bedrooms = fields.Int()
    min_area = fields.Float()
    max_area = fields.Float()
    page = fields.Int(load_default=1)
    per_page = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))
