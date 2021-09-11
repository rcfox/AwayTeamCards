import sys
from pathlib import Path
from pprint import pprint

from deck import Deck
import card
import image_helper

SAVE_DIR = Path('temp')


def main(spreadsheet: Path):
    card_types = card.Card.load_card_types(spreadsheet)
    hidden = card_types[card.HiddenCard][0].draw()

    for card_type, cards in card_types.items():
        if card_type == card.HiddenCard:
            continue
        # images = [c.draw() for c in cards[:69]]
        # sheet = image_helper.create_card_sheet(images, hidden, 10, 7)
        # sheet.save(SAVE_DIR / f'{card_type.__name__}.png')

    cards = card_types[card.MacguffinCard]
    deck = Deck('foo', 'bar', 'foo.', cards)
    pprint(deck.create_tts_deck().to_json())


if __name__ == '__main__':
    if len(sys.argv) > 1:
        spreadsheet = Path(sys.argv[1])
        main(spreadsheet)
    else:
        print('Must provide an AwayTeamCards spreadsheet.')
