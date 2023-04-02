from dataclasses import dataclass
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw

import image_helper
from typedefs import BBox
from card_template import CardTemplate

@dataclass
class PokerDeckTemplate(CardTemplate):
    width: int = 825
    height: int = 1125

    inset: int = 75
    box_separation: int = CardTemplate.box_separation * 2

    rect_radius: int = CardTemplate.rect_radius * 2
    rect_stroke_width: int = CardTemplate.rect_stroke_width * 2

    title_font_size: int = CardTemplate.title_font_size * 2
    title_padding: int = CardTemplate.title_padding * 2

    type_font_size: int = CardTemplate.type_font_size * 2
    type_padding: int = CardTemplate.type_padding *2

    text_font_size: int = CardTemplate.text_font_size *2 
    text_padding: int = CardTemplate.text_padding * 2
    

@dataclass
class PokerDeckTextOnlyTemplate(PokerDeckTemplate):
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
class PokerDeckImageOnlyTemplate(PokerDeckTemplate):
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
class PokerDeckMacguffinCardTemplate(PokerDeckTextOnlyTemplate):
    def populate_trigger(self, image: Image, card: 'MacguffinCard') -> None:
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

    def populate_rating(self, image: Image, card: 'MacguffinCard') -> None:
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

    def draw(self, card: 'Card') -> Image:
        img = super().draw(card)

        self.populate_trigger(img, card)
        self.populate_rating(img, card)

        return img
