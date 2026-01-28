import re

# Date & Time patterns
DAYS_OF_WEEK_PATTERN = r"\b(?P<weekday>Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b"
MONTH_NAMES_PATTERN = r"\b(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)\b"
ORDINAL_SUFFIX_PATTERN = r"(?<!-)(?P<ordinal>st|nd|rd|th|\d{1,2}(st|nd|rd|th))\b"

THIS_WEEKDAY_PATTERN = re.compile(r"\bthis\s+" + DAYS_OF_WEEK_PATTERN, re.IGNORECASE)
NEXT_WEEKDAY_PATTERN = re.compile(r"\bnext\s+" + DAYS_OF_WEEK_PATTERN, re.IGNORECASE) 
NTH_WEEKDAY_OF_NEXT_MONTH_PATTERN = re.compile(r"\b(?P<ordinal>first|second|third|fourth|fifth|last|\d{1,2}(st|nd|rd|th))\b\s+" \
                                               + DAYS_OF_WEEK_PATTERN + r"\s+of\s+next\s+month", re.IGNORECASE) 
NTH_OF_MONTH_PATTERN = re.compile(ORDINAL_SUFFIX_PATTERN + r"\s+of\s+" + MONTH_NAMES_PATTERN + r"(?:\s+(?P<year>\d{4}))?", re.IGNORECASE)
THREE_LETTER_MONTH_WITH_PERIOD_PATTERN = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\.(?=\W)", re.IGNORECASE)
NOON_MIDNIGHT_PATTERN = re.compile(r"\b(?:noon|midnight)\b", re.IGNORECASE)

# Prepositions pattern
PREPOSITIONS_PATTERN = re.compile(r"\b(?:at|@|on|by|the|of|during|for)\b$", re.IGNORECASE)

# Ordinals map
ORDINAL_WORDS_MAP = {
        "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
        "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
        "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14, "fifteenth": 15,
        "sixteenth": 16, "seventeenth": 17, "eighteenth": 18, "nineteenth": 19, "twentieth": 20,
        "twenty-first": 21, "twenty-second": 22, "twenty-third": 23, "twenty-fourth": 24, "twenty-fifth": 25,
        "twenty-sixth": 26, "twenty-seventh": 27, "twenty-eighth": 28, "twenty-ninth": 29, "thirtieth": 30,
        "thirty-first": 31, "last": -1
    }
