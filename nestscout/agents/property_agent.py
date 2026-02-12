"""Property Search sub-agent — converts NL queries to structured property search."""

from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool, tool

from nestscout.agents.config import get_llm

# ── System Prompt ──────────────────────────────────────────────────────────────
PROPERTY_SEARCH_SYSTEM_PROMPT = """\
You are NestScout's Property Search Specialist — a highly trained real estate \
search expert embedded in an AI-powered property intelligence platform.

YOUR ROLE:
You translate natural-language property queries into precise structured searches \
and return relevant listings to users. You are the primary interface between \
human intent and the property database.

CAPABILITIES:
1. Parse complex search criteria from conversational queries
2. Understand real estate terminology across markets (sale/rent, bedrooms, \
   area in m², price ranges, locations)
3. Interpret relative terms ("affordable", "spacious", "central") based on \
   market context
4. Use the search_properties tool to query the database with structured filters
5. Use the get_property_details tool to retrieve full details for a specific listing

RESPONSE FORMAT:
- Always return structured information: address, price, bedrooms, area, and any \
  relevant scores
- When multiple results match, present them as a numbered list ranked by relevance
- Include price per m² when both price and area are available
- Flag any properties that seem unusually priced for their characteristics
- If no results match, suggest relaxing the most restrictive filter

CONSTRAINTS:
- Never fabricate property data — only return results from the tools
- If a query is ambiguous, ask ONE clarifying question before searching
- Always specify the currency when mentioning prices
- Convert user terms to filter parameters: "cheap" → lower price range, \
  "big" → higher area_m2, "family" → 3+ bedrooms
"""


# ── Tools ──────────────────────────────────────────────────────────────────────
@tool
def search_properties(
    city: str = "",
    operation: str = "sale",
    min_price: float = 0,
    max_price: float = 0,
    min_bedrooms: int = 0,
    max_bedrooms: int = 0,
    min_area: float = 0,
    max_area: float = 0,
) -> str:
    """Search properties in the database with structured filters.

    Args:
        city: City name to filter by (partial match).
        operation: 'sale' or 'rent'.
        min_price: Minimum price filter.
        max_price: Maximum price filter (0 = no limit).
        min_bedrooms: Minimum number of bedrooms.
        max_bedrooms: Maximum number of bedrooms (0 = no limit).
        min_area: Minimum area in m².
        max_area: Maximum area in m² (0 = no limit).
    """
    from nestscout.services.property_service import PropertyService
    import json

    kwargs = {"page": 1, "per_page": 10}
    if city:
        kwargs["city"] = city
    if operation:
        kwargs["operation"] = operation
    if min_price > 0:
        kwargs["min_price"] = min_price
    if max_price > 0:
        kwargs["max_price"] = max_price
    if min_bedrooms > 0:
        kwargs["min_bedrooms"] = min_bedrooms
    if max_bedrooms > 0:
        kwargs["max_bedrooms"] = max_bedrooms
    if min_area > 0:
        kwargs["min_area"] = min_area
    if max_area > 0:
        kwargs["max_area"] = max_area

    result = PropertyService.list_properties(**kwargs)
    return json.dumps(result, indent=2, default=str)


@tool
def get_property_details(property_id: int) -> str:
    """Get full details of a specific property by its ID.

    Args:
        property_id: The unique property identifier.
    """
    from nestscout.services.property_service import PropertyService
    import json

    prop = PropertyService.get_by_id(property_id)
    if not prop:
        return f"Property with ID {property_id} not found."
    return json.dumps(prop.to_dict(include_images=True), indent=2, default=str)


# ── Agent Creation ─────────────────────────────────────────────────────────────
class PropertySearchInput(BaseModel):
    """Input schema for the Property Search sub-agent."""
    natural_language_query: str = Field(
        description="The user's property search query in natural language."
    )


def create_property_search_tool() -> Tool:
    """Create the Property Search sub-agent wrapped as a LangChain Tool."""
    llm = get_llm(temperature=0)
    tools = [search_properties, get_property_details]

    prompt = ChatPromptTemplate.from_messages([
        ("system", PROPERTY_SEARCH_SYSTEM_PROMPT),
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
            return f"Property search failed: {str(e)}"

    return Tool(
        name="property_search_specialist",
        func=run_agent,
        description=(
            "Use this tool when the user wants to find, search, or browse properties. "
            "Handles queries like 'find apartments in Madrid under 300k' or "
            "'show me 3-bedroom houses for rent'."
        ),
        args_schema=PropertySearchInput,
    )
