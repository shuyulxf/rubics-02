from dateutil.parser import parse 
from dateparser.search import search_dates 
from datetime import datetime, timedelta 
from constants import THIS_WEEKDAY_PATTERN, NEXT_WEEKDAY_PATTERN, NTH_WEEKDAY_OF_NEXT_MONTH_PATTERN, THREE_LETTER_MONTH_WITH_PERIOD_PATTERN, NOON_MIDNIGHT_PATTERN, PREPOSITIONS_PATTERN, NTH_OF_MONTH_PATTERN, MONTH_NAMES_PATTERN, ORDINAL_WORDS_MAP
import calendar  # Already imported, but ensuring for monthrange 
import re  


def clean_title_date(title: str) -> str:
    ''' Clean the date & time section of the title string to make it suitable for date parsing. '''
    # Convert yyyy-mm-dd to yyyy-dd-mm for dateutil's parser (day first)
    swap_pattern = re.compile(r'\b(?P<year>\d{4})(?P<delim>\D)(?P<month>\d{2})\2(?P<day>\d{2})\b')
    def swap_mm_dd(match):
        year, delim, month, day = match.group("year"), match.group("delim"), match.group("month"), match.group("day")
        return f"{year}{delim}{day}{delim}{month}"
    
    # All "00-00" patterns are interpreted as "dd-mm", except "00:00"
    # Replace months with their names to remove ambiguity with days
    month_name_pattern = re.compile(r'(?<!\d)(?P<day>\d{2})(?P<delim>[^:\d])(?P<month>\d{2})(?!\d)')
    def convert_to_month_name(match):
        day, delim, month = match.group("day"), match.group("delim"), match.group("month")
        month_name = calendar.month_name[int(month)]
        return f"{day}{delim}{month_name}"

    # Remove periods from title for compatibility with dateparser
    title = remove_period_after_month_abbreviation(title)
    title = swap_pattern.sub(swap_mm_dd, title)
    title = re.sub(month_name_pattern, convert_to_month_name, title)
    return title


def remove_period_after_month_abbreviation(title: str) -> str:
    ''' Remove any periods immediately after a three-letter month abbreviation (if there are any), for compatibility with dateparser.'''
    match_exists = True
    while match_exists:
        match = THREE_LETTER_MONTH_WITH_PERIOD_PATTERN.search(title)
        if match:
            period_idx = match.end() - 1
            title = title[:period_idx] + title[period_idx + 1:]
        else:
            match_exists = False
    return title


def time_is_specified(cleaned_title: str) -> bool:
    ''' Check if a time is specified in the cleaned title string.'''
    title = cleaned_title.lower()  # Case-insensitive
    if "noon" in title or "midnight" in title:
        return True
    # Pattern for hh:mm, hh:mm AM/PM, hh:mm:ss, hh:mm:ss AM/PM
    time_pattern = re.compile(r'\b\d{1,2}:\d{2}(:\d{2})?\s*(am|pm)?\b', re.IGNORECASE)
    return bool(time_pattern.search(title))


def complete_ordinal_str(cleaned_title: str, match: re.Match) -> str:
        '''
        Complete the ordinal string from a regex match.
        This is used to handle cases where the ordinal string is incomplete (e.g., "st" instead of "first").
        '''
        ordinal_start_idx = match.start("ordinal")
        first_whitespace_idx = cleaned_title.rfind(' ', 0, ordinal_start_idx)
        rest_of_ordinal_str = cleaned_title[first_whitespace_idx + 1:ordinal_start_idx].strip() if first_whitespace_idx != -1 else cleaned_title[:ordinal_start_idx].strip()
        return  rest_of_ordinal_str + match.group("ordinal")
        

def ordinal_to_int(ordinal_str: str) -> int | None:
    '''
    Convert an ordinal string to an integer (e.g., "first/1st" -> 1, "second/2nd" -> 2) or -1 for "last"
    Supports English ordinal words from "first/1st" to "thirty-first/31st", and "last".
    '''
    ordinal_str = ordinal_str.lower()
    if ordinal_str in ORDINAL_WORDS_MAP:
        return ORDINAL_WORDS_MAP[ordinal_str]
    
    # Numeric ordinals (e.g., 1st, 2nd, ...)
    match = re.match(r'(\d+)(st|nd|rd|th)', ordinal_str)
    if match:
        num = int(match.group(1))
        if 1 <= num <= 31:
            return num
    return None


