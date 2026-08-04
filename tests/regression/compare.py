from difflib import SequenceMatcher


def similarity(expected, actual):
    return SequenceMatcher(
        None,
        expected.lower(),
        actual.lower()
    ).ratio()