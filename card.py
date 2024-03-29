from __future__ import annotations

from dataclasses import dataclass, field
from typing import ContextManager, Dict, List, Tuple
from pathlib import Path

from util import spreadsheet, spreadsheet_as_dicts
from card_template import CardTemplate, ImageOnlyCardTemplate, TextOnlyCardTemplate, MacguffinCardTemplate
from card_template_game_crafter import PokerDeckTemplate, PokerDeckImageOnlyTemplate, PokerDeckTextOnlyTemplate, PokerDeckMacguffinCardTemplate, SquareDeckTemplate, SquareDeckImageOnlyTemplate, CircleDeckTemplate
import image_helper

ELEMENTS: Dict[str, Element] = {}


@dataclass
class Element:
    name: str
    image_filename: str

    @property
    def image_path(self) -> Path:
        return image_helper.ICON_DIR / self.image_filename

    @classmethod
    def load(cls, path: Path) -> List[Element]:
        global ELEMENTS
        ELEMENTS = {}
        with spreadsheet(path) as wb:
            for row in wb['Elements'].iter_rows(min_row=2, max_col=2):
                name = row[0].value
                if name is None:
                    continue

                image = row[1].value
                e = Element(name, image)
                ELEMENTS[e.name] = e
        return ELEMENTS.values()

    @classmethod
    def get(cls, name: str) -> Optional[Element]:
        return ELEMENTS.get(name)


@dataclass
class Card:
    name: str
    description: str
    deck_count: int

    def get_filename(self) -> str:
        filename = f'{self.__class__.__name__}{self.name}.png'
        return filename.replace('/', '')

    def tts_template(self) -> CardTemplate:
        return CardTemplate()

    def game_crafter_template(self) -> CardTemplate:
        return PokerDeckTemplate()

    def draw(self):
        return self.draw_tts()

    def draw_tts(self):
        return self.tts_template().draw(self)

    def draw_game_crafter(self):
        return self.game_crafter_template().draw(self)

    def get_card_type(self) -> str:
        return self.__class__.__name__.replace('Card', '')

    def get_tags(self) -> List[str]:
        return ['Card']

    def generate_image(self, image: Image, bbox: BBox) -> None:
        return

    @classmethod
    def load_card_types(cls, path: Path) -> Dict[str, List[Card]]:
        Element.load(path)
        card_types = {}
        for card_type in cls.__subclasses__():
            card_types[card_type.__name__] = card_type.load(path)
        return card_types


@dataclass
class ElementCard(Card):
    element: Element

    @classmethod
    def load(cls, path: Path) -> List[Card]:
        cards = []
        with spreadsheet(path) as wb:
            for row in wb['Elements'].iter_rows(min_row=2, max_col=3):
                element = Element.get(row[0].value)
                if element is None:
                    continue
                deck_count = int(row[2].value)
                cards.append(ElementCard(element.name, '', deck_count, element))
        return cards

    def tts_template(self) -> CardTemplate:
        return ImageOnlyCardTemplate()

    def game_crafter_template(self) -> CardTemplate:
        return SquareDeckImageOnlyTemplate()

    def get_tags(self) -> List[str]:
        return super().get_tags() + ['Element', self.element.name]

    def generate_image(self, image: Image, bbox: BBox) -> None:
        icons = [self.element.image_path]
        image_helper.draw_image_row(image, bbox, icons)


@dataclass
class ObstacleCard(Card):
    elements: List[Element]

    @classmethod
    def load(cls, path: Path) -> List[Card]:
        cards = []
        with spreadsheet(path) as wb:
            for row in wb['Obstacles'].iter_rows(min_row=2, max_col=5):
                elements = [Element.get(cell.value) for cell in row[:2]]
                if elements[0] is None:
                    continue
                name = row[2].value
                description = row[3].value
                deck_count = int(row[4].value)
                cards.append(ObstacleCard(name, description, deck_count, elements))
        return cards

    def get_tags(self) -> List[str]:
        return (super().get_tags() + ['Obstacle'] +
                [e.name for e in self.elements])

    def generate_image(self, image: Image, bbox: BBox) -> None:
        icons = [element.image_path for element in self.elements]
        image_helper.draw_image_row(image, bbox, icons)