def weekday_to_int(weekday_str: str) -> int:
    ''' Convert a weekday string to an integer (0=Monday, 6=Sunday).'''
    weekday_map = {day.lower(): i for i, day in enumerate(calendar.day_name)}
    weekday_int = weekday_map[weekday_str.lower()]
    return weekday_int


def is_same_weekday_as_today(cleaned_title: str) -> bool:
    ''' Check if the weekday of "next [weekday]" is the same weekday as today.'''
    match = NEXT_WEEKDAY_PATTERN.search(cleaned_title)
    if match:
        weekday_str = match.group("weekday").capitalize() 
        today_weekday_str = datetime.now().strftime("%A") 
        return weekday_str == today_weekday_str
    return False


def parse_noon(cleaned_title: str, date_time: datetime | None) -> datetime | None:
    ''' Parse "noon" from a cleaned title string. This is more reliable than using dateutil or dateparser.'''
    if date_time and "noon" in cleaned_title.lower():
        return date_time.replace(hour=12, minute=0, second=0, microsecond=0)
    return date_time


def parse_simple_date(cleaned_title: str) -> datetime:
    '''Parse with dateutil (fuzzy=True) to handle (simple) natural language and mixed text '''
    return parse_noon(cleaned_title, parse(cleaned_title, dayfirst=True, fuzzy=True))


def parse_relative_natural_language_dates(cleaned_title: str) -> datetime | None:
    '''
    Parse relative natural language dates from a cleaned title string.
    This function uses dateparser to handle phrases like "tomorrow", "next week", etc.
    It also ensures that if a time is not specified, the date is set to midnight.
    '''
    parsed_date = search_dates(str(cleaned_title), settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime.now()})
    if parsed_date:
        # dateparser may hallucinate a date if there is a preposition in the title, but no date
        # e.g., "Going on vacation" --> gets parsed to tomorrow because dateparser forces a date if it sees certain prepositions
        if PREPOSITIONS_PATTERN.fullmatch(parsed_date[-1][0]):
            return None

        parsed_date = parsed_date[-1][1]
        if not time_is_specified(cleaned_title):
            # Will return a datetime at midnight if time is not specified
            parsed_date = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
    return parse_noon(cleaned_title, parsed_date)


def _parse_time(cleaned_title: str, parsed_date: datetime) -> datetime | None:
    '''
    Parse time from a cleaned title string and set it on the parsed date.
    To use when the date is parsed using with a custom regex instead of a library.
    '''
    if time_is_specified(cleaned_title):
        parsed_time = parse_simple_date(cleaned_title)
        if parsed_time:
            parsed_date = parsed_date.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
    else:
        # Set to midnight if no time specified
        parsed_date = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
    return parsed_date


def validate_structured_date(cleaned_title: str) -> bool:
    '''
    Validate structured date formats (e.g., "DD-MM", "YYYY-MM-DD") to detect invalid dates like "31/04".
    Checks if the day is valid for the extracted month using calendar.monthrange.
    Focuses on supported formats from README.md (e.g., "DD-MM-YYYY", "YYYY-MM-DD", "DD/MM").
    Returns True if valid or no structured date found; False if explicitly invalid.
    '''
    # Patterns for supported structured formats (DD-MM, DD/MM, YYYY-MM-DD, etc.)
    # Covers "DD-MM", "DD/MM", "DD-MM-YYYY", "DD/MM/YYYY", "YYYY-MM-DD", "YYYY/MM/DD"
    structured_patterns = [
        r'\b(\d{1,2})[/-](\d{1,2})\b',  # DD-MM or DD/MM (assumes current year)
        r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b',  # DD-MM-YYYY or DD/MM/YYYY
        r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b'   # YYYY-MM-DD or YYYY/MM/DD
    ]
    for pattern in structured_patterns:
        match = re.search(pattern, cleaned_title)
        if match:
            groups = match.groups()
            if len(groups) == 2:  # DD-MM format
                day, month = int(groups[0]), int(groups[1])
                year = datetime.now().year  # Assume current year for partial dates
            elif len(groups) == 3 and int(groups[2]) > 999:  # DD-MM-YYYY
                day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
            else:  # YYYY-MM-DD
                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
            
            # Basic range checks
            if not (1 <= month <= 12 and 1 <= day <= 31):
                return False
            
            # Validate day against month's max days (accounts for leap years via monthrange)
            _, max_days = calendar.monthrange(year, month)
            if day > max_days:
                return False
    return True  # Valid or no structured date to validate


