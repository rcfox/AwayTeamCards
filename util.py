from contextlib import contextmanager
from typing import ContextManager, Dict, List
from pathlib import Path
import itertools

import openpyxl


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


@contextmanager
def spreadsheet(path: Path) -> ContextManager[openpyxl.Workbook]:
    wb = openpyxl.load_workbook(str(path), read_only=True)
    try:
        yield wb
    finally:
        wb.close()


def spreadsheet_as_dicts(path: Path, sheet_name: str) -> List[Dict]:
    with spreadsheet(path) as wb:
        sheet = wb[sheet_name]
        rows = sheet.iter_rows()
        header = [cell.value for cell in next(rows)]
        for row in rows:
            yield dict(zip(header, [cell.value for cell in row]))


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)
