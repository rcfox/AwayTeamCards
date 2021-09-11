import json
import sys
from pathlib import Path
from pprint import pprint

from deck import Deck
import card
import image_helper
import util
import tabletop_simulator

SAVE_DIR = Path('generated')


def main(spreadsheet: Path):
    decks = Deck.load_decks(spreadsheet)

    collection = tabletop_simulator.Collection(
        [deck.create_tts_deck() for deck in decks])

    output_json = SAVE_DIR / 'all.json'
    with output_json.open('w') as f:
        json.dump(collection.to_json(), f, indent=2)

    for deck in decks:
        print(deck.name)
        deck.generate_card_sheets()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        spreadsheet = Path(sys.argv[1])
        main(spreadsheet)
    else:
        print('Must provide an AwayTeamCards spreadsheet.')