def parse_nth_weekday_of_next_month(cleaned_title: str) -> datetime | None:
    ''' 
    Parse "[nth] [weekday] of next month" from a cleaned title string.

    Returns a tuple: (parsed date or None, is_invalid_date).

    Will return is_invalid_date=True if the date is invalid (e.g., "31st Monday of next month" when next month has only 4 Mondays).
    '''
    match = NTH_WEEKDAY_OF_NEXT_MONTH_PATTERN.search(cleaned_title)
    if match:
        ordinal_str, weekday_str = match.group("ordinal"), match.group("weekday")
        target_occurence = ordinal_to_int(ordinal_str)
        target_weekday = weekday_to_int(weekday_str)
        current_month = datetime.now().month
        next_month = current_month + 1 if current_month < 12 else 1
        year = datetime.now().year
        # Adjust year if wrapping to January
        year = year if next_month > 1 else year + 1
        
        if target_occurence == -1:
            # If parsing "last", search backwards from the end of the next next month
            next_next_month = next_month + 1 if next_month < 12 else 1
            year_of_next_next_month = year if next_month < 12 else year + 1
            last_day = datetime(year_of_next_next_month, next_next_month, 1) - timedelta(days=1)
            days_to_target_weekday = (last_day.weekday() - target_weekday) % 7
            date_target_occurrence = last_day - timedelta(days=days_to_target_weekday)
        else:
            first_day = datetime(year, next_month, 1)
            days_until_target_weekday = (target_weekday - first_day.weekday() + 7) % 7
            date_first_occurrence_of_target_weekday = datetime(year, next_month, 1) + timedelta(days=days_until_target_weekday)
            date_target_occurrence = date_first_occurrence_of_target_weekday + timedelta(weeks=target_occurence - 1)

            # Validate if the calculated date is still in the target month
            # If it overflowed (e.g., "31st Monday" when month has only 4-5 Mondays), mark as invalid
            if date_target_occurrence.month != next_month:
                return (None, True)  # Invalid: Ordinal too high for the month
        
        # Parse time (if there is one)
        return (_parse_time(cleaned_title, date_target_occurrence), False)
    return (None, False)


def parse_nth_of_month(cleaned_title: str) -> datetime | None:
    '''
    Parse "[nth] of [month] [year]" from a cleaned title string. [year] is optional.

    Returns a tuple: (parsed date or None, is_invalid_date).

    is_invalid_date is only True if the date is confirmedly invalid (e.g., "31st of February" or "last of February").
    If the date is valid or does not follow an "[nth] of [month]" pattern, is_invalid_date is False.
    '''
    match = NTH_OF_MONTH_PATTERN.search(cleaned_title)
    if match:
        month_str, year_str = match.group("month"), match.group("year")

        # Only checking for "st/th/nd/rd" suffixes to handle and detect invalid dates in this format (e.g., "thirty-second")
        # But this means ordinal_str is incomplete and needs all the letters that come between it and the first whitespace before it (or the start of the string if not preceded by a whitespace)
        ordinal_str = complete_ordinal_str(cleaned_title, match)

        day = ordinal_to_int(ordinal_str)
        month = datetime.strptime(month_str, "%B").month
        year = int(year_str) if year_str else datetime.now().year
        
        # "last" not supported for day of month
        if day is None or day == -1 or not month:  
            return (None, True)
        
        # Create date, preferring future dates
        # If parsed date is in the past, try next year
        try:
            parsed_date = datetime(year, month, day)
            if parsed_date < datetime.now():
                parsed_date = datetime(year + 1, month, day)
        except ValueError:
            return (None, True) # Invalid date (e.g., February 30th)
        
        # Parse time (if there is one)
        return (_parse_time(cleaned_title, parsed_date), False)
    return (None, False)


