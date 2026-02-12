"""AI CLI commands — interactive chat and one-shot search."""

import click
from rich.console import Console
from rich.markdown import Markdown

console = Console()


def _get_app():
    from nestscout import create_app
    return create_app()


@click.group("ai")
def ai_cli():
    """AI assistant commands."""
    pass


@ai_cli.command("chat")
def chat_interactive():
    """Start an interactive AI chat session.

    Type 'quit' or 'exit' to end the session.
    """
    app = _get_app()
    with app.app_context():
        from nestscout.services.ai_service import AIService

        console.print("🤖 NestScout AI Assistant", style="bold blue")
        console.print("Type your question about properties, neighbourhoods, or prices.")
        console.print("Type 'quit' or 'exit' to end.\n", style="dim")

        while True:
            try:
                message = click.prompt("You", prompt_suffix=" > ")
            except (click.Abort, EOFError):
                break

            if message.lower().strip() in ("quit", "exit", "q"):
                console.print("\n👋 Goodbye!", style="blue")
                break

            if not message.strip():
                continue

            console.print("⏳ Thinking...", style="dim")
            response = AIService.chat(message)
            console.print()
            console.print(Markdown(f"**🤖 AI:** {response}"))
            console.print()


@ai_cli.command("search")
@click.argument("query")
def ai_search(query):
    """One-shot natural-language property search.

    QUERY: Your search query in natural language.
    """
    app = _get_app()
    with app.app_context():
        from nestscout.services.ai_service import AIService

        console.print(f"🔍 Searching: {query}", style="blue")
        results = AIService.search(query)

        for r in results:
            if "response" in r:
                console.print(Markdown(r["response"]))
            else:
                console.print(r)
