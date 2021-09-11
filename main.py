import sys
from pathlib import Path
from pprint import pprint

import card

SAVE_DIR = Path('temp')


def main(spreadsheet: Path):
    card_types = card.Card.load_card_types(spreadsheet)

    for cards in card_types.values():
        for c in cards:
            c.draw().save(SAVE_DIR / c.get_filename())
    pprint(card_types)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        spreadsheet = Path(sys.argv[1])
        main(spreadsheet)
    else:
        print('Must provide an AwayTeamCards spreadsheet.')
