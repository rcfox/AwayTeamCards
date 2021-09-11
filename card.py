from __future__ import annotations

from dataclasses import dataclass, field
from typing import ContextManager, Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont

from util import spreadsheet, text_wrap

FONT_PATH = '/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf'

ELEMENTS: Dict[str, Element] = {}

Point = Tuple[int, int]
BBox = Tuple[Point, Point]


@dataclass
class Element:
    name: str
    image_filename: str

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
class CardTemplate:
    font: ImageFont = field(
        default_factory=lambda: ImageFont.truetype(FONT_PATH))

    bg_colour: Tuple[int, int, int, int] = (255, 255, 255, 255)
    fg_colour: Tuple[int, int, int, int] = (0, 0, 0, 255)

    width: int = 407
    height: int = 585

    text_box_rows: int = 8

    inset: int = 24
    box_separation: int = 8

    rect_radius: int = 8
    rect_stroke_width: int = 3

    title_font_size: int = 32
    title_padding: int = 4

    type_font_size: int = 16
    type_padding: int = 2

    text_font_size: int = 24
    text_padding: int = 8

    def get_x1(self) -> int:
        return self.inset

    def get_x2(self) -> int:
        return self.width - self.inset

    def get_text_height(self, font: ImageFont) -> int:
        # Use 'Q' since it's full height and has a descender
        _, height = font.getsize('Q')
        return height

    def draw_title_box(self, draw: ImageDraw, title: str) -> BBox:
        font = self.font.font_variant(size=self.title_font_size)

        title_box_height = self.get_text_height(font) + self.title_padding * 2

        x1 = self.get_x1()
        x2 = self.get_x2()
        y1 = self.inset
        y2 = y1 + title_box_height

        draw.rounded_rectangle(((x1, y1), (x2, y2)),
                               radius=self.rect_radius,
                               outline=self.fg_colour,
                               width=self.rect_stroke_width)

        title_x = x1 + self.rect_radius + self.title_padding
        title_y = y1 + self.title_padding
        draw.text((title_x, title_y),
                  title,
                  font=font,
                  fill=self.fg_colour,
                  anchor='la')

        return ((x1, y1), (x2, y2))

    def draw_type_marker(self, draw: ImageDraw, card_type: str) -> int:
        font = self.font.font_variant(size=self.type_font_size)

        type_height = self.get_text_height(font)
        type_x = self.width - self.inset
        type_y = self.height - self.inset - type_height // 2 - self.type_padding
        draw.text((type_x, type_y),
                  card_type.upper(),
                  font=font,
                  fill=self.fg_colour,
                  anchor='rm')

        return type_height + self.type_padding * 2

    def draw_text_box(self, draw: ImageDraw, text: str, offset: int) -> BBox:
        font = self.font.font_variant(size=self.text_font_size)

        text_height = self.get_text_height(font)
        text_box_height = self.text_box_rows * text_height + self.text_padding * 2

        x1 = self.get_x1()
        x2 = self.get_x2()

        y2 = self.height - self.inset - offset
        y1 = y2 - text_box_height - self.box_separation

        draw.rounded_rectangle(((x1, y1), (x2, y2)),
                               radius=self.rect_radius,
                               outline=self.fg_colour,
                               width=self.rect_stroke_width)

        text_x = x1 + (x2 - x1) // 2
        text_y = y1 + (y2 - y1) // 2
        max_width = (x2 - x1) - self.text_padding * 2

        draw.multiline_text((text_x, text_y),
                            text_wrap(text, font, max_width),
                            font=font,
                            fill=self.fg_colour,
                            anchor='mm',
                            align='center')

        return ((x1, y1), (x2, y2))

    def draw_image_box(self, draw: ImageDraw, y1: int, y2: int) -> BBox:
        y1 = y1 + self.box_separation
        y2 = y2 - self.box_separation
        x1 = self.get_x1()
        x2 = self.get_x2()

        draw.rounded_rectangle(((x1, y1), (x2, y2)),
                               radius=self.rect_radius,
                               outline=self.fg_colour,
                               width=self.rect_stroke_width)
        return ((x1, y1), (x2, y2))

    def draw(self, card: Card):
        img = Image.new('RGBA', (self.width, self.height),
                        color=self.bg_colour)
        draw = ImageDraw.Draw(img)

        text_offset = self.draw_type_marker(draw, card.get_card_type())
        title_bbox = self.draw_title_box(draw, card.name)
        text_bbox = self.draw_text_box(draw, card.description, text_offset)
        image_bbox = self.draw_image_box(draw, title_bbox[1][1],
                                         text_bbox[0][1])

        return img


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
                    ElementCard(element.name, '', deck_count, CardTemplate(),
                                element))
        return cards


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

                cards.append(
                    RewardCard(name, description, deck_count, CardTemplate(),
                               elements))
        return cards


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
                                  CardTemplate(), power_rating))
        return cards
