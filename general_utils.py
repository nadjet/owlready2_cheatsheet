import unicodedata
from io import StringIO
import csv
import re


def deaccent(text):
    if not isinstance(text, str):
        text = text.decode('utf8')
    norm = unicodedata.normalize("NFD", text)
    result = ''.join(ch for ch in norm if unicodedata.category(ch) != 'Mn')
    return unicodedata.normalize("NFC", result)


def clean_name(name: str):
    name = re.sub(r"\s\s+"," ", name)
    return name.strip()


def parse_string_csv(string_csv, delimiter=','):
    """
    :param string_csv: the string is a row of csv
    :return: a list of the csv values
    """
    f = StringIO(string_csv)
    reader = csv.reader(f, delimiter=delimiter)
    results = []
    for row in reader:
        for item in row:
            item = clean_name(item)
            if item=="":
                continue
            results.append(item)
        break
    return results