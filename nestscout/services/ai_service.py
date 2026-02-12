"""AI service — wraps the LangChain supervisor agent for Flask integration."""

from typing import Any


class AIService:
    """Interface between Flask endpoints and the LangChain agent system."""

    @staticmethod
    def chat(message: str, user_id: int | None = None, context: dict | None = None) -> str:
        """Send a message to the AI supervisor and get a response.

        Args:
            message: User's natural-language query.
            user_id: Optional user ID for personalised context.
            context: Optional additional context (current property, profile, etc.).

        Returns:
            The AI agent's response string.
        """
        try:
            from nestscout.agents.supervisor import create_supervisor
            supervisor = create_supervisor()
            result = supervisor.invoke({"input": message})
            return result.get("output", "I couldn't process that request.")
        except ImportError:
            return (
                "AI agent not available. Ensure LangChain dependencies are installed "
                "and LLM_BASE_URL is configured in .env"
            )
        except Exception as e:
            return f"AI agent error: {str(e)}"

    @staticmethod
    def search(query: str) -> list[dict[str, Any]]:
        """Perform a natural-language property search.

        Returns:
            List of matching property dicts.
        """
        # For now, delegates to the AI chat with a search-specific prompt
        response = AIService.chat(f"Search for properties matching: {query}")
        return [{"response": response}]
