import math
import json
import time
from dataclasses import dataclass
from typing import List, Iterable, Dict
from pathlib import Path

from card import Card
import tabletop_simulator
import util
import image_helper

from PIL.Image import Image

BASE_FACE_URL = 'https://raw.githubusercontent.com/rcfox/AwayTeamCards/master/generated/{deck}.png?{cache_buster}'
GENERATED_PATH = Path('generated')


@dataclass
class Deck:
    name: str
    description: str
    back_url: str
    cards: List[Card]

    def subdecks(self) -> Iterable[Card]:
        yield from util.grouper(self.cards, 69)

    def generate_card_sheets(self, hidden_card: Image) -> List[Path]:
        sheets = []
        for subdeck_idx, subdeck in enumerate(self.subdecks(), start=10):
            image = self.create_subdeck_card_sheet(hidden_card, subdeck)
            filename = f'{self.name}{subdeck_idx}.png'
            path = GENERATED_PATH / filename
            image.save(path)
            sheets.append(path)
        return sheets

    def create_subdeck_card_sheet(self, hidden_card: Image,
                                  subdeck: List[Card]) -> Image:
        images = [card.draw() for card in subdeck if card]
        rows = math.ceil(len(images) / 10)
        return image_helper.create_card_sheet(images, hidden_card, 10, rows)

    def create_tts_deck(self) -> tabletop_simulator.Deck:
        tts_deck = tabletop_simulator.Deck(self.name, self.description)

        for subdeck_idx, subdeck in enumerate(self.subdecks(), start=10):
            face_url = BASE_FACE_URL.format(deck=f'{self.name}{subdeck_idx}',
                                            cache_buster=time.time())
            rows = math.ceil(len(subdeck) / 10)
            tts_deck.CustomDeck[str(subdeck_idx)] = tabletop_simulator.SubDeck(
                face_url, self.back_url, 10, rows)

            for card_id, card in enumerate(self.cards,
                                           start=subdeck_idx * 100):
                tts_card = tabletop_simulator.Card(card.name, card.description,
                                                   card_id)
                for _ in range(card.deck_count):
                    tts_deck.DeckIDs.append(card_id)
                    tts_deck.ContainedObjects.append(tts_card)

        return tts_deck
