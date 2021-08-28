from io import BytesIO
from collections import namedtuple
import sys
import json

from PIL import Image, ImageDraw, ImageFont
import cairosvg
import openpyxl

Obstacle = namedtuple('Obstacle', ['element1', 'element2', 'name', 'flavour'])
Reward = namedtuple('Reward', ['element1', 'element2', 'name', 'text'])

FONT_PATH = '/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf'


def text_wrap(text, font, max_width):
    """Wrap text base on specified width.
        This is to enable text of width more than the image width to be display
        nicely.
        @params:
            text: str
                text to wrap
            font: obj
                font of the text
            max_width: int
                width to split the text with
        @return
            lines: list[str]
                list of sub-strings
        """
    lines = []

    # If the text width is smaller than the image width, then no need to split
    # just add it to the line list and return
    if font.getsize(text)[0] <= max_width:
        lines.append(text)
    else:
        #split the line by spaces to get words
        words = text.split(' ')
        i = 0
        # append every word to a line while its width is shorter than the image width
        while i < len(words):
            line = ''
            while i < len(words) and font.getsize(line +
                                                  words[i])[0] <= max_width:
                line = line + words[i] + " "
                i += 1
            if not line:
                line = words[i]
                i += 1
            lines.append(line)
    return '\n'.join(lines)


def parse_spreadsheet(filename):
    wb = openpyxl.load_workbook(filename, read_only=True)
    elements = {}
    obstacles = []
    rewards = []

    try:
        elements_sheet = wb['Elements']
        obstacles_sheet = wb['Obstacles']
        rewards_sheet = wb['Rewards']

        for row in elements_sheet.iter_rows(min_row=2, max_col=2):
            elements[row[0].value] = row[1].value

        for row in obstacles_sheet.iter_rows(min_row=2, max_col=4):
            obstacles.append(Obstacle(*[cell.value for cell in row]))

        for row in rewards_sheet.iter_rows(min_row=2, max_col=4):
            rewards.append(Reward(*[cell.value for cell in row]))

    finally:
        wb.close()

    return elements, obstacles, rewards


def svg2image(svg, size):
    width, height = size
    out = BytesIO()
    cairosvg.svg2png(url=svg,
                     write_to=out,
                     parent_width=width,
                     parent_height=height)
    return Image.open(out)


def draw_element_card(element, icon):
    width = 407
    height = 585

    img = Image.new('RGBA', (width, height), color=(255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(FONT_PATH, size=64)
    text_width, text_height = font.getsize(element)

    title_x = width // 2 - text_width // 2
    title_y = 32

    draw.text((title_x, title_y),
              element,
              font=font,
              fill=(0, 0, 0),
              align='center')

    icon_size = max(width, height) // 2
    icon_img = svg2image(icon, (icon_size, icon_size))

    img.paste(icon_img,
              (width // 2 - icon_size // 2, height // 2 - icon_size // 2 + 32),
              icon_img)

    return img


def draw_obstacle_card(obstacle, elements):
    width = 407
    height = 585

    img = Image.new('RGBA', (width, height), color=(255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    title_size = 65
    text_width = 1000
    while text_width > width - 64:
        title_size -= 1
        font = ImageFont.truetype(FONT_PATH, size=title_size)
        text_width, text_height = font.getsize(obstacle.name)

    title_x = width // 2 - text_width // 2
    title_y = 32

    draw.text((title_x, title_y),
              obstacle.name,
              font=font,
              fill=(0, 0, 0),
              align='center')

    icon_size = max(width, height) // 4
    icon_img1 = svg2image(elements[obstacle.element1], (icon_size, icon_size))
    icon_img2 = svg2image(elements[obstacle.element2], (icon_size, icon_size))

    icon_y = title_y + text_height + icon_size // 2

    img.paste(icon_img1, (width // 4 - icon_size // 2, icon_y), icon_img1)
    img.paste(icon_img2, (3 * width // 4 - icon_size // 2, icon_y), icon_img2)

    flavour_x = width // 2
    flavour_y = icon_y + icon_size + 50

    font = ImageFont.truetype(FONT_PATH, size=32)

    draw.multiline_text((flavour_x, flavour_y),
                        text_wrap(obstacle.flavour, font, width - 64),
                        font=font,
                        fill=(0, 0, 0),
                        anchor='ma',
                        align='center')
    return img


def draw_reward_card(reward, elements):
    width = 407
    height = 585
    icon_size = max(width, height) // 4

    img = Image.new('RGBA', (width, height), color=(255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    if reward.name:

        title_size = 65
        text_width = 1000
        while text_width > width - 64:
            title_size -= 1
            font = ImageFont.truetype(FONT_PATH, size=title_size)
            text_width, text_height = font.getsize(reward.name)

        title_x = width // 2 - text_width // 2
        title_y = 32

        draw.text((title_x, title_y),
                  reward.name,
                  font=font,
                  fill=(0, 0, 0),
                  align='center')

        icon_y = title_y + text_height + icon_size // 2
        icon_y2 = icon_y + icon_size + 10

    else:

        icon_y = 3 * icon_size // 4
        icon_y2 = height - 3 * icon_size // 2

    icon_img1 = svg2image(elements[reward.element1], (icon_size, icon_size))

    img.paste(icon_img1, (width // 2 - icon_size // 2, icon_y), icon_img1)

    if reward.element2 is not None:
        icon_img2 = svg2image(elements[reward.element2],
                              (icon_size, icon_size))
        img.paste(icon_img2, (width // 2 - icon_size // 2, icon_y2), icon_img2)

    if reward.text:
        font = ImageFont.truetype(FONT_PATH, size=32)
        line_height = font.getsize('hg')[1]
        text_x = width // 2
        text_y = icon_y2 + 32

        draw.multiline_text((text_x, text_y),
                            text_wrap(reward.text, font, width - 64),
                            font=font,
                            fill=(0, 0, 0),
                            anchor='ma',
                            align='center')

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
    elements, obstacles, rewards = parse_spreadsheet(sys.argv[1])

    element_cards = []
    for element, icon in elements.items():
        element_cards.append(draw_element_card(element, icon))
    hidden = hidden_card(element_cards[0].size)
    create_image_sheets('element', element_cards, hidden)

    obstacle_cards = []
    for obstacle in obstacles:
        obstacle_cards.append(draw_obstacle_card(obstacle, elements))
    create_image_sheets('obstacle', obstacle_cards, hidden)

    reward_cards = []
    for reward in rewards:
        reward_cards.append(draw_reward_card(reward, elements))
    create_image_sheets('reward', reward_cards, hidden)


if __name__ == '__main__':
    main()
