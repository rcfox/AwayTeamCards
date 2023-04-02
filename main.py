import json
import sys
import tempfile
from pathlib import Path
from pprint import pprint

import requests

from deck import Deck
import card
import image_helper
import util
import tabletop_simulator

SAVE_DIR = Path('generated')

SPREADSHEET_ID = '1YAY_diHKl7vRUOvA_KsW_tmMnFpQGiaZSLMKNZcBbXI'


def export_url(spreadsheet_id):
    return f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=xlsx'


def main(spreadsheet: Path):
    decks = Deck.load_decks(spreadsheet)

    for deck in decks.values():
        deck.generate_game_crafter_images()

    tts_decks = [deck.create_tts_deck() for deck in decks.values()]
    for i, deck in enumerate(tts_decks):
        deck.Transform.posX = i * 2.5

    collection = tabletop_simulator.Collection(tts_decks)

    output_json = SAVE_DIR / 'all.json'
    with output_json.open('w') as f:
        json.dump(collection.to_json(), f, indent=2)

    for deck in decks.values():
        print(deck.name)
        deck.generate_card_sheets()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        spreadsheet = Path(sys.argv[1])
        main(spreadsheet)
    else:
        print(f'Downloading spreadsheet {SPREADSHEET_ID}.')
        r = requests.get(export_url(SPREADSHEET_ID))
        r.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix='.xlsx') as tmp_file:
            tmp_file.write(r.content)
            main(Path(tmp_file.name))
