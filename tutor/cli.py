import click
from typing import Optional
from dotenv import load_dotenv

from tutor.commands.generate_topics import (
    generate_topics_prompt_inner,
    select_conversation_topic_inner,
)
from tutor.commands.generate_flashcard_from_word import (
    generate_flashcard_from_word_inner,
)
from tutor.commands.regenerate_flashcard import (
    regenerate_flashcard_inner,
)
from tutor.commands.list_lesser_known_cards import (
    list_lesser_known_cards_inner,
)
from tutor.llm_flashcards import GPT_3_5_TURBO, GPT_4, GPT_4o
from tutor.utils.config import get_config

from tutor.cli_global_state import set_debug, set_model, set_skip_confirm

load_dotenv()


@click.group()
@click.option(
    "--model",
    type=click.Choice([GPT_3_5_TURBO, GPT_4, GPT_4o]),
    default=GPT_4o,
    help="Customize the OpenAI model used",
)
@click.option("--debug/--no-debug", default=False, help="Turn on extra debug logging")
@click.option(
    "--skip-confirm", type=bool, default=False, help="Skip confirmation for commands"
)
def cli(model: str, debug: bool, skip_confirm: bool) -> None:
    """chinese-tutor tool"""
    set_model(model)
    set_debug(debug)
    set_skip_confirm(skip_confirm)


@cli.command()
@click.option(
    "--conversation-topics-path",
    type=str,
    help="Path to data file with past topics",
    default="data/conversation_topics.yaml",
)
@click.option(
    "--num-topics",
    type=int,
    help="Number of new topics to generate",
    default=10,
)
def generate_topics_prompt(conversation_topics_path: str, num_topics: int) -> None:
    """Prints a prompt to pass to ChatGPT to get new conversation topics."""
    click.echo(generate_topics_prompt_inner(conversation_topics_path, num_topics))


@cli.command()
@click.option(
    "--conversation-topics-path",
    type=str,
    help="Path to data file with past topics",
    default="data/conversation_topics.yaml",
)
def select_conversation_topic(conversation_topics_path: str):
    """Selects a random conversation topic from a file on disk."""
    click.echo(select_conversation_topic_inner(conversation_topics_path))


@cli.command()
@click.argument("word", type=str)
@click.option("--deck", type=str, default=None)
def generate_flashcard_from_word(deck: str, word: str):
    """Add a new Anki flashcard for a specific WORD to DECK."""
    deck = deck or get_config().default_deck
    click.echo(generate_flashcard_from_word_inner(deck, word))


# Shortcut for the most common action.
cli.add_command(generate_flashcard_from_word, name="g")


@cli.command()
@click.argument("word", type=str)
def regenerate_flashcard(word: str):
    """Regenerate Anki flashcard for a specific WORD."""
    click.echo(regenerate_flashcard_inner(word))


# Shortcut for the next-most common action.
cli.add_command(regenerate_flashcard, name="rg")


@cli.command()
@click.option("--deck", type=str, default=None)
@click.option("--count", type=int, default=5)
def list_lesser_known_cards(deck: str, count: int):
    """Regenerate Anki flashcard for a specific WORD."""
    deck = deck or get_config().default_deck
    click.echo(list_lesser_known_cards_inner(deck, count))


@cli.command()
@click.argument("deck", required=False)
def config(deck: Optional[str]) -> None:
    """View or set the default deck configuration.

    If DECK is provided, sets the default deck.
    If no DECK is provided, shows current configuration.
    """
    if deck:
        get_config().default_deck = deck
        click.echo(f"Default deck set to: {deck}")
    else:
        try:
            current_deck = get_config().default_deck
            click.echo(f"Current default deck: {current_deck}")
        except ValueError as e:
            click.echo(str(e), err=True)
            click.echo("Use 'config DECK' to set a default deck")
            exit(1)
