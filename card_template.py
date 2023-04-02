from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

import image_helper
from util import text_wrap
from typedefs import BBox

FONT_PATH = '/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf'


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

    def get_text_width(self, font: ImageFont, text: str) -> int:
        width, _ = font.getsize(text)
        return width

    def draw_rect(self, draw: ImageDraw, bbox: BBox) -> None:
        draw.rounded_rectangle(bbox,
                               radius=self.rect_radius,
                               outline=self.fg_colour,
                               width=self.rect_stroke_width)

    def populate_title(self, draw: ImageDraw, title: str, bbox: BBox) -> None:
        self.draw_rect(draw, bbox)

        ((x1, y1), (x2, _)) = bbox
        font = self.font.font_variant(size=self.title_font_size)
        title_x = x1 + self.rect_radius + self.title_padding
        title_y = y1 + self.title_padding

        max_width = x2 - self.rect_radius - self.title_padding - title_x
        font_adjust = 1
        while self.get_text_width(font, title) > max_width:
            font = self.font.font_variant(size=self.title_font_size - font_adjust)
            font_adjust += 1

        draw.text((title_x, title_y + font_adjust // 2),
                  title,
                  font=font,
                  fill=self.fg_colour,
                  anchor='la')

    def get_title_box(self) -> BBox:
        font = self.font.font_variant(size=self.title_font_size)

        title_box_height = self.get_text_height(font) + self.title_padding * 2

        x1 = self.get_x1()
        x2 = self.get_x2()
        y1 = self.inset
        y2 = y1 + title_box_height

        return ((x1, y1), (x2, y2))

    def get_type_marker_offset(self) -> int:
        font = self.font.font_variant(size=self.type_font_size)
        type_height = self.get_text_height(font)
        return type_height + self.type_padding * 2

    def populate_type_marker(self, draw: ImageDraw, card_type: str) -> None:
        font = self.font.font_variant(size=self.type_font_size)

        type_height = self.get_text_height(font)
        type_x = self.width - self.inset
        type_y = self.height - self.inset - type_height // 2 - self.type_padding
        draw.text((type_x, type_y),
                  card_type.upper(),
                  font=font,
                  fill=self.fg_colour,
                  anchor='rm')

    def get_text_box(self) -> BBox:
        font = self.font.font_variant(size=self.text_font_size)

        text_offset = self.get_type_marker_offset()

        text_height = self.get_text_height(font)
        text_box_height = self.text_box_rows * text_height + self.text_padding * 2

        x1 = self.get_x1()
        x2 = self.get_x2()

        y2 = self.height - self.inset - text_offset
        y1 = y2 - text_box_height - self.box_separation

        return ((x1, y1), (x2, y2))

    def populate_text(self, draw: ImageDraw, text: str, bbox: BBox) -> None:
        self.draw_rect(draw, bbox)

        ((x1, y1), (x2, y2)) = bbox
        font = self.font.font_variant(size=self.text_font_size)
        text_x = x1 + (x2 - x1) // 2
        text_y = y1 + (y2 - y1) // 2
        max_width = (x2 - x1) - self.text_padding * 2

        draw.multiline_text((text_x, text_y),
                            text_wrap(text, font, max_width),
                            font=font,
                            fill=self.fg_colour,
                            anchor='mm',
                            align='center')

    def get_image_box(self) -> BBox:
        text_bbox = self.get_text_box()
        title_bbox = self.get_title_box()

        (_, (_, y1)) = title_bbox
        ((_, y2), _) = text_bbox

        y1 = y1 + self.box_separation
        y2 = y2 - self.box_separation
        x1 = self.get_x1()
        x2 = self.get_x2()
        return ((x1, y1), (x2, y2))

    def populate_image(self, image: Image, card: Card, bbox: BBox) -> None:
        draw = ImageDraw.Draw(image)
        self.draw_rect(draw, bbox)

        card.generate_image(image, bbox)

    def draw(self, card: Card):
        img = Image.new('RGBA', (self.width, self.height),
                        color=self.bg_colour)
        draw = ImageDraw.Draw(img)

        self.populate_type_marker(draw, card.get_card_type())

        text_bbox = self.get_text_box()
        self.populate_text(draw, card.description, text_bbox)

        title_bbox = self.get_title_box()
        self.populate_title(draw, card.name, title_bbox)

        image_bbox = self.get_image_box()
        self.populate_image(img, card, image_bbox)

        return img


@dataclass
class TextOnlyCardTemplate(CardTemplate):
    def get_text_box(self) -> BBox:
        _, (_, title_bottom_y) = self.get_title_box()

        text_offset = self.get_type_marker_offset()

        x1 = self.get_x1()
        x2 = self.get_x2()

        y2 = self.height - self.inset - text_offset
        y1 = title_bottom_y + self.box_separation

        return ((x1, y1), (x2, y2))

    def populate_image(self, *args, **kwargs) -> None:
        return


@dataclass
class ImageOnlyCardTemplate(CardTemplate):
    def populate_text(self, *args, **kwargs) -> None:
        return

    def get_text_box(self) -> BBox:
        text_offset = self.get_type_marker_offset()

        x1 = self.get_x1()
        x2 = self.get_x2()

        y2 = self.height - self.inset - text_offset + self.box_separation
        y1 = y2

        return ((x1, y1), (x2, y2))


@dataclass
class MacguffinCardTemplate(TextOnlyCardTemplate):
    def populate_trigger(self, image: Image, card: MacguffinCard) -> None:
        draw = ImageDraw.Draw(image)

        font = self.font.font_variant(size=self.type_font_size)

        trigger_text = card.trigger.upper()

        text_height = self.get_text_height(font)
        text_width = self.get_text_width(font, trigger_text)

        before_offset = 0
        icon_offset = 0
        icon_size = 0

        if card.trigger_type.lower() == 'before':
            icon_size = text_height
            before_offset = icon_size + self.type_padding

        elif card.trigger_type.lower() == 'after':
            icon_size = text_height
            icon_offset = text_width + self.type_padding

        trigger_x = self.get_x1() + self.rect_radius + before_offset
        trigger_y = self.height - self.inset - text_height // 2 - self.type_padding

        draw.text((trigger_x, trigger_y),
                  trigger_text,
                  font=font,
                  fill=self.fg_colour,
                  anchor='lm')

        if icon_size > 0:
            gear_icon = image_helper.svg2image(
                image_helper.ICON_DIR / 'gear.svg', icon_size, icon_size)
            icon_x = self.get_x1() + self.rect_radius + icon_offset
            icon_y = trigger_y - icon_size // 2
            image.paste(gear_icon, (icon_x, icon_y), gear_icon)

    def populate_rating(self, image: Image, card: MacguffinCard) -> None:
        draw = ImageDraw.Draw(image)
        font = self.font.font_variant(size=self.title_font_size)

        ((x1, y1), (x2, y2)) = self.get_text_box()

        colour = (200, 200, 200, 255)
        text_colour = (0, 0, 0, 255)
        text = str(card.power_rating)

        if 'neutral' in card.ryan_rating:
            colour = (200, 200, 0, 255)
        if 'negative' in card.ryan_rating:
            colour = (255, 0, 0, 255)
            text_colour = (255, 255, 255, 255)
        if 'positive' in card.ryan_rating:
            colour = (0, 255, 0, 255)

        diameter = self.get_text_height(font) + 2
        offset = 8

        circle_x1 = x2 - diameter - offset
        circle_y1 = y1 + offset

        circle_x2 = x2 - offset
        circle_y2 = y1 + diameter + offset

        draw.ellipse(((circle_x1, circle_y1), (circle_x2, circle_y2)),
                     fill=colour)

        circle_x = (circle_x2 - circle_x1) // 2 + circle_x1
        circle_y = (circle_y2 - circle_y1) // 2 + circle_y1

        draw.text((circle_x, circle_y),
                  text,
                  font=font,
                  fill=text_colour,
                  anchor='mm')

    def draw(self, card: Card) -> Image:
        img = super().draw(card)

        self.populate_trigger(img, card)
        self.populate_rating(img, card)

        return img
