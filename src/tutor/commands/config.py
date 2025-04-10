import click
import sys
from tutor.utils.config import get_config


@click.command()
@click.option("--deck", "-d", help="Set the default deck for flashcards")
@click.option(
    "--language", "-l", help="Set the default language (mandarin or cantonese)"
)
@click.option(
    "--learner-level",
    "--level",
    "-v",
    help="Set the learner level (e.g., beginner, intermediate, advanced)",
)
def config(deck: str = None, language: str = None, learner_level: str = None) -> None:
    """View or set configuration options.

    Use options to specify what to configure:
    --deck: Set the default deck for flashcards
    --language: Set the default language (mandarin or cantonese)
    --learner-level: Set the learner level (beginner, intermediate, advanced, etc.)

    If no options are provided, shows current configuration.
    """
    config_obj = get_config()
    changes_made = False

    if deck:
        config_obj.default_deck = deck
        click.echo(f"Default deck set to: {deck}")
        changes_made = True

    if language:
        config_obj.default_language = language
        click.echo(f"Default language set to: {language}")
        changes_made = True

    if learner_level:
        config_obj.learner_level = learner_level
        click.echo(f"Learner level set to: {learner_level}")
        changes_made = True

    if not changes_made:
        try:
            # Display current configuration
            click.echo(f"Current default deck: {config_obj.default_deck}")
            click.echo(f"Current default language: {config_obj.default_language}")
            click.echo(f"Current learner level: {config_obj.learner_level}")
        except ValueError as e:
            click.echo(str(e), err=True)
            click.echo("Use 'config DECK' to set a default deck")
            sys.exit(1)
