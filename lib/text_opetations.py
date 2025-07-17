import Levenshtein

def text_confidence(pattern: str, string: str) -> float:
    if (max_len := max(len(pattern), len(string))) == 0:
        return 1.0
    return 1.0 - (Levenshtein.distance(pattern.lower(), string.lower()) / max_len)