@dataclass
class RewardCard(Card):
    elements: List[Element]

    @classmethod
    def load(cls, path: Path) -> List[Card]:
        cards = []
        with spreadsheet(path) as wb:
            for row in wb['Rewards'].iter_rows(min_row=2):
                elements = [Element.get(cell.value) for cell in row[3:]]
                elements = [e for e in elements if e is not None]
                if len(elements) == 0:
                    continue

                name = row[0].value
                description = row[1].value or ''
                deck_count = int(row[2].value)

                if name is None:
                    name = '/'.join(element.name for element in elements)

                cards.append(RewardCard(name, description, deck_count, elements))
        return cards

    def tts_template(self) -> CardTemplate:
        if self.description:
            return CardTemplate()
        return ImageOnlyCardTemplate()

    def game_crafter_template(self) -> CardTemplate:
        if self.description:
            return SquareDeckTemplate()
        return SquareDeckImageOnlyTemplate()

    def get_tags(self) -> List[str]:
        return (super().get_tags() + ['Reward'] +
                [e.name for e in self.elements])

    def generate_image(self, image: Image, bbox: BBox) -> None:
        icons = [element.image_path for element in self.elements]
        image_helper.draw_image_column(image, bbox, icons)


@dataclass
class RoleCard(Card):
    @classmethod
    def load(cls, path: Path) -> List[Card]:
        cards = []
        with spreadsheet(path) as wb:
            for row in wb['SpeciesRolesTrait'].iter_rows(min_row=2,
                                                         min_col=6,
                                                         max_col=7):
                name = row[0].value
                if name is None:
                    continue

                description = row[1].value or ''
                deck_count = 1

                cards.append(RoleCard(name, description, deck_count))
        return cards

    def game_crafter_template(self) -> CardTemplate:
        return CircleDeckTemplate()

    def get_tags(self) -> List[str]:
        return super().get_tags() + ['Role']

    def generate_image(self, image: Image, bbox: BBox) -> None:
        icons = [image_helper.ICON_DIR / 'role.svg']
        image_helper.draw_image_row(image, bbox, icons)


@dataclass
class MacguffinCard(Card):
    power_rating: int
    ryan_rating: List[str]
    trigger: str
    trigger_type: str

    @classmethod
    def load(cls, path: Path) -> List[Card]:
        cards = []
        for row in spreadsheet_as_dicts(path, 'MacGuffins'):
            if not (row['Name'] or '').strip() or not (row['Effect'] or '').strip():
                continue

            deck_count = 1
            power_rating = int(row['Power Rating'] or 0)
            ryan_rating = (row["Ryan's Rating"] or '').split(',')

            cards.append(
                MacguffinCard(row['Name'], row['Effect'], deck_count,
                              power_rating,
                              ryan_rating, row['Trigger'] or '',
                              row['Before/After'] or ''))

        return cards

    def tts_template(self) -> CardTemplate:
        return MacguffinCardTemplate()

    def game_crafter_template(self) -> CardTemplate:
        return PokerDeckMacguffinCardTemplate()

    def get_tags(self) -> List[str]:
        return super().get_tags() + [
            'MacGuffin',
            self.trigger.title(),
            self.trigger_type.title()
        ] + self.ryan_rating


@dataclass
class HiddenCard(Card):
    @classmethod
    def load(cls, path: Path) -> List[Card]:
        return [cls('???', '', 0)]

    def tts_template(self) -> CardTemplate:
        return ImageOnlyCardTemplate()

    def generate_image(self, image: Image, bbox: BBox) -> None:
        icons = [image_helper.ICON_DIR / 'hidden.svg']
        image_helper.draw_image_row(image, bbox, icons)
