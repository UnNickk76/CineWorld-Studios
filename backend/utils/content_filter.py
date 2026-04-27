"""
Content filter per testi creativi (idea, plot, screenplay, marketing) e chat.

Strategia:
- BLASPHEMY (bestemmie): censura DURA → tutte lettere → asterischi totali ("***** ***").
- PROFANITY (parolacce comuni: cazzo, figa, merda, ...): censura SOFT → preserva prima/ultima
  lettera ("ca***o", "fi**a"). L'intento è ancora comprensibile, ma bloccato per pubblico.
- EXPLICIT (termini sessuali espliciti): censura SOFT come PROFANITY ("s***so", "p*ne").

Le liste sono in italiano standard. Il match è case-insensitive su parole intere o sostringhe
chiare (gestione varianti come "k" al posto di "c", apostrofi e plurali principali).
"""
import re
from typing import Iterable

# === Bestemmie (HARD censorship) ===
# Match anche varianti con maiuscole, spazi multipli o trattini.
BLASPHEMY_PATTERNS = [
    r"\bporco\s+d[i!1\*]o\b",
    r"\bporco\s+gesu['`]?\b",
    r"\bporca\s+madonna\b",
    r"\bporca\s+mad(?:on|onn)a\b",
    r"\bd[i!1\*]o\s+(?:bestia|porco|cane|canaro|merda|cagna|maiale|stronzo|caino|boia|infame|schifoso|deficiente|stupido|brutto|cornuto|ladro|porco|bastardo|ergo)\b",
    r"\bmadonna\s+(?:porca|puttana|troia|merda|maiala|cagna|deficiente|stupida)\b",
    r"\bcristo\s+(?:porco|cane|merda|infame|deficiente|stupido)\b",
    r"\bgesu['`]?\s+(?:porco|cane|merda)\b",
    r"\bsanto\s+d[i!1\*]o\b",
]

# === Parolacce comuni (SOFT censorship: preserva prima e ultima lettera) ===
PROFANITY_WORDS = [
    "cazzo", "cazzi", "cazzata", "cazzate", "incazzato", "incazzata",
    "figa", "fighe", "figata", "fighi", "fighetta",
    "merda", "merde", "merdaio", "merdoso", "merdosa", "stramerda",
    "stronzo", "stronza", "stronzi", "stronze", "stronzata", "stronzate",
    "coglione", "coglioni", "coglionata",
    "puttana", "puttane", "puttanata", "puttanaio", "puttaniere",
    "troia", "troie", "troione",
    "bastardo", "bastarda", "bastardi",
    "vaffanculo", "fanculo", "affanculo", "vaffancul",
    "minchia", "minchie", "minchione",
    "culo", "culi", "inculato", "inculata",
    "scopata", "scopate", "scopare", "scopato",  # comune ma esplicito
    "puttanata", "puttanate",
]

# === Termini sessualmente espliciti (SOFT censorship) ===
EXPLICIT_WORDS = [
    "sesso", "sessuale", "sessuali",
    "pene", "peni", "uccello",
    "vagina", "vagine", "patata",
    "tette", "tetta", "tettone", "seno",
    "culo", "natiche",
    "orgasmo", "orgasmi", "godere", "godimento",
    "eiaculazione", "eiacula", "eiaculare",
    "masturbazione", "masturbarsi", "masturba",
    "pompino", "pompini",
    "trombare", "trombata", "trombato",
    "scopata", "scopare", "scopato",
    "amplesso", "ampesso",
    "erezione", "eretto", "eretta",
    "preliminari", "penetrazione", "penetrare",
    "nudo", "nuda", "nudi", "nude", "nudita",
]


def _soft_censor_word(word: str) -> str:
    """Preserva prima e ultima lettera, asterisca il resto.
    Esempio: 'cazzo' -> 'ca**o'. Per parole <=2 char: tutto asterisco."""
    if len(word) <= 2:
        return "*" * len(word)
    if len(word) == 3:
        return word[0] + "*" + word[-1]
    # Ratio: ~50% del centro asteriscato, almeno 2 *
    middle_len = max(2, len(word) - 2)
    return word[0] + ("*" * middle_len) + word[-1]


def _hard_censor(text: str) -> str:
    """Sostituisce ogni carattere alfanumerico con * mantenendo spazi/punteggiatura."""
    return re.sub(r"[A-Za-zÀ-ÿ0-9]", "*", text)


# Pre-compila i pattern per performance
_BLASPHEMY_RE = [re.compile(p, re.IGNORECASE) for p in BLASPHEMY_PATTERNS]
_PROFANITY_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in sorted(set(PROFANITY_WORDS), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
_EXPLICIT_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in sorted(set(EXPLICIT_WORDS), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def censor_text(text: str, allow_explicit: bool = False) -> str:
    """Applica filtri di censura. Le bestemmie vengono SEMPRE censurate (hard).
    Le parolacce comuni vengono soft-censurate. I termini espliciti vengono soft-censurati
    a meno che `allow_explicit=True` (es. genere erotico VM18 — non usato attualmente)."""
    if not text or not isinstance(text, str):
        return text
    out = text
    # 1. Bestemmie: hard censure
    for pat in _BLASPHEMY_RE:
        out = pat.sub(lambda m: _hard_censor(m.group(0)), out)
    # 2. Parolacce comuni: soft
    out = _PROFANITY_RE.sub(lambda m: _soft_censor_word(m.group(0)), out)
    # 3. Espliciti
    if not allow_explicit:
        out = _EXPLICIT_RE.sub(lambda m: _soft_censor_word(m.group(0)), out)
    return out


def censor_dict(d: dict, fields: Iterable[str], allow_explicit: bool = False) -> dict:
    """Censura in-place i campi indicati di un dict. Ritorna lo stesso dict per chaining."""
    if not isinstance(d, dict):
        return d
    for f in fields:
        v = d.get(f)
        if isinstance(v, str):
            d[f] = censor_text(v, allow_explicit=allow_explicit)
        elif isinstance(v, list):
            d[f] = [censor_text(x, allow_explicit=allow_explicit) if isinstance(x, str) else x for x in v]
    return d


def has_blasphemy(text: str) -> bool:
    """Ritorna True se il testo contiene una bestemmia (utile per logging/abuse-tracking)."""
    if not text:
        return False
    return any(p.search(text) for p in _BLASPHEMY_RE)
