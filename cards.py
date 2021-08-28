from io import BytesIO
from collections import namedtuple
import sys
import json

from PIL import Image, ImageDraw, ImageFont
import cairosvg
import openpyxl

Obstacle = namedtuple('Obstacle', ['element1', 'element2', 'name', 'flavour'])
Reward = namedtuple('Reward', ['element1', 'element2', 'name', 'text'])
Role = namedtuple('Role', ['name', 'power'])

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
    roles = []

    try:
        elements_sheet = wb['Elements']
        obstacles_sheet = wb['Obstacles']
        rewards_sheet = wb['Rewards']
        roles_sheet = wb['SpeciesRolesTrait']

        for row in elements_sheet.iter_rows(min_row=2, max_col=2):
            elements[row[0].value] = row[1].value

        for row in obstacles_sheet.iter_rows(min_row=2, max_col=4):
            obstacles.append(Obstacle(*[cell.value for cell in row]))

        for row in rewards_sheet.iter_rows(min_row=2, max_col=4):
            rewards.append(Reward(*[cell.value for cell in row]))

        for row in roles_sheet.iter_rows(min_row=2, min_col=6, max_col=7):
            if row[0].value:
                roles.append(Role(*[cell.value for cell in row]))

    finally:
        wb.close()

    return elements, obstacles, rewards, roles


def svg2image(svg, size):
    width, height = size
    out = BytesIO()
    cairosvg.svg2png(url=f'icons/{svg}',
                     write_to=out,
                     parent_width=width,
                     parent_height=height)
    return Image.open(out)


