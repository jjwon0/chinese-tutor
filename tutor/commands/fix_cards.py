import click
from typing import Optional
from tutor.llm.models import ChineseFlashcard
from tutor.utils.anki import AnkiConnectClient
from tutor.llm_flashcards import (
    generate_flashcards,
)
from tutor.utils.logging import dprint
from tutor.llm.prompts import get_generate_flashcard_from_word_prompt
from tutor.utils.azure import text_to_speech
from tutor.utils.config import get_config


@click.command()
@click.option("--deck", type=str, default=None, help="Deck to fix cards in")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be updated without making changes",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Limit the number of cards to process",
)
@click.option(
    "--force-update",
    is_flag=True,
    default=False,
    help="Force update all cards even if they have all required fields",
)
def fix_cards(
    deck: Optional[str],
    dry_run: bool = False,
    limit: Optional[int] = None,
    force_update: bool = False,
) -> None:
    """Fix all cards in a deck by regenerating them with latest features.

    Only regenerates audio if the sample usage changes.
    """
    # Use default deck from config if not specified
    deck = deck or get_config().default_deck
    result = _fix_cards_impl(deck, dry_run, limit, force_update)
    click.echo(result)


def _fix_cards_impl(
    deck: str,
    dry_run: bool = False,
    limit: Optional[int] = None,
    force_update: bool = False,
) -> str:
    """Implementation of fix_cards command.

    Args:
        deck: Name of the deck to fix cards in
        dry_run: If True, show what would be updated without making changes
        limit: Maximum number of cards to process
        force_update: Force update all cards even if they have all required fields

    Returns:
        A summary of what was updated
    """
    ankiconnect_client = AnkiConnectClient()

    # Get all cards in the deck
    # Escape colons in deck name for Anki's query syntax
    deck_query = f'deck:"{deck}"'
    cards = ankiconnect_client.find_notes(deck_query)
    if not cards:
        return f"No cards found in deck: {deck}"

    total_cards = len(cards)
    if limit:
        cards = cards[:limit]
        print(f"Found {total_cards} cards in deck: {deck}, processing first {limit}")
    else:
        print(f"Found {total_cards} cards in deck: {deck}")

    if dry_run:
        print("DRY RUN: No changes will be made")

    stats = {
        "total": len(cards),
        "updated": 0,
        "audio_updated": 0,
        "skipped": 0,  # Cards that don't need updates
    }

    for i, card in enumerate(cards, 1):
        try:
            print(f"\nProcessing card {i}/{len(cards)}: {card.word}")

            # Check if card needs updates
            needs_update = False
            reasons = []
            fields = ankiconnect_client.get_note_fields(card.anki_note_id)

            # Check if any required fields are missing or empty
            for field in ChineseFlashcard.get_required_anki_fields():
                if field not in fields or not fields[field]:
                    needs_update = True
                    reasons.append(f"missing {field}")

            # Force update if requested
            if force_update:
                needs_update = True
                reasons.append("force update requested")

            if not needs_update:
                print("Card is up to date, skipping...")
                stats["skipped"] += 1
                continue

            print(f"Updates needed: {', '.join(reasons)}")

            # Generate new card content
            prompt = get_generate_flashcard_from_word_prompt(card.word)
            dprint(prompt)
            flashcards = generate_flashcards(prompt)
            dprint(flashcards)
            new_card = flashcards.flashcards[0]

            # Check if we need to update audio
            need_audio = card.sample_usage != new_card.sample_usage
            if need_audio:
                print("Sample usage changed, will regenerate audio:")
                print(f"Old: {card.sample_usage}")
                print(f"New: {new_card.sample_usage}")

            if not dry_run:
                # Only generate audio if sample usage changed
                audio_filepath = (
                    text_to_speech(new_card.sample_usage) if need_audio else None
                )
                ankiconnect_client.update_flashcard(
                    card.anki_note_id, new_card, audio_filepath
                )
                stats["updated"] += 1
                if need_audio:
                    stats["audio_updated"] += 1
            else:
                print("Would update card with:")
                print(new_card)
                if need_audio:
                    print("Would regenerate audio")
                stats["updated"] += 1
                if need_audio:
                    stats["audio_updated"] += 1
        except Exception as e:
            print(f"Error processing card {card.word}: {e}")
            # Fail fast on errors
            raise Exception(
                f"Failed to process card {card.word}. Fix any issues and try again."
            )

    # Generate summary
    summary = [
        f"Card Update Summary for deck '{deck}':",
        f"Total cards processed: {stats['total']}",
        f"Cards updated: {stats['updated']}",
        f"Cards skipped (up to date): {stats['skipped']}",
        f"Audio files regenerated: {stats['audio_updated']}",
    ]

    if dry_run:
        summary.insert(1, "DRY RUN - No changes were made")

    return "\n".join(summary)
