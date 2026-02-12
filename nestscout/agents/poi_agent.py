"""POI / Area sub-agent — neighbourhood expertise and location intelligence."""

from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool, tool

from nestscout.agents.config import get_llm

# ── System Prompt ──────────────────────────────────────────────────────────────
POI_AGENT_SYSTEM_PROMPT = """\
You are NestScout's Neighbourhood & Location Intelligence Expert — a specialist \
in urban geography, local amenities, and area characterisation for real estate decisions.

YOUR ROLE:
You answer all questions about Points of Interest (POIs), nearby amenities, \
walkability, neighbourhood character, and area quality. You help users understand \
what it's actually like to live in a specific location.

DOMAIN EXPERTISE:
- POI categories: cafés, restaurants, supermarkets, schools, kindergartens, \
  hospitals, clinics, pharmacies, gyms, parks, public transport (metro, bus, tram), \
  shopping malls, banks, post offices, nightlife venues
- Distance interpretation: <300m = "steps away", 300-500m = "short walk", \
  500-1000m = "walkable", 1-2km = "nearby", >2km = "requires transport"
- Walking speed reference: ~5 km/h (12 min/km)

CAPABILITIES:
1. Use search_pois to find amenities near any coordinates or property
2. Use get_area_stats to summarise neighbourhood character
3. Calculate and interpret walkability scores
4. Compare neighbourhoods for liveability
5. Identify area strengths and gaps (e.g., "great for families but no nightlife")

RESPONSE FORMAT:
- Organise POIs by category when listing nearby amenities
- Always include distances in metres AND estimated walking time
- Provide a brief neighbourhood characterisation (1-2 sentences)
- When comparing areas, use a structured comparison table
- Rate walkability: Excellent (90+), Good (70-89), Fair (50-69), Poor (<50)

CONSTRAINTS:
- Only report POIs returned by your tools — never invent locations
- Distances must come from actual calculations, not estimates
- If asked about an area with no data, clearly state data is unavailable
- Always clarify the search radius used
"""


# ── Tools ──────────────────────────────────────────────────────────────────────
@tool
def search_pois(
    latitude: float,
    longitude: float,
    radius_m: float = 1000.0,
    category_id: int = 0,
) -> str:
    """Search for Points of Interest near a specific location.

    Args:
        latitude: Latitude of the center point.
        longitude: Longitude of the center point.
        radius_m: Search radius in metres (default 1000).
        category_id: Filter by category ID (0 = all categories).
    """
    from nestscout.services.poi_service import POIService
    import json

    cat_id = category_id if category_id > 0 else None
    results = POIService.find_nearby(latitude, longitude, radius_m=radius_m, category_id=cat_id)
    return json.dumps(results[:20], indent=2, default=str)  # Limit to 20 results


@tool
def get_area_stats(latitude: float, longitude: float, radius_m: float = 1000.0) -> str:
    """Get a statistical summary of POIs around a location.

    Returns category counts and average distances for area characterisation.

    Args:
        latitude: Latitude of the center point.
        longitude: Longitude of the center point.
        radius_m: Analysis radius in metres.
    """
    from nestscout.services.poi_service import POIService
    import json

    results = POIService.find_nearby(latitude, longitude, radius_m=radius_m)

    # Aggregate by category
    stats: dict = {}
    for poi in results:
        cat = poi.get("category_name", "Unknown")
        if cat not in stats:
            stats[cat] = {"count": 0, "distances": [], "avg_distance": 0}
        stats[cat]["count"] += 1
        stats[cat]["distances"].append(poi["distance_m"])

    for cat, data in stats.items():
        data["avg_distance"] = round(sum(data["distances"]) / len(data["distances"]), 1)
        data["nearest"] = round(min(data["distances"]), 1)
        del data["distances"]

    summary = {
        "center": {"lat": latitude, "lng": longitude},
        "radius_m": radius_m,
        "total_pois": len(results),
        "categories": stats,
    }
    return json.dumps(summary, indent=2, default=str)


# ── Agent Creation ─────────────────────────────────────────────────────────────
class POIAgentInput(BaseModel):
    """Input schema for the POI/Area sub-agent."""
    natural_language_query: str = Field(
        description="The user's question about a neighbourhood, nearby amenities, or area quality."
    )


def create_poi_agent_tool() -> Tool:
    """Create the POI/Area sub-agent wrapped as a LangChain Tool."""
    llm = get_llm(temperature=0.1)
    tools = [search_pois, get_area_stats]

    prompt = ChatPromptTemplate.from_messages([
        ("system", POI_AGENT_SYSTEM_PROMPT),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=5)

    def run_agent(natural_language_query: str) -> str:
        try:
            result = executor.invoke({"input": natural_language_query})
            return result["output"]
        except Exception as e:
            return f"POI/Area analysis failed: {str(e)}"

    return Tool(
        name="neighbourhood_expert",
        func=run_agent,
        description=(
            "Use this tool when the user asks about neighbourhoods, nearby amenities, "
            "walkability, area character, or what services are near a property. "
            "Handles queries like 'what schools are near this property' or "
            "'is this area good for families'."
        ),
        args_schema=POIAgentInput,
    )
