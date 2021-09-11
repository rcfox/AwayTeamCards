from __future__ import annotations

from dataclasses import dataclass, field
from typing import ContextManager, Dict, List, Tuple
from pathlib import Path

from util import spreadsheet
from card_template import CardTemplate, TextOnlyCardTemplate, ImageOnlyCardTemplate
import image_helper

ELEMENTS: Dict[str, Element] = {}

ICON_DIR = Path('icons')


@dataclass
class Element:
    name: str
    image_filename: str

    @property
    def image_path(self) -> Path:
        return ICON_DIR / self.image_filename

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
    template: CardTemplate

    def get_filename(self) -> str:
        filename = f'{self.__class__.__name__}{self.name}.png'
        return filename.replace('/', '')

    def draw(self):
        return self.template.draw(self)

    def get_card_type(self) -> str:
        return self.__class__.__name__.replace('Card', '')

    def generate_image(self, image: Image, bbox: BBox) -> None:
        return

    @classmethod
    def load_card_types(cls, path: Path) -> Dict[type, List[Card]]:
        Element.load(path)
        card_types = {}
        for card_type in cls.__subclasses__():
            card_types[card_type] = card_type.load(path)
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
                cards.append(
                    ElementCard(element.name, '', deck_count,
                                ImageOnlyCardTemplate(), element))
        return cards

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
                cards.append(
                    ObstacleCard(name, description, deck_count, CardTemplate(),
                                 elements))
        return cards

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

                if description:
                    template = CardTemplate()
                else:
                    template = ImageOnlyCardTemplate()

                cards.append(
                    RewardCard(name, description, deck_count, template,
                               elements))
        return cards

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

                cards.append(
                    RoleCard(name, description, deck_count, CardTemplate()))
        return cards

    def generate_image(self, image: Image, bbox: BBox) -> None:
        icons = [ICON_DIR / 'role.svg']
        image_helper.draw_image_row(image, bbox, icons)


@dataclass
class MacguffinCard(Card):
    power_rating: int

    @classmethod
    def load(cls, path: Path) -> List[Card]:
        cards = []
        with spreadsheet(path) as wb:
            for row in wb['MacGuffins'].iter_rows(min_row=2, max_col=3):
                name = row[0].value
                if name is None:
                    continue

                power_rating = 0
                try:
                    power_rating = int(row[1].value or 0)
                except ValueError:
                    pass

                description = row[2].value or ''

                deck_count = 1

                cards.append(
                    MacguffinCard(name, description, deck_count,
                                  TextOnlyCardTemplate(), power_rating))
        return cards
