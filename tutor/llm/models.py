from typing import List, Literal, Union
from pydantic.json_schema import SkipJsonSchema
from pydantic import BaseModel, Field


class ChineseFlashcard(BaseModel):
    anki_note_id: SkipJsonSchema[Union[int, None]] = None
    word: str = Field(description="The word/phrase in simplified Chinese")
    pinyin: str = Field(description="The word romanized using Pinyin (lowercased)")
    english: str = Field(description="The word translated into English (lowercased)")
    sample_usage: str = Field(
        description="Example sentence with the word which contextualizes it"
    )
    sample_usage_english: str = Field(
        description="The sample usage field translated to English"
    )
    frequency: Literal[
        "very common", "common", "infrequent", "rare", "very rare", None
    ] = Field(
        default=None,
        description="Correctly assign one one of the predefined relative frequencies to this word/phrase",
    )

    def __str__(self):
        return f"""
Word: {self.word}
Pinyin: {self.pinyin}
English: {self.english}
Sample Usage: {self.sample_usage}
Sample Usage (English): {self.sample_usage_english}
Frequency: {self.frequency}
        """.strip()

    @classmethod
    def from_anki_json(cls, anki_json):
        fields = anki_json["fields"]
        instance = cls(
            anki_note_id=anki_json["noteId"],
            word=fields["Chinese"]["value"],
            pinyin=fields["Pinyin"]["value"],
            english=fields["English"]["value"],
            sample_usage=fields["Sample Usage"]["value"],
            sample_usage_english=fields["Sample Usage (English)"]["value"],
            frequency=None,  # currently field is only at generation
        )
        return instance


class ChineseFlashcards(BaseModel):
    flashcards: List[ChineseFlashcard]
