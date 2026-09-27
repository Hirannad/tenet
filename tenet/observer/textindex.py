"""A deterministic term index for Hungarian and English: fold accents, strip common
suffixes, keep six characters, weight by TF-IDF, compare by cosine."""
import math
import re
import unicodedata
from collections import Counter

STOP = set("""
a az egy es is nem hogy de ha mint meg csak mar vagy ami aki ez ezt azt itt ott mert akkor
van volt lesz lett kell lehet igen sem minden mind maga sajat utan elott alatt felett kozott
mas masik uj regi most majd meg mar ugy igy olyan ilyen amit amely amelyik ahol amikor mikor
the and for with that this from are was were been have has not but you your our their its
into onto than then when what which while will would should could can may might must also
just only some such each other more most very about after before over under again once
there here where how all any both few many much own same too use used using make made
""".split())
SUFFIXES = sorted("""
nak nek ban ben bol bol ra re val vel rol hoz hez hoz ig kent ert nal nel tol tul ot et at
ok ek ak os es t k s ed ing ly ation ations ies
""".split(), key=len, reverse=True)


def fold(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def stem(word):
    for _ in range(2):
        for suffix in SUFFIXES:
            if word.endswith(suffix) and len(word) - len(suffix) >= 4:
                word = word[: -len(suffix)]
                break
        else:
            break
    return word[:6]


def tokens(text):
    words = re.split(r"[^a-z0-9]+", fold(re.sub(r"([a-z])([A-Z])", r"\1 \2", text)))
    return [stem(w) for w in words if len(w) >= 3 and not w.isdigit() and w not in STOP]


def vectors(docs):
    """TF-IDF vectors for a {key: text or Counter} corpus: (1 + ln tf) * ln(1 + N / df)."""
    counts = {k: (v if isinstance(v, Counter) else Counter(tokens(v))) for k, v in docs.items()}
    df = Counter(t for c in counts.values() for t in c)
    n = len(counts) or 1
    return {k: {t: (1 + math.log(tf)) * math.log(1 + n / df[t]) for t, tf in c.items()} for k, c in counts.items()}


def cosine(a, b):
    if len(a) > len(b):
        a, b = b, a
    dot = sum(w * b.get(t, 0.0) for t, w in a.items())
    na = math.sqrt(sum(w * w for w in a.values()))
    nb = math.sqrt(sum(w * w for w in b.values()))
    return dot / (na * nb) if na and nb else 0.0
