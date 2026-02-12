"""Scoring service — personalised property scoring engine.

Implements the scoring algorithm from DesignDoc §7:
  For each Property P and Profile R:
      total = 0; weight_sum = 0
      For each ScoringRule S in R:
          raw_value = evaluate(S, P)      # 0.0–1.0
          total += raw_value × S.weight
          weight_sum += S.weight
      P.score = (total / weight_sum) × 100
"""

from datetime import datetime, timezone

from sqlalchemy import select

from nestscout.extensions import db
from nestscout.models.property import Property
from nestscout.models.search_profile import SearchProfile
from nestscout.models.scoring import ScoringRule, PropertyScore
from nestscout.models.poi import POI
from nestscout.models.associations import PropertyPOIDistance
from nestscout.utils.geo import haversine_distance


class ScoringService:
    """Personalised property scoring engine."""

    @staticmethod
    def compute_scores(profile_id: int) -> int:
        """Compute scores for all properties against a given profile.

        Returns:
            Number of properties scored.
        """
        profile = db.session.get(SearchProfile, profile_id)
        if not profile or not profile.scoring_rules:
            return 0

        properties = list(db.session.execute(select(Property)).scalars())
        count = 0

        for prop in properties:
            score, breakdown = ScoringService._score_property(prop, profile.scoring_rules)

            # Upsert the score
            existing = db.session.execute(
                select(PropertyScore).where(
                    PropertyScore.property_id == prop.id,
                    PropertyScore.profile_id == profile_id,
                )
            ).scalar_one_or_none()

            if existing:
                existing.total_score = score
                existing.breakdown = breakdown
                existing.computed_at = datetime.now(timezone.utc)
            else:
                ps = PropertyScore(
                    property_id=prop.id,
                    profile_id=profile_id,
                    total_score=score,
                    breakdown=breakdown,
                )
                db.session.add(ps)

            count += 1

        db.session.commit()
        return count

    @staticmethod
    def get_ranked_properties(profile_id: int) -> list[dict]:
        """Get properties ranked by their score for a given profile.

        Returns:
            List of property dicts with score info, sorted descending.
        """
        stmt = (
            select(PropertyScore, Property)
            .join(Property, PropertyScore.property_id == Property.id)
            .where(PropertyScore.profile_id == profile_id)
            .order_by(PropertyScore.total_score.desc())
        )

        results = []
        for score, prop in db.session.execute(stmt):
            d = prop.to_dict()
            d["score"] = score.to_dict()
            results.append(d)

        return results

    @staticmethod
    def _score_property(prop: Property, rules: list[ScoringRule]) -> tuple[float, dict]:
        """Score a single property against scoring rules.

        Returns:
            (total_score 0-100, breakdown dict)
        """
        total = 0.0
        weight_sum = 0.0
        breakdown = {}

        for rule in rules:
            raw_value = ScoringService._evaluate_rule(rule, prop)
            total += raw_value * rule.weight
            weight_sum += rule.weight
            breakdown[f"rule_{rule.id}_{rule.rule_type}"] = {
                "raw_value": round(raw_value, 3),
                "weight": rule.weight,
                "weighted": round(raw_value * rule.weight, 3),
            }

        final_score = (total / weight_sum * 100) if weight_sum > 0 else 0.0
        return round(final_score, 2), breakdown

    @staticmethod
    def _evaluate_rule(rule: ScoringRule, prop: Property) -> float:
        """Evaluate a single scoring rule against a property.

        Returns:
            A value between 0.0 and 1.0.
        """
        if rule.rule_type == "poi_proximity":
            return ScoringService._eval_poi_proximity(rule, prop)
        elif rule.rule_type == "poi_density":
            return ScoringService._eval_poi_density(rule, prop)
        elif rule.rule_type == "property_attr":
            return ScoringService._eval_property_attr(rule, prop)
        elif rule.rule_type == "walkability":
            return ScoringService._eval_walkability(rule, prop)
        else:
            return 0.0  # Unknown rule types score 0

    @staticmethod
    def _eval_poi_proximity(rule: ScoringRule, prop: Property) -> float:
        """Score = 1 - (nearest_distance / max_distance). 0 if none found."""
        if not prop.latitude or not prop.longitude or not rule.poi_category_id:
            return 0.0

        max_dist = rule.max_distance_m or 1000.0

        # Check pre-computed distances first
        stmt = (
            select(PropertyPOIDistance)
            .join(POI, PropertyPOIDistance.poi_id == POI.id)
            .where(
                PropertyPOIDistance.property_id == prop.id,
                POI.category_id == rule.poi_category_id,
            )
            .order_by(PropertyPOIDistance.distance_m)
            .limit(1)
        )
        nearest = db.session.execute(stmt).scalar_one_or_none()

        if nearest:
            if nearest.distance_m > max_dist:
                return 0.0
            return max(0.0, 1.0 - (nearest.distance_m / max_dist))

        # Fallback: compute on the fly with haversine
        pois = list(db.session.execute(
            select(POI).where(POI.category_id == rule.poi_category_id)
        ).scalars())

        if not pois:
            return 0.0

        min_dist = min(
            haversine_distance(prop.latitude, prop.longitude, p.latitude, p.longitude)
            for p in pois if p.latitude and p.longitude
        )

        if min_dist > max_dist:
            return 0.0
        return max(0.0, 1.0 - (min_dist / max_dist))

    @staticmethod
    def _eval_poi_density(rule: ScoringRule, prop: Property) -> float:
        """Score = min(count / target_count, 1.0)."""
        if not prop.latitude or not prop.longitude or not rule.poi_category_id:
            return 0.0

        params = rule.parameters or {}
        radius = rule.max_distance_m or 1000.0
        target_count = params.get("target_count", 5)

        pois = list(db.session.execute(
            select(POI).where(POI.category_id == rule.poi_category_id)
        ).scalars())

        count = sum(
            1 for p in pois
            if p.latitude and p.longitude
            and haversine_distance(prop.latitude, prop.longitude, p.latitude, p.longitude) <= radius
        )

        return min(count / target_count, 1.0)

    @staticmethod
    def _eval_property_attr(rule: ScoringRule, prop: Property) -> float:
        """Score based on how close a property attribute is to the user's ideal."""
        params = rule.parameters or {}
        attr_name = params.get("attribute")
        ideal = params.get("ideal")
        tolerance = params.get("tolerance", 0)

        if not attr_name or ideal is None:
            return 0.0

        actual = getattr(prop, attr_name, None)
        if actual is None:
            return 0.0

        try:
            actual = float(actual)
            ideal = float(ideal)
            tolerance = float(tolerance)
        except (ValueError, TypeError):
            return 0.0

        if tolerance == 0:
            return 1.0 if actual == ideal else 0.0

        diff = abs(actual - ideal)
        return max(0.0, 1.0 - (diff / tolerance))

    @staticmethod
    def _eval_walkability(rule: ScoringRule, prop: Property) -> float:
        """Composite walkability score across multiple POI categories."""
        if not prop.latitude or not prop.longitude:
            return 0.0

        params = rule.parameters or {}
        categories = params.get("categories", [])
        max_dist = rule.max_distance_m or 1000.0

        if not categories:
            return 0.0

        scores = []
        for cat_id in categories:
            pois = list(db.session.execute(
                select(POI).where(POI.category_id == cat_id)
            ).scalars())

            if not pois:
                scores.append(0.0)
                continue

            min_dist = min(
                haversine_distance(prop.latitude, prop.longitude, p.latitude, p.longitude)
                for p in pois if p.latitude and p.longitude
            )
            scores.append(max(0.0, 1.0 - (min_dist / max_dist)))

        return sum(scores) / len(scores) if scores else 0.0
