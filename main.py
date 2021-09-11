import sys
from pathlib import Path
from pprint import pprint

import card
import image_helper

SAVE_DIR = Path('temp')


def main(spreadsheet: Path):
    card_types = card.Card.load_card_types(spreadsheet)

    for card_type, cards in card_types.items():
        images = [c.draw() for c in cards[:29]]
        sheet = image_helper.create_card_sheet(images, images[-1], 10, 3)
        sheet.save(SAVE_DIR / f'{card_type.__name__}.png')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        spreadsheet = Path(sys.argv[1])
        main(spreadsheet)
    else:
        print('Must provide an AwayTeamCards spreadsheet.')
