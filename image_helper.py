from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import List

import cairosvg
from PIL import Image as ImageModule
from PIL.Image import Image

from typedefs import BBox

ICON_DIR = Path('icons')


@lru_cache
def svg2image(svg_path: Path, width: int, height: int) -> Image:
    out = BytesIO()
    cairosvg.svg2png(url=str(svg_path),
                     write_to=out,
                     parent_width=width,
                     parent_height=height)
    return ImageModule.open(out)


def draw_image_column(dest_image: Image, dest_area: BBox,
                      column_images: List[Path]) -> Image:
    ((x1, y1), (x2, y2)) = dest_area
    width = x2 - x1
    height = y2 - y1

    icon_size = min(width, height) // (len(column_images) + 1)
    icon_x = x1 + width // 2 - icon_size // 2

    y_step = (height - icon_size) // len(column_images)

    icon_imgs = [
        svg2image(icon, icon_size, icon_size) for icon in column_images
    ]

    icon_y = y1 + height // (len(column_images) + 1) - icon_size // 2
    for icon_img in icon_imgs:
        dest_image.paste(icon_img, (icon_x, icon_y), icon_img)
        icon_y += y_step

    return dest_image


def draw_image_row(dest_image: Image, dest_area: BBox,
                   row_images: List[Path]) -> Image:
    ((x1, y1), (x2, y2)) = dest_area

    width = x2 - x1
    height = y2 - y1

    icon_size = min(width, height) // max(len(row_images), 2)
    icon_y = y1 + height // 2 - icon_size // 2

    x_step = (width - icon_size) // len(row_images)

    icon_imgs = [svg2image(icon, icon_size, icon_size) for icon in row_images]

    icon_x = x1 + width // (len(row_images) + 1) - icon_size // 2
    for icon_img in icon_imgs:
        dest_image.paste(icon_img, (icon_x, icon_y), icon_img)
        icon_x += x_step

    return dest_image


def create_card_sheet(images: List[Image], hidden_image: Image, columns: int,
                      rows: int) -> Image:
    if columns > 10:
        raise ValueError('too many columns: max is 10')
    if rows > 7:
        raise ValueError('too many rows: max is 7')
    if len(images) > rows * columns - 1:
        raise ValueError(
            'too many images: max is columns*rows, with one reserved for the hidden card'
        )
    if len(images) < 1:
        raise ValueError('no images given')

    card_width, card_height = images[0].size

    sheet = ImageModule.new('RGB', (columns * card_width, rows * card_height))
    for idx, image in enumerate(images):
        x = (idx % columns) * card_width
        y = (idx // columns) * card_height
        sheet.paste(image, (x, y), image)

    sheet.paste(hidden_image,
                ((columns - 1) * card_width, (rows - 1) * card_height),
                hidden_image)
    return sheet
