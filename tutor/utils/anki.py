from enum import Enum
import json
from pathlib import Path
import platform

import requests

from tutor.llm.models import ChineseFlashcard


class AnkiAction(Enum):
    ADD_NOTE = "addNote"
    NOTES_INFO = "notesInfo"
    FIND_NOTES = "findNotes"
    DECK_NAMES = "deckNames"
    CREATE_DECK = "createDeck"
    UPDATE_NOTE_FIELDS = "updateNoteFields"


class AnkiConnectClient:
    def __init__(self, address="http://localhost:8765"):
        self.address = address
        self.headers = {"Content-Type": "application/json"}

    def send_request(self, action, params=None):
        if not isinstance(action, AnkiAction):
            raise ValueError("Invalid action type")

        payload = json.dumps(
            {"action": action.value, "version": 6, "params": params or {}}
        )
        response = requests.post(self.address, data=payload, headers=self.headers)

        if response.status_code != 200:
            raise Exception(
                f"AnkiConnect request failed with status {response.status_code}"
            )

        result = response.json()
        if "error" in result and result["error"]:
            raise Exception(f"AnkiConnect error: {result['error']}")

        return result.get("result")

    def get_note_details(self, note_ids):
        note_details = self.send_request(AnkiAction.NOTES_INFO, {"notes": note_ids})
        return [ChineseFlashcard.from_anki_json(nd) for nd in note_details]

    def find_note_ids(self, query):
        """Search for notes by query (e.g., deck name or tags)."""
        return self.send_request(AnkiAction.FIND_NOTES, {"query": query})

    def find_notes(self, query):
        """Search for and fetch notes by query."""
        note_ids = self.find_note_ids(query)
        return self.get_note_details(note_ids)

    def add_flashcard(self, deck_name, flashcard, audio_filepath):
        """Add a new flashcard and return its note ID."""
        note = {
            "deckName": deck_name,
            "modelName": "chinese-tutor",
            "fields": {
                "Chinese": flashcard.word,
                "Pinyin": flashcard.pinyin,
                "English": flashcard.english,
                "Sample Usage": flashcard.sample_usage,
                "Sample Usage (English)": flashcard.sample_usage_english,
            },
            "tags": [],
            "audio": [
                {
                    "path": audio_filepath,
                    "filename": audio_filepath,
                    "fields": ["Sample Usage (Audio)"],
                }
            ],
        }
        return self.send_request(AnkiAction.ADD_NOTE, {"note": note})

    def update_flashcard(self, note_id, flashcard, audio_filepath=None):
        """Update an existing flashcard."""
        payload = {
            "note": {
                "id": note_id,
                "fields": {
                    "Chinese": flashcard.word,
                    "Pinyin": flashcard.pinyin,
                    "English": flashcard.english,
                    "Sample Usage": flashcard.sample_usage,
                    "Sample Usage (English)": flashcard.sample_usage_english,
                },
            }
        }

        if audio_filepath:
            payload["note"]["fields"]["Sample Usage (Audio)"] = ""

        self.send_request(AnkiAction.UPDATE_NOTE_FIELDS, payload)

        if audio_filepath:
            payload["note"]["audio"] = [
                {
                    "path": audio_filepath,
                    "filename": audio_filepath,
                    "fields": ["Sample Usage (Audio)"],
                }
            ]
            self.send_request(AnkiAction.UPDATE_NOTE_FIELDS, payload)

    def list_decks(self):
        return self.send_request(AnkiAction.DECK_NAMES)

    def add_deck(self, deck_name):
        """Create a new deck."""
        self.send_request(AnkiAction.CREATE_DECK, {"deck": deck_name})

    def maybe_add_deck(self, deck_name):
        """Create a deck if it doesn't exist."""
        decks = self.list_decks()
        if deck_name not in decks:
            self.add_deck(deck_name)


def get_subdeck(base_deck_name: str, subdeck_name: str):
    return f"{base_deck_name}::{subdeck_name}"


def get_default_anki_media_dir() -> Path:
    """Returns the default Anki media directory path based on the operating system."""
    system = platform.system()
    home = Path.home()

    if system == "Windows":
        return home / "AppData/Roaming/Anki2/User 1/collection.media"
    elif system == "Darwin":  # macOS
        return home / "Library/Application Support/Anki2/User 1/collection.media"
    elif system == "Linux":
        return home / ".local/share/Anki2/User 1/collection.media"
    else:
        raise NotImplementedError(f"Unsupported operating system: {system}")
