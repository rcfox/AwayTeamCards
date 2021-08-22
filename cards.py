from io import BytesIO
from collections import namedtuple
import sys
import json

from PIL import Image, ImageDraw, ImageFont
import cairosvg
import openpyxl

Obstacle = namedtuple('Obstacle', ['element1', 'element2', 'name', 'flavour'])


def parse_spreadsheet(filename):
    wb = openpyxl.load_workbook(filename, read_only=True)
    elements = {}
    obstacles = []

    try:
        elements_sheet = wb['Elements']
        obstacles_sheet = wb['Obstacles']

        for row in elements_sheet.iter_rows(min_row=2, max_col=2):
            elements[row[0].value] = row[1].value

        for row in obstacles_sheet.iter_rows(min_row=2):
            obstacles.append(Obstacle(*[cell.value for cell in row]))

    finally:
        wb.close()

    return elements, obstacles


def draw_element_card(element, icon):
    width = 407
    height = 585

    img = Image.new('RGBA', (width, height), color=(255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype('/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf',
                              size=64)
    text_width, text_height = font.getsize(element)

    title_x = width // 2 - text_width // 2
    title_y = 32

    draw.text((title_x, title_y), element, font=font, fill=(0, 0, 0))

    out = BytesIO()
    cairosvg.svg2png(url=icon,
                     write_to=out,
                     parent_width=max(width, height) // 2,
                     parent_height=max(width, height) // 2),
    icon_img = Image.open(out)
    icon_img.save('foo.png')

    icon_width, icon_height = icon_img.size

    img.paste(
        icon_img,
        (width // 2 - icon_width // 2, height // 2 - icon_height // 2 + 32),
        icon_img)

    img.save(f'{element}.png')

    return img


def create_image_sheets(name, images, hidden):
    if len(images) > 69:
        create_image_sheets(name + '_', images[70:], hidden)

    sheet_width = 10
    if len(images) <= 10:
        sheet_width = len(images) // 2 + 1
    sheet_height = len(images) // sheet_width + 1

    card_width, card_height = images[0].size

    sheet = Image.new('RGB',
                      (sheet_width * card_width, sheet_height * card_height))
    width, height = images[0].size
    for idx, image in enumerate(images):
        x = (idx % sheet_width) * width
        y = (idx // sheet_width) * height
        sheet.paste(image, (x, y), image)

    sheet.paste(hidden,
                ((sheet_width - 1) * width, (sheet_height - 1) * height),
                hidden)
    sheet.save(f'{name}.png')


def hidden_card(size):
    img = Image.new('RGBA', size)
    draw = ImageDraw.Draw(img)

    draw.ellipse(((0, 0), size), fill=(255, 0, 0))
    return img


def main():
    elements, obstacles = parse_spreadsheet(sys.argv[1])

    element_cards = []
    for element, icon in elements.items():
        element_cards.append(draw_element_card(element, icon))
    hidden = hidden_card(element_cards[0].size)
    create_image_sheets('element', element_cards, hidden)


if __name__ == '__main__':
    main()
