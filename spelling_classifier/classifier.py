import re
from rapidfuzz.fuzz import ratio

# Keyboard patterns commonly produced by random typing.
KEYBOARD_PATTERNS = (
    "qwerty", "asdf", "zxcv", "qaz", "wsx", "edc", "rfv", "tgb",
    "yhn", "ujm", "ijk", "jkl", "plp", "sds", "dfg", "fgh", "ghj",
    "tyty", "rere", "wewe", "uiui", "opop", "abab", "lele", "dedede",
    "ghgh", "fwfw", "jkjk", "zxcz", "qazw", "jklop"
)

# Common spelling/phonetic substitutions children may make.
PHONETIC_REPLACEMENTS = (
    ("tch", "ch"), ("dge", "j"), ("tion", "shun"), ("sion", "zhun"),
    ("ough", "o"), ("augh", "a"), ("eigh", "ay"), ("ph", "f"),
    ("ck", "k"), ("qu", "k"), ("c", "k"), ("q", "k"),
    ("x", "ks"), ("z", "s"), ("y", "i")
)


def clean(word: str) -> str:
    return re.sub(r"[^a-z]", "", str(word).lower())


def phonetic_form(word: str) -> str:
    """Small, explainable phonetic normalization; not a full pronunciation engine."""
    s = clean(word)
    for old, new in PHONETIC_REPLACEMENTS:
        s = s.replace(old, new)
    s = re.sub(r"(.)\1+", r"\1", s)
    # Vowels are treated as one sound family for approximate child spellings.
    s = re.sub(r"[aeiou]+", "a", s)
    return s


def keyboard_score(word: str) -> float:
    s = clean(word)
    if not s:
        return 1.0
    if len(set(s)) == 1:
        return 1.0

    repeated = sum(s[i] == s[i + 2] for i in range(len(s) - 2))
    alternating = repeated / max(1, len(s) - 2)
    sequence = max((len(p) for p in KEYBOARD_PATTERNS if p in s), default=0)
    sequence_ratio = sequence / len(s)
    return max(alternating, sequence_ratio)


def ordered_match(target: str, attempt: str) -> float:
    """How much of the target appears in the same order in the attempt."""
    if not target:
        return 0.0
    j = 0
    matched = 0
    for char in attempt:
        if j < len(target) and char == target[j]:
            matched += 1
            j += 1
    return matched / len(target)


def classify(actual_word: str, typed_word: str) -> dict:
    target = clean(actual_word)
    attempt = clean(typed_word)

    if not target or not attempt:
        return {
            "label": "uncertain",
            "confidence": 0.0,
            "reason": "Missing word or attempt."
        }

    if target == attempt:
        return {
            "label": "genuine_attempt",
            "confidence": 1.0,
            "reason": "The answer is correct."
        }

    edit_similarity = ratio(target, attempt) / 100.0
    phonetic_similarity = ratio(phonetic_form(target), phonetic_form(attempt)) / 100.0
    order_similarity = ordered_match(target, attempt)
    junk = keyboard_score(attempt)

    # Very strong keyboard/repetition evidence should override weak similarity.
    if junk >= 0.75 and edit_similarity < 0.80:
        return {
            "label": "random_or_meaningless",
            "confidence": min(0.99, 0.85 + junk * 0.14),
            "reason": "Strong keyboard-mashing or repeated-character pattern."
        }

    # Close spelling mistakes.
    if edit_similarity >= 0.72:
        return {
            "label": "genuine_attempt",
            "confidence": round(min(0.99, 0.70 + edit_similarity * 0.29), 2),
            "reason": "The attempt is structurally close to the target spelling."
        }

    # Phonetic spelling can look very different from the correct spelling.
    if phonetic_similarity >= 0.68 and order_similarity >= 0.35:
        return {
            "label": "genuine_attempt",
            "confidence": round(min(0.95, 0.62 + phonetic_similarity * 0.32), 2),
            "reason": "The attempt has a strong approximate phonetic/spelling relationship."
        }

    # A partial target with junk appended is still often a genuine attempt.
    if order_similarity >= 0.70 and len(target) >= 4:
        return {
            "label": "genuine_attempt",
            "confidence": round(min(0.90, 0.65 + order_similarity * 0.25), 2),
            "reason": "Most target letters occur in the correct order."
        }

    # Borderline cases are deliberately not forced into a binary decision.
    if edit_similarity >= 0.45 or phonetic_similarity >= 0.55 or order_similarity >= 0.50:
        return {
            "label": "uncertain",
            "confidence": 0.55,
            "reason": "There is some relationship to the target, but not enough evidence for a confident decision."
        }

    return {
        "label": "random_or_meaningless",
        "confidence": 0.90,
        "reason": "Little spelling or phonetic relationship to the target."
    }