def find_datetime_string_in_title(title: str, datetime_str: re.Pattern | str) -> tuple[int, int]:
    '''
    Find the starting & ending indexes of the datetime string in the title.
    The datetime "string" can be either a string or a regex pattern.
    Returns (-1, -1) if the datetime string is not found.
    '''
    datetime_start_idx = -1
    datetime_end_idx = -1

    if type(datetime_str) == re.Pattern:
        match = datetime_str.search(title)
        if match and datetime_str == NTH_OF_MONTH_PATTERN:
            datetime_start_idx = title.find(complete_ordinal_str(title, match))
            datetime_end_idx = match.end()
        elif match:
            datetime_start_idx = match.start()
            datetime_end_idx = match.end()

    elif type(datetime_str) == str:
        datetime_start_idx = title.find(datetime_str)
        datetime_end_idx = datetime_start_idx + len(datetime_str)

    return (datetime_start_idx, datetime_end_idx)


def remove_date_prepositions(title: str, datetime_start_idx: int) -> tuple:
    ''' 
    Remove prepositions to the left of the datetime string until a non-preposition word is reached.
    Returns a tuple: (The full title less any datetime-related prepositions, The title section before the datetime string less any ending prepositions)
    '''
    before = title[:datetime_start_idx].rstrip()
    match_exists = True
    while match_exists:
        match = PREPOSITIONS_PATTERN.search(before)
        if match:
            before = before[:-len(match.group())].rstrip()  # Remove the preposition
        else:
            match_exists = False

    # Note: Title still contains the datetime string at this point
    # Add a whitespace between before and the rest of the title to ensure they don't get concatenated as one word
    # Double-spaces are handled later 
    title = before + ' ' + title[datetime_start_idx:]
    return (title.strip(), before)


def remove_singular_datetime_string(title: str, datetime_str: re.Pattern | str) -> str:
    '''
    Remove a given datetime string (including prepositions that immediately precede) from the title.
    The datetime "string" can be either a string or a regex pattern.
    '''
    datetime_start_idx, datetime_end_idx = find_datetime_string_in_title(title, datetime_str)
    if datetime_start_idx == -1 or datetime_end_idx == 0:
        return title
    
    after = title[datetime_end_idx + 1:]
    title, before = remove_date_prepositions(title, datetime_start_idx)
   
    # Remove the datetime string from the title
    # Add a whitespace between before and the rest of the title to ensure they don't get concatenated as one word
    # Double-spaces are handled later 
    title = before + ' ' + after
    return title.strip()


def remove_date_from_title(title: str) -> str:
    '''
    Remove any section of the event's title that denotes a date and/or time,
    including associated prepositions like "at", "@", "on", "by", "the", and "of".
    This should be called after the date/time has been parsed.
    '''
    # Remove period after three-letter month abbreviations (if there is one)
    title = remove_period_after_month_abbreviation(title)

    # Handle the special patterns that search_dates() may not detect reliably
    title = remove_singular_datetime_string(title, NTH_WEEKDAY_OF_NEXT_MONTH_PATTERN)
    title = remove_singular_datetime_string(title, NTH_OF_MONTH_PATTERN)  
    title = remove_singular_datetime_string(title, THIS_WEEKDAY_PATTERN)
    title = remove_singular_datetime_string(title, NEXT_WEEKDAY_PATTERN)
    title = remove_singular_datetime_string(title, NOON_MIDNIGHT_PATTERN)
    title = remove_singular_datetime_string(title, THREE_LETTER_MONTH_WITH_PERIOD_PATTERN)

    # Then, use search_dates to find and remove other date/time strings
    parsed_results = search_dates(title, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime.now()})
    if parsed_results:
        for datetime_string, _ in parsed_results:
            # datetime_string may contain prepositions AFTER the date or time. Remove these.
            datetime_string = remove_date_prepositions(datetime_string, len(datetime_string))[0]
            title = remove_singular_datetime_string(title, datetime_string)
        
    # Clean up multiple spaces and trim
    title = ' '.join(title.split()).strip()
    return title

