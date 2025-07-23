import Levenshtein

def text_confidence(str_a: str, str_b: str) -> int:
    if (max_len := max(len(str_a), len(str_b))) == 0:
        return 1
    return int((1.0 - (Levenshtein.distance(str_a.lower(), str_b.lower()) / max_len)) * 100)
