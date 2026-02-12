"""Price Prediction sub-agent — real estate valuation analysis."""

from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool, tool

from nestscout.agents.config import get_llm

# ── System Prompt ──────────────────────────────────────────────────────────────
PRICE_AGENT_SYSTEM_PROMPT = """\
You are NestScout's Real Estate Valuation Analyst — a specialist in property \
pricing, market analysis, and investment assessment.

YOUR ROLE:
You estimate fair market values for properties, identify deals and overpriced \
listings, and provide data-driven pricing insights. You help users make informed \
financial decisions about real estate.

DOMAIN EXPERTISE:
- Price per m² analysis across different cities, neighbourhoods, and property types
- Comparable sales methodology (comps): matching by location, size, type, condition
- Price signals: renovation status, floor level, orientation, building age, energy rating
- Market indicators: days on market, price reductions, listing volume trends
- Investment metrics: gross yield (rent/price), cap rate, price growth potential

CAPABILITIES:
1. Use predict_price to estimate the fair market value of a property based on its \
   characteristics and comparable listings
2. Use get_comparables to find similar recently-listed properties for price benchmarking
3. Calculate price per m² and compare against area averages
4. Flag listings >15% above predicted value as "overpriced" and >15% below as "potential deal"

RESPONSE FORMAT:
- Always state your estimated fair value as a range (±10%)
- Show the price per m² calculation
- List 2-3 comparable properties used for the estimate
- Provide a deal assessment: "Fair Price" / "Good Deal" / "Overpriced" / "Suspicious"
- For investment queries, calculate gross rental yield if rent data is available

CONSTRAINTS:
- Base estimates ONLY on comparable data from the database — never guess market prices
- Always disclose the confidence level: High (5+ comps), Medium (3-4), Low (1-2)
- If insufficient data exists, clearly state the estimate is unreliable
- Never provide financial advice — only data analysis
- Prices must always include the currency
"""


# ── Tools ──────────────────────────────────────────────────────────────────────
@tool
def predict_price(
    city: str,
    area_m2: float,
    bedrooms: int = 0,
    operation: str = "sale",
) -> str:
    """Estimate fair market price based on comparable properties.

    Args:
        city: City where the property is located.
        area_m2: Property area in square metres.
        bedrooms: Number of bedrooms.
        operation: 'sale' or 'rent'.
    """
    from nestscout.services.property_service import PropertyService
    import json

    # Find comparable properties
    kwargs = {"city": city, "operation": operation, "per_page": 50}
    if bedrooms > 0:
        kwargs["min_bedrooms"] = max(bedrooms - 1, 0)
        kwargs["max_bedrooms"] = bedrooms + 1
    if area_m2 > 0:
        kwargs["min_area"] = area_m2 * 0.7
        kwargs["max_area"] = area_m2 * 1.3

    result = PropertyService.list_properties(**kwargs)
    items = result["items"]

    if not items:
        return json.dumps({"error": "No comparable properties found", "confidence": "none"})

    prices_per_m2 = [
        p["price"] / p["area_m2"]
        for p in items
        if p.get("price") and p.get("area_m2") and p["area_m2"] > 0
    ]

    if not prices_per_m2:
        return json.dumps({"error": "No properties with price and area data", "confidence": "none"})

    avg_price_m2 = sum(prices_per_m2) / len(prices_per_m2)
    estimated_price = avg_price_m2 * area_m2

    confidence = "high" if len(prices_per_m2) >= 5 else "medium" if len(prices_per_m2) >= 3 else "low"

    return json.dumps({
        "estimated_price": round(estimated_price, 2),
        "price_range_low": round(estimated_price * 0.9, 2),
        "price_range_high": round(estimated_price * 1.1, 2),
        "avg_price_per_m2": round(avg_price_m2, 2),
        "comparable_count": len(prices_per_m2),
        "confidence": confidence,
    }, indent=2)


@tool
def get_comparables(
    city: str,
    area_m2: float,
    bedrooms: int = 0,
    operation: str = "sale",
    limit: int = 5,
) -> str:
    """Find comparable properties for price benchmarking.

    Args:
        city: City to search in.
        area_m2: Target area for comparison.
        bedrooms: Target bedroom count.
        operation: 'sale' or 'rent'.
        limit: Maximum number of comparables to return.
    """
    from nestscout.services.property_service import PropertyService
    import json

    kwargs = {"city": city, "operation": operation, "per_page": limit}
    if bedrooms > 0:
        kwargs["min_bedrooms"] = max(bedrooms - 1, 0)
        kwargs["max_bedrooms"] = bedrooms + 1
    if area_m2 > 0:
        kwargs["min_area"] = area_m2 * 0.7
        kwargs["max_area"] = area_m2 * 1.3

    result = PropertyService.list_properties(**kwargs)
    comps = []
    for p in result["items"][:limit]:
        comp = {
            "id": p["id"],
            "title": p["title"],
            "price": p["price"],
            "area_m2": p["area_m2"],
            "bedrooms": p["bedrooms"],
            "city": p["city"],
            "address": p["address"],
        }
        if p.get("price") and p.get("area_m2") and p["area_m2"] > 0:
            comp["price_per_m2"] = round(p["price"] / p["area_m2"], 2)
        comps.append(comp)

    return json.dumps(comps, indent=2, default=str)


# ── Agent Creation ─────────────────────────────────────────────────────────────
class PriceAgentInput(BaseModel):
    """Input schema for the Price Prediction sub-agent."""
    natural_language_query: str = Field(
        description="The user's question about property pricing, valuation, or deals."
    )


def create_price_agent_tool() -> Tool:
    """Create the Price Prediction sub-agent wrapped as a LangChain Tool."""
    llm = get_llm(temperature=0)
    tools = [predict_price, get_comparables]

    prompt = ChatPromptTemplate.from_messages([
        ("system", PRICE_AGENT_SYSTEM_PROMPT),
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
            return f"Price analysis failed: {str(e)}"

    return Tool(
        name="price_analyst",
        func=run_agent,
        description=(
            "Use this tool when the user asks about property prices, valuations, "
            "fair market value, deals, or investment potential. "
            "Handles queries like 'is this a good price for a 80m² flat in Barcelona' "
            "or 'what's the average price per m² in Madrid'."
        ),
        args_schema=PriceAgentInput,
    )
