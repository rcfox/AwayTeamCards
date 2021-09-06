from __future__ import annotations

from dataclasses import dataclass, field
from typing import ContextManager, Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont

from util import spreadsheet, text_wrap

FONT_PATH = '/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf'

ELEMENTS: Dict[str, Element] = {}


@dataclass
class Element:
    name: str
    image_filename: str

    @classmethod
    def load(cls, path: Path) -> List[Element]:
        elements = []
        with spreadsheet(path) as wb:
            for row in wb['Elements'].iter_rows(min_row=2, max_col=2):
                name = row[0].value
                if name is None:
                    continue

                image = row[1].value
                e = Element(name, image)
                elements.append(e)
                ELEMENTS[e.name] = e
        return elements

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

    min_text_box_size: int = 8

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

    def get_text_height(self, font: ImageFont) -> int:
        # Use 'Q' since it's full height and has a descender
        _, height = font.getsize('Q')
        return height

    def draw_title_box(self, draw: ImageDraw, title: str) -> None:
        font = self.font.font_variant(size=self.title_font_size)

        title_box_height = self.get_text_height(font) + self.title_padding * 2

        draw.rounded_rectangle(
            ((self.inset, self.inset),
             (self.width - self.inset, self.inset + title_box_height)),
            radius=self.rect_radius,
            outline=self.fg_colour,
            width=self.rect_stroke_width)

        title_x = self.inset + self.rect_radius + self.title_padding
        title_y = self.inset + self.title_padding
        draw.text((title_x, title_y),
                  title,
                  font=font,
                  fill=self.fg_colour,
                  anchor='la')

    def draw_type_marker(self, draw: ImageDraw, card_type: str) -> None:
        font = self.font.font_variant(size=self.type_font_size)
        type_height = self.get_text_height(font)
        type_x = self.width - self.inset
        type_y = self.height - self.inset - type_height // 2 - self.type_padding
        draw.text((type_x, type_y),
                  card_type.upper(),
                  font=font,
                  fill=self.fg_colour,
                  anchor='rm')

    def get_text_box_height(self, text: str) -> int:
        font = self.font.font_variant(size=self.text_font_size)
        _, text_height = font.getsize(text + 'Q')
        text_box_height = self.min_text_box_size * text_height + self.text_padding * 2
        return text_box_height

    def draw_text_box(self, draw: ImageDraw, text: str) -> None:
        type_height = self.get_text_height(
            self.font.font_variant(size=self.type_font_size))
        bottom_y = self.height - self.inset - type_height - self.type_padding * 2
        text_box_height = self.get_text_box_height(text)
        top_y = bottom_y - text_box_height - self.box_separation

        font = self.font.font_variant(size=self.text_font_size)
        draw.rounded_rectangle(
            ((self.inset, top_y), (self.width - self.inset, bottom_y)),
            radius=self.rect_radius,
            outline=self.fg_colour,
            width=self.rect_stroke_width)

        draw.multiline_text(
            (self.width // 2, bottom_y - text_box_height // 2),
            text_wrap(text, font,
                      self.width - self.inset * 2 - self.text_padding * 2),
            font=font,
            fill=self.fg_colour,
            anchor='mm',
            align='center')

    def draw_image_box(self, draw: ImageDraw) -> None:
        text_box_y = 200
        text_box_height = 40

        title_height = self.get_text_height(
            self.font.font_variant(size=self.title_font_size))
        img_box_y = self.inset + title_height + self.title_padding * 2 + self.box_separation
        img_box_height = text_box_y - img_box_y - text_box_height - self.box_separation
        draw.rounded_rectangle(
            ((self.inset, img_box_y),
             (self.width - self.inset, img_box_y + img_box_height)),
            radius=self.rect_radius,
            outline=self.fg_colour,
            width=self.rect_stroke_width)

    def draw(self, card: Card):
        img = Image.new('RGBA', (self.width, self.height),
                        color=self.bg_colour)
        draw = ImageDraw.Draw(img)

        self.draw_title_box(draw, card.name)
        self.draw_text_box(draw, card.description)
        self.draw_image_box(draw)
        self.draw_type_marker(draw, card.get_card_type())

        return img


@dataclass
class Card:
    name: str
    description: str
    deck_count: int
    template: CardTemplate

    def draw(self):
        return self.template.draw(self)

    def get_card_type(self) -> str:
        return self.__class__.__name__.replace('Card', '')


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
