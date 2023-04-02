from dataclasses import dataclass
import math

from PIL import Image, ImageDraw

import image_helper
from typedefs import BBox
from card_template import CardTemplate
from util import text_wrap

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
    type_padding: int = CardTemplate.type_padding * 2

    text_font_size: int = CardTemplate.text_font_size * 2
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
class SquareDeckTemplate(CardTemplate):
    width: int = 1125
    height: int = 1125

    inset: int = 75
    box_separation: int = CardTemplate.box_separation * 2

    rect_radius: int = CardTemplate.rect_radius * 2
    rect_stroke_width: int = CardTemplate.rect_stroke_width * 2

    title_font_size: int = CardTemplate.title_font_size * 2
    title_padding: int = CardTemplate.title_padding * 2

    type_font_size: int = CardTemplate.type_font_size * 2
    type_padding: int = CardTemplate.type_padding * 2

    text_font_size: int = CardTemplate.text_font_size * 2
    text_padding: int = CardTemplate.text_padding * 2


@dataclass
class SquareDeckTextOnlyTemplate(SquareDeckTemplate):
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
class SquareDeckImageOnlyTemplate(SquareDeckTemplate):
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



@dataclass
class CircleDeckTemplate(CardTemplate):
    width: int = 1125
    height: int = 1125

    inset: int = 75
    box_separation: int = CardTemplate.box_separation * 2

    rect_radius: int = CardTemplate.rect_radius * 2
    rect_stroke_width: int = CardTemplate.rect_stroke_width * 2

    title_font_size: int = CardTemplate.title_font_size * 2
    title_padding: int = CardTemplate.title_padding * 2

    type_font_size: int = CardTemplate.type_font_size * 2
    type_padding: int = CardTemplate.type_padding * 2

    text_font_size: int = CardTemplate.text_font_size * 2
    text_padding: int = CardTemplate.text_padding * 2


    def draw(self, card: 'Card'):
        img = Image.new('RGBA', (self.width, self.height),
                        color=self.bg_colour)
        draw = ImageDraw.Draw(img)

        card_bbox = ((self.inset, self.inset), (self.width - self.inset, self.height - self.inset))
        draw.ellipse(card_bbox,
                     outline=self.fg_colour, width=self.rect_stroke_width)


        self.populate_text(draw, card.description, card_bbox)

        self.populate_title(draw, card.name, card_bbox)

        image_bbox = self.get_image_box()
        self.populate_image(img, card, image_bbox)

        return img

    def populate_text(self, draw: ImageDraw, text: str, bbox: BBox) -> None:
        ((x1, y1), (x2, y2)) = bbox
        center_y = y2 - (y2 - y1) // 2
        font = self.font.font_variant(size=self.text_font_size)
        text_x = x1 + (x2 - x1) // 2
        text_y = y2 - (y2 - y1) // 2
        width = (x2 - x1) - self.text_padding * 2

        circle_radius = width // 2
        dist_from_center = text_y - center_y
        font_height = self.get_text_height(font)

        def max_width(line_num):
            y = dist_from_center + font_height * (line_num + 1)
            if y > circle_radius:
                return 0
            return math.sqrt(circle_radius**2 - y**2) * 2

        draw.multiline_text((text_x, text_y),
                            text_wrap(text, font, max_width),
                            font=font,
                            fill=self.fg_colour,
                            anchor='ma',
                            align='center')

    def populate_title(self, draw: ImageDraw, title: str, bbox: BBox) -> None:
        ((x1, y1), (x2, y2)) = bbox
        font = self.font.font_variant(size=self.title_font_size)
        title_x = x2 - (x2 - x1) // 2
        title_y = y1 + (y2 - y1) // 3

        center_y = y2 - (y2 - y1) // 2

        circle_radius = (x2 - x1) // 2 - self.title_padding * 2
        dist_from_center = title_y - center_y
        font_height = self.get_text_height(font)

        def max_width(line_num):
            y = dist_from_center + font_height * (line_num + 1)
            if y > circle_radius:
                return 0
            return math.sqrt(circle_radius**2 - y**2) * 2

        draw.multiline_text((title_x, title_y),
                            text_wrap(title, font, max_width),
                            font=font,
                            fill=self.fg_colour,
                            anchor='ma',
                            align='center')

    def get_image_box(self) -> BBox:
        x1 = self.get_x1()
        x2 = self.get_x2()
        y1 = self.inset
        y2 = y1 + (self.height - self.inset) // 3
        return ((x1, y1), (x2, y2))

    def populate_image(self, image: Image, card: 'Card', bbox: BBox) -> None:
        card.generate_image(image, bbox)
