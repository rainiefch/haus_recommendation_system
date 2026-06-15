import re
import json
import difflib

with open("nlp.json", "r", encoding="utf-8") as _f:
    _CFG = json.load(_f)

VOCAB           = _CFG["vocab"]
IGNORE_WORDS    = _CFG["ignore_words"]
_NORMALIZATIONS = _CFG["normalizations"]
_INTENT_PAT     = _CFG["intent_patterns"]
_SCALE          = _CFG["scale_answers"]
_YESNO          = _CFG["yes_no_answers"]
_SWEET          = _CFG["sweetness_answers"]
_SPICY          = _CFG["spicy_answers"]
_SUBTYPE        = _CFG["food_subtypes"]
_KW_RULES       = _CFG.get("keyword_rules", {})
_KW_THRESHOLD   = _CFG.get("keyword_threshold", 2)
COMBO_TRIGGERS  = _CFG["combo_triggers"]
DRINK_TRIGGERS  = _CFG["drink_triggers"]
FOOD_TRIGGERS   = _CFG["food_triggers"]
_CATEGORY       = _CFG["category_triggers"]
NAV_NEXT        = _CFG["nav_next"]
NAV_PREV        = _CFG["nav_prev"]

try:
    from Sastrawi.Stemmer.StemmerFactory import StemmerFactory as _SF
    _stemmer = _SF().create_stemmer()
    _HAS_SASTRAWI = True
except ImportError:
    _stemmer = None
    _HAS_SASTRAWI = False

def _stem(word: str) -> str:
    if _HAS_SASTRAWI:
        return _stemmer.stem(word)
    return word

_VOCAB_STEMS = {_stem(v): v for v in VOCAB}

def normalize(text: str) -> str:
    #Lowercase - multi-word slang - single-word slang - strip suffix 'nya' - split digit - strip punctuation - collapse spaces
    text = text.lower()
    for old, new in _NORMALIZATIONS.items():
        if " " in old:
            text = text.replace(old, new)
    for old, new in _NORMALIZATIONS.items():
        if " " not in old:
            text = re.sub(rf"\b{re.escape(old)}\b", new, text)
    text = re.sub(r"\b(\w+)(ku|mu|nya)\b", r"\1", text)

    text = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", text)
    text = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def correct_typo(text: str) -> str:
    text = normalize(text)
    words = text.split()
    corrected = []
    for word in words:
        if word in VOCAB:
            corrected.append(word)
            continue
        stemmed = _stem(word)
        if stemmed in _VOCAB_STEMS:
            corrected.append(_VOCAB_STEMS[stemmed])
            continue
        match = difflib.get_close_matches(word, VOCAB, n=1, cutoff=0.78)
        if match:
            corrected.append(match[0])
            continue
        corrected.append(word)

    return " ".join(corrected)

def _match_patterns(text: str, patterns: list) -> bool:
    return any(re.search(p, text) for p in patterns)

def _score_keywords(text: str) -> dict[str, int]:
    tokens = set(text.split())
    stemmed_tokens = {_stem(t) for t in tokens}

    scores: dict[str, int] = {}
    for intent, kw_list in _KW_RULES.items():
        total = 0
        for entry in kw_list:
            if isinstance(entry, (list, tuple)) and len(entry) == 2:
                kw, weight = entry
            elif isinstance(entry, str):
                kw, weight = entry, 1
            else:
                continue
            kw_stem = _stem(kw)
            if kw in tokens or kw_stem in stemmed_tokens:
                total += weight
        if total > 0:
            scores[intent] = total

    return scores

def detect_intent(text: str) -> str:
    text = normalize(text)
    priority = ["price", "show_cart", "remove", "cancel", "payment_confirm", "pay", "recommendation", "menu"]
    for intent in priority:
        if _match_patterns(text, _INTENT_PAT[intent]):
            return intent
    for pat in _INTENT_PAT["order"]:
        if re.search(pat, text):
            if "lihat" not in text and "daftar" not in text:
                return "order"
    if _match_patterns(text, _INTENT_PAT["greeting"]):
        return "greeting"
    if detect_category(text) is not None:
        return "menu"
    scores = _score_keywords(text)
    if scores:
        best_intent = max(scores, key=scores.get)
        if scores[best_intent] >= _KW_THRESHOLD:
            return best_intent
    return "unknown"

def detect_scale(text: str):
    t = normalize(text)
    for w in _SCALE["zero"]:
        if w in t: return 0
    for w in _SCALE["two"]:
        if w in t: return 2
    for w in _SCALE["one"]:
        if w in t: return 1
    return None

def detect_sweetness(text: str):
    t = normalize(text)
    for phrase in _SWEET["high"]:
        if phrase in t: return 2
    for phrase in _SWEET["medium"]:
        if phrase in t: return 1
    return None

def detect_spicy(text: str):
    t = normalize(text)
    for phrase in _SPICY["zero"]:
        if phrase in t: return 0
    for phrase in _SPICY["medium"]:
        if phrase in t: return 1
    for phrase in _SPICY["high"]:
        if phrase in t: return 2
    return None

def detect_yes_no(text: str):
    t = normalize(text)
    for w in _YESNO["yes"]:
        if w in t: return 1
    for w in _YESNO["no"]:
        if w in t: return 0
    return None

def detect_food_subtype(text: str):
    t = normalize(text)
    for subtype, triggers in _SUBTYPE.items():
        if any(tr in t for tr in triggers):
            return subtype
    return None

def detect_category(text: str) -> str | None:
    t = normalize(text)
    for category, triggers in _CATEGORY.items():
        for trigger in triggers:
            if " " in trigger and trigger in t:
                return category
    for category, triggers in _CATEGORY.items():
        for trigger in triggers:
            if " " not in trigger and trigger in t.split():
                return category
    return None

def match_choice(user: str, choices: list) -> str | None:
    if not choices:
        return None
    t = normalize(user)
    choices_map = {normalize(c): c for c in choices}
    if t in choices_map:
        return choices_map[t]
    t_stem = _stem(t)
    for norm, original in choices_map.items():
        if _stem(norm) == t_stem:
            return original
    for norm, original in choices_map.items():
        if norm in t or t in norm:
            return original
    for word in t.split():
        matches = difflib.get_close_matches(word, list(choices_map.keys()), n=1, cutoff=0.65)
        if matches:
            return choices_map[matches[0]]
    return None