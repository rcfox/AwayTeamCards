from __future__ import annotations

import re
import math
import json
import time
from dataclasses import dataclass
from typing import List, Iterable, Dict
from pathlib import Path

from card import Card, MacguffinCard
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
    hidden_card: Image
    cards: List[Card]

    @classmethod
    def load_decks(self, path: Path) -> Dict[str, Deck]:
        card_types = Card.load_card_types(path)
        hidden = card_types['HiddenCard'][0].draw()

        decks = {}
        for row in util.spreadsheet_as_dicts(path, 'Decks'):
            deck = Deck(row['Name'], row['Description'], row['Back Image'],
                        hidden, card_types[row['Card Class']])
            decks[deck.name] = deck
        return decks

    def generate_game_crafter_images(self):
        image_path = Path('game_crafter')
        for card_idx, card in enumerate(self.cards):
            if card.deck_count == 0:
                continue
            sanitized_name = re.sub(r'\W', '', card.name)
            filename = f'{sanitized_name}_{card_idx}[face,{card.deck_count}].png'
            deck_name = card.__class__.__name__.replace('Card', '')
            if isinstance(card, MacguffinCard):
                if card.power_rating > 0:
                    deck_name = 'Ideal'
                else:
                    deck_name = 'Caveat'
            path = image_path/ deck_name / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            print(path)
            image = card.draw_game_crafter()
            image.save(path)

    def subdecks(self) -> Iterable[Card]:
        yield from util.grouper(self.cards, 69)

    def generate_card_sheets(self) -> List[Path]:
        sheets = []
        for subdeck_idx, subdeck in enumerate(self.subdecks(), start=10):
            image = self.create_subdeck_card_sheet(subdeck)
            filename = f'{self.name}{subdeck_idx}.png'
            path = GENERATED_PATH / filename
            image.save(path)
            sheets.append(path)
        return sheets

    def create_subdeck_card_sheet(self, subdeck: List[Card]) -> Image:
        images = [card.draw() for card in subdeck if card]
        rows = math.ceil(len(images) / 10)
        return image_helper.create_card_sheet(images, self.hidden_card, 10,
                                              rows)

    def create_tts_deck(self) -> tabletop_simulator.Deck:
        tts_deck = tabletop_simulator.Deck(self.name, self.description)

        for subdeck_idx, subdeck in enumerate(self.subdecks(), start=10):
            subdeck = [card for card in subdeck if card]
            face_url = BASE_FACE_URL.format(deck=f'{self.name}{subdeck_idx}',
                                            cache_buster=time.time())

            rows = math.ceil(len(subdeck) / 10)
            tts_deck.CustomDeck[str(subdeck_idx)] = tabletop_simulator.SubDeck(
                face_url, self.back_url, 10, rows)

            for card_id, card in enumerate(subdeck, start=subdeck_idx * 100):
                tts_card = tabletop_simulator.Card(card.name, card.description,
                                                   card_id)
                tts_card.Tags = card.get_tags()
                for _ in range(card.deck_count):
                    tts_deck.DeckIDs.append(card_id)
                    tts_deck.ContainedObjects.append(tts_card)

        return tts_deck
