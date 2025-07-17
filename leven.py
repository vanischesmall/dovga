import Levenshtein

def text_similarity(str_a: str, str_b: str) -> float:
    if (max_len := max(len(str_a), len(str_b))) == 0:
        return 1.0
    return 1.0 - (Levenshtein.distance(str_a.lower(), str_b.lower()) / max_len)


print(text_similarity('Привот сесед', 'привет сосед'))
