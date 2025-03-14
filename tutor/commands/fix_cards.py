from tutor.utils.anki import AnkiConnectClient
from tutor.llm_flashcards import (
    generate_flashcards,
)
from tutor.utils.logging import dprint
from tutor.llm.prompts import get_generate_flashcard_from_word_prompt
from tutor.utils.azure import text_to_speech


def fix_cards_inner(deck: str, dry_run: bool = False) -> str:
    """Fix all cards in a deck by regenerating them with latest features.

    Only regenerates audio if the sample usage changes.

    Args:
        deck: Name of the deck to fix cards in
        dry_run: If True, show what would be updated without making changes

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

    print(f"Found {len(cards)} cards in deck: {deck}")
    if dry_run:
        print("DRY RUN: No changes will be made")

    stats = {
        "total": len(cards),
        "updated": 0,
        "audio_updated": 0,
        "skipped": 0,
        "errors": 0,
    }

    for card in cards:
        try:
            print(f"\nProcessing card: {card.word}")

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
            stats["errors"] += 1
            stats["skipped"] += 1
            continue

    # Generate summary
    summary = [
        f"Card Update Summary for deck '{deck}':",
        f"Total cards processed: {stats['total']}",
        f"Cards updated: {stats['updated']}",
        f"Audio files regenerated: {stats['audio_updated']}",
        f"Cards skipped: {stats['skipped']}",
        f"Errors encountered: {stats['errors']}",
    ]

    if dry_run:
        summary.insert(1, "DRY RUN - No changes were made")

    return "\n".join(summary)
