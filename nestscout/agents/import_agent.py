"""Import sub-agent — AI-powered data extraction from text and URLs."""

from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool, tool

from nestscout.agents.config import get_llm

# ── System Prompt ──────────────────────────────────────────────────────────────
IMPORT_AGENT_SYSTEM_PROMPT = """\
You are NestScout's Real Estate Data Extraction Specialist — an expert at \
parsing, structuring, and normalising property listing data from any text format.

YOUR ROLE:
You extract structured property information from unstructured text, pasted \
listing descriptions, or scraped webpage content. You are the bridge between \
messy real-world data and the platform's clean database schema.

EXTRACTION FIELDS (in order of priority):
1. title — The listing headline or a generated summary (REQUIRED)
2. price — Numeric value, strip currency symbols and thousands separators
3. currency — ISO 4217 code (EUR, USD, GBP, etc.) — default EUR if ambiguous
4. operation — 'sale' or 'rent' — infer from context ("monthly", "per month" → rent)
5. bedrooms — Integer count (interpret "studio" as 0, "T2" as 2, etc.)
6. bathrooms — Integer count
7. area_m2 — Area in square metres (convert from ft² if needed: × 0.0929)
8. address — Full street address if available
9. city — City name
10. postal_code — Postal/ZIP code
11. description — Full listing description text

PARSING RULES:
- PRICES: Remove dots/commas used as thousands separators. "250.000 €" → 250000. \
  "€1,200/month" → 1200, operation=rent
- AREA: "80 m²" → 80. "850 sq ft" → 78.97. "80m2" → 80
- BEDROOMS: "3 hab" → 3. "T3" → 3. "Studio" → 0. "3 bed" → 3
- ADDRESSES: Extract the most complete address possible. If fragmented, \
  concatenate street + number + city
- MULTI-LISTING: If the text contains MULTIPLE properties, extract each separately

RESPONSE FORMAT:
Return a JSON object (or array for multiple listings) with the extracted fields. \
Use null for fields you cannot confidently extract. Never fabricate data.

Example output:
{
  "title": "Sunny 3-bed apartment in Eixample",
  "price": 285000,
  "currency": "EUR",
  "operation": "sale",
  "bedrooms": 3,
  "bathrooms": 2,
  "area_m2": 95,
  "address": "Carrer de Mallorca 234",
  "city": "Barcelona",
  "postal_code": "08036",
  "description": "Beautiful renovated apartment..."
}

CONSTRAINTS:
- NEVER invent data points — only extract what's explicitly in the text
- If a field is ambiguous, use null instead of guessing
- Always validate numeric fields are reasonable (price > 0, area > 0)
- Flag if listing appears to be a scam (unrealistically low price)
"""


# ── Tools ──────────────────────────────────────────────────────────────────────
@tool
def parse_listing_text(raw_text: str) -> str:
    """Parse raw text and extract structured property data.

    This tool uses the LLM's understanding to extract fields from
    unstructured listing text.

    Args:
        raw_text: The raw listing text to parse.
    """
    # The extraction happens via the agent's LLM reasoning — this tool
    # simply returns the text for the agent to process
    return f"Please extract property data from this text:\n\n{raw_text}"


@tool
def create_property(property_json: str) -> str:
    """Save an extracted property to the database.

    Args:
        property_json: JSON string with property fields.
    """
    from nestscout.services.property_service import PropertyService
    import json

    try:
        data = json.loads(property_json)
        prop = PropertyService.create(data)
        return f"Property created successfully with ID {prop.id}: {prop.title}"
    except Exception as e:
        return f"Failed to create property: {str(e)}"


# ── Agent Creation ─────────────────────────────────────────────────────────────
class ImportAgentInput(BaseModel):
    """Input schema for the Import sub-agent."""
    raw_listing_text: str = Field(
        description="Raw property listing text to parse and structure."
    )


def create_import_agent_tool() -> Tool:
    """Create the Import sub-agent wrapped as a LangChain Tool."""
    llm = get_llm(temperature=0)
    tools = [parse_listing_text, create_property]

    prompt = ChatPromptTemplate.from_messages([
        ("system", IMPORT_AGENT_SYSTEM_PROMPT),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=5)

    def run_agent(raw_listing_text: str) -> str:
        try:
            result = executor.invoke({"input": raw_listing_text})
            return result["output"]
        except Exception as e:
            return f"Import extraction failed: {str(e)}"

    return Tool(
        name="import_specialist",
        func=run_agent,
        description=(
            "Use this tool when the user pastes raw listing text or wants to import "
            "a property from unstructured data. Extracts title, price, bedrooms, area, "
            "address, and other fields from any text format."
        ),
        args_schema=ImportAgentInput,
    )
