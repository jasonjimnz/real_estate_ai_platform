"""POI schemas — validation for POIs and categories."""

from marshmallow import Schema, fields, validate


class POICategorySchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    icon = fields.Str()
    color = fields.Str(validate=validate.Length(max=7))


class POICreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    category_id = fields.Int(required=True)
    latitude = fields.Float()
    longitude = fields.Float()
    address = fields.Str()
    rating = fields.Float()
    metadata_extra = fields.Dict()


class POIBulkSchema(Schema):
    """Validates a list of POIs/businesses for bulk import."""
    pois = fields.List(fields.Nested(POICreateSchema), required=True)