def card_template(title, card_type, text):
    width = 407
    height = 585

    num_text_lines = 8

    inset = 24
    box_separation = 8

    rect_radius = 8
    rect_outline_width = 3

    title_font = ImageFont.truetype(FONT_PATH, size=32)
    title_padding = 4

    type_font = ImageFont.truetype(FONT_PATH, size=16)
    type_padding = 2

    text_font = ImageFont.truetype(FONT_PATH, size=24)
    text_padding = 8

    img = Image.new('RGBA', (width, height), color=(255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # ---

    # Add 'Q' to every string to try to get a uniform text height.
    _, title_height = title_font.getsize(title + 'Q')
    title_box_height = title_height + title_padding * 2
    draw.rounded_rectangle(
        ((inset, inset), (width - inset, inset + title_box_height)),
        radius=rect_radius,
        outline=(0, 0, 0),
        width=rect_outline_width)

    title_x = inset + rect_radius + title_padding
    title_y = inset + title_padding
    draw.text((title_x, title_y),
              title,
              font=title_font,
              fill=(0, 0, 0),
              anchor='la')

    # ---

    type_width, type_height = type_font.getsize(card_type + 'Q')
    type_x = width - inset
    type_y = height - inset - type_height // 2 - type_padding
    draw.text((type_x, type_y),
              card_type,
              font=type_font,
              fill=(0, 0, 0),
              anchor='rm')

    type_box_x = width // 2
    type_box_y = height - inset
    type_box_width = type_width + type_padding * 2
    type_box_height = type_height + type_padding * 2
    # draw.rounded_rectangle(
    #     ((type_box_x - type_box_width // 2, type_box_y - type_box_height),
    #      (type_box_x + type_box_width // 2, type_box_y)),
    #     radius=rect_radius,
    #     outline=(0, 0, 0),
    #     width=rect_outline_width)

    # ---

    text_box_y = type_box_y - type_box_height
    text_box_height = 0
    if text:
        text_width, text_height = text_font.getsize(text + 'Q')
        text_box_y = type_box_y - type_box_height - box_separation
        text_box_height = num_text_lines * text_height + text_padding * 2
        draw.rounded_rectangle(((inset, text_box_y - text_box_height),
                                (width - inset, text_box_y)),
                               radius=rect_radius,
                               outline=(0, 0, 0),
                               width=rect_outline_width)

        draw.multiline_text((width // 2, text_box_y - text_box_height // 2),
                            text_wrap(text, text_font,
                                      width - inset * 2 - text_padding * 2),
                            font=text_font,
                            fill=(0, 0, 0),
                            anchor='mm',
                            align='center')

    # --

    img_box_y = inset + title_height + title_padding * 2 + box_separation
    img_box_height = text_box_y - img_box_y - text_box_height - box_separation
    draw.rounded_rectangle(
        ((inset, img_box_y), (width - inset, img_box_y + img_box_height)),
        radius=rect_radius,
        outline=(0, 0, 0),
        width=rect_outline_width)

    return img, (inset, img_box_y), (width - inset, img_box_y + img_box_height)


def icons_vertical(img, xy1, xy2, icons):
    x1, y1 = xy1
    x2, y2 = xy2

    width = x2 - x1
    height = y2 - y1

    icon_size = min(width, height) // (len(icons) + 1)
    icon_x = x1 + width // 2 - icon_size // 2

    y_step = (height - icon_size) // len(icons)

    icon_imgs = [svg2image(icon, (icon_size, icon_size)) for icon in icons]

    icon_y = y1 + height // (len(icons) + 1) - icon_size // 2
    for icon_img in icon_imgs:
        img.paste(icon_img, (icon_x, icon_y), icon_img)
        icon_y += y_step

    return img


def icons_horizontal(img, xy1, xy2, icons):
    x1, y1 = xy1
    x2, y2 = xy2

    width = x2 - x1
    height = y2 - y1

    icon_size = min(width, height) // max(len(icons), 2)
    icon_y = y1 + height // 2 - icon_size // 2

    x_step = (width - icon_size) // len(icons)

    icon_imgs = [svg2image(icon, (icon_size, icon_size)) for icon in icons]

    icon_x = x1 + width // (len(icons) + 1) - icon_size // 2
    for icon_img in icon_imgs:
        img.paste(icon_img, (icon_x, icon_y), icon_img)
        icon_x += x_step

    return img


def draw_element_card(element, icon):
    if 'macguffin' in element.lower():
        return

    img, xy1, xy2 = card_template(element, 'ELEMENT', '')
    return icons_vertical(img, xy1, xy2, [icon])


def draw_obstacle_card(obstacle, elements):
    img, xy1, xy2 = card_template(obstacle.name, 'OBSTACLE', obstacle.flavour)
    icons = [elements[obstacle.element1], elements[obstacle.element2]]
    return icons_horizontal(img, xy1, xy2, icons)


def draw_reward_card(reward, elements):
    name = reward.name
    if not name:
        name = f'{reward.element1}/{reward.element2}'

    img, xy1, xy2 = card_template(name, 'REWARD', reward.text)

    icons = [elements[reward.element1]]
    if reward.element2:
        icons.append(elements[reward.element2])

    return icons_vertical(img, xy1, xy2, icons)


def draw_role_card(role):
    img, xy1, xy2 = card_template(role.name, 'ROLE', role.power)
    return icons_vertical(img, xy1, xy2, ['role.svg'])


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
    sheet.save(f'generated/{name}.png')


def hidden_card():
    img, xy1, xy2 = card_template('???', 'HIDDEN', '')
    return icons_vertical(img, xy1, xy2, ['hidden.svg'])


def main():
    elements, obstacles, rewards, roles = parse_spreadsheet(sys.argv[1])

    hidden = hidden_card()

    element_cards = []
    for element, icon in elements.items():
        card = draw_element_card(element, icon)
        if card is not None:
            element_cards.append(card)
    create_image_sheets('element', element_cards, hidden)

    obstacle_cards = []
    for obstacle in obstacles:
        obstacle_cards.append(draw_obstacle_card(obstacle, elements))
    create_image_sheets('obstacle', obstacle_cards, hidden)

    reward_cards = []
    for reward in rewards:
        reward_cards.append(draw_reward_card(reward, elements))
    create_image_sheets('reward', reward_cards, hidden)

    role_cards = []
    for role in roles:
        role_cards.append(draw_role_card(role))
    create_image_sheets('role', role_cards, hidden)


if __name__ == '__main__':
    main()
