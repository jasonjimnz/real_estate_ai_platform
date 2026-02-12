"""Profile and scoring rule schemas."""

from marshmallow import Schema, fields, validate


class ScoringRuleSchema(Schema):
    rule_type = fields.Str(
        required=True,
        validate=validate.OneOf([
            "poi_proximity", "poi_density", "property_attr",
            "walkability", "ai_sentiment", "price_value",
        ]),
    )
    poi_category_id = fields.Int()
    max_distance_m = fields.Float()
    weight = fields.Float(required=True, validate=validate.Range(min=0.0, max=1.0))
    parameters = fields.Dict()


class ProfileCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    filters = fields.Dict()


class ProfileUpdateRulesSchema(Schema):
    rules = fields.List(fields.Nested(ScoringRuleSchema), required=True)
