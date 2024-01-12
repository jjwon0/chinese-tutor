from enum import Enum
import json

import requests


class AnkiAction(Enum):
    ADD_NOTE = "addNote"
    CARDS_INFO = "cardsInfo"
    FIND_CARDS = "findCards"


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

    def get_card_details(self, card_ids):
        """
        Retrieve details for a list of card IDs.

        :param card_ids: List of card IDs.
        :return: A list of dictionaries containing card details.
        """
        return self.send_request(AnkiAction.CARDS_INFO, {"cards": card_ids})

    def maybe_get_card_details(self, text, deck_name):
        """
        Check if a card with the specified front content exists in the given deck.

        :param text: The content on the front side of the card to check.
        :param deck_name: The name of the deck to search in.
        :return: True if the card exists, False otherwise.
        """
        card_ids = self.send_request(
            AnkiAction.FIND_CARDS, {"query": f'deck:"{deck_name}" "{text}"'}
        )
        if card_ids:
            return self.get_card_details(card_ids)

    def add_flashcard(self, deck_name, flashcard):
        """
        Adds a flashcard to an Anki deck with the 'chinese-tutor' note type.

        Parameters:
        deck_name (str): Name of the Anki deck.
        chinese (str): The Chinese text.
        pinyin (str): The corresponding Pinyin.
        english (str): The English translation.
        sample_usage (str): A sample sentence in Chinese.
        sample_usage_english (str): English translation of the sample sentence.
        """
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
        }
        return self.send_request(AnkiAction.ADD_NOTE, {"note": note})
