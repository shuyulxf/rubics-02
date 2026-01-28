import unittest
import itertools
import re
from abc import ABC
from datetime import datetime
from app import app, db, Event
from freezegun import freeze_time


class TestCaseBaseSetup(unittest.TestCase, ABC):
    def setUp(self):
        '''Configure the app for testing'''
        app.config['TESTING'] = True
        # Use an in-memory SQLite database for tests
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        # Create the test client
        self.app = app.test_client()
        # Push the application context and create all tables
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        '''Cleanup the database and remove the app context'''
        db.session.remove()
        db.drop_all()
        self.ctx.pop()


class TestAppRoutes(TestCaseBaseSetup):
    ''' 
    Test the app's different routes
    Unit tests in this class should be P2P (Pass-to-Pass)
    '''

    def test_home(self):
        ''' Test that the home route ("/") returns a 200 OK status code. '''
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)

    def test_add_event(self):
        ''' Test posting a new event item using the "/add" route. ''' 
        # P2P --> Should still work even if a date_time is not specified in the title
        event_title = "Test Event"
        response = self.app.post("/add", data={"title": event_title}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Verify that the new event has been added to the database.
        event = Event.query.filter_by(title=event_title).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, event_title)

    def test_delete_event(self):
        ''' Test deleting an event item using the "/delete/<event_id>" route. '''
        # Manually add a event item to delete.
        event = Event(title="Delete Test")
        db.session.add(event)
        db.session.commit()
        event_id = event.id
        # Delete the event using the delete route.
        response = self.app.get(f"/delete/{event_id}", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Use Session.get() instead of Query.get()
        deleted_event = db.session.get(Event, event_id)
        self.assertIsNone(deleted_event)


class TestDateParsing(TestCaseBaseSetup):
    ''' 
    Test the date parsing functionality. 
    Unit tests in this class should be P2P (Pass-to-Pass)
    '''

    @freeze_time("2025-06-17 12:00:00")
    def test_yyyy_mm_dd(self):
        ''' Test parsing dates in the format yyyy-mm-dd. '''
        # With time
        response = self.app.post("/add", data={"title": "Meeting on 2025-12-18 at 1:30 PM"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Verify that the date_time has been correctly parsed
        event = Event.query.filter_by(date_time=datetime(2025, 12, 18, 13, 30)).first()
        self.assertIsNotNone(event)

        # Without time
        response = self.app.post("/add", data={"title": "Meeting on 2025-12-02"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 12, 2)).first()
        self.assertIsNotNone(event)

        response = self.app.post("/add", data={"title": "Meeting on 2025/12/03"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 12, 3)).first()
        self.assertIsNotNone(event)                 
      
    @freeze_time("2025-06-17 12:00:00")
    def test_dd_mm_yyyy(self):
        ''' Test parsing dates in the format dd-mm-yyyy. '''
        # With time
        response = self.app.post("/add", data={"title": "Meeting on 20-10-2025 at 8:30 AM"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 10, 20, 8, 30)).first()
        self.assertIsNotNone(event)

        # Without time
        response = self.app.post("/add", data={"title": "Meeting on 03-10-2025"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 10, 3)).first()
        self.assertIsNotNone(event)

        response = self.app.post("/add", data={"title": "Meeting on 04/10/2025"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 10, 4)).first()
        self.assertIsNotNone(event)  

    @freeze_time("2025-06-17 12:00:00")
    def test_dd_mm(self):
        ''' Test parsing dates in the format dd-mm. '''
        # With time
        response = self.app.post("/add", data={"title": "Meeting on 20-10 at 8:30 AM"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 10, 20, 8, 30)).first()
        self.assertIsNotNone(event)

        # Without time
        response = self.app.post("/add", data={"title": "Meeting on 03-10"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 10, 3)).first()
        self.assertIsNotNone(event)

        response = self.app.post("/add", data={"title": "Meeting on 04/10"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 10, 4)).first()
        self.assertIsNotNone(event)
 
    @freeze_time("2025-06-17 12:00:00")
    def test_dd_mm_in_next_year(self):
        ''' Test parsing dates in the format dd-mm that cannot be in the future this year are interpreted as next year.'''
        # With time
        response = self.app.post("/add", data={"title": "Meeting on 03-01 at 8:30 AM"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2026, 1, 3, 8, 30)).first()
        self.assertIsNotNone(event)

        # Without time
        response = self.app.post("/add", data={"title": "Meeting on 03-02"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2026, 2, 3)).first()
        self.assertIsNotNone(event)

        response = self.app.post("/add", data={"title": "Meeting on 04/02"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2026, 2, 4)).first()
        self.assertIsNotNone(event)

    @freeze_time("2025-06-17 00:00:00")
    def test_12_hour_time_only(self):
        ''' Test parsing 12-hour time formats with AM/PM without a specified date (should be interpreted as "today"). '''
        response = self.app.post("/add", data={"title": "Meeting at 1:00 PM"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 6, 17, 13, 00)).first()
        self.assertIsNotNone(event)

    @freeze_time("2025-06-17 00:00:00")
    def test_24_hour_time_only(self):
        ''' Test parsing 24-hour time formats without a specified date (should be interpreted as "today"). '''
        response = self.app.post("/add", data={"title": "Meeting @ 8:30"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 6, 17, 8, 30)).first()
        self.assertIsNotNone(event)

    @freeze_time("2025-06-17 12:00:00")
    def test_nth_weekday_of_next_month(self):
        ''' Test parsing "[nth] [weekday] of next month" with various formats. '''
        # 1st sunday of next month
        response = self.app.post("/add", data={"title": "Meeting on the 1st Sunday of next month"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 6)).first()
        self.assertIsNotNone(event)

        # First monday of next month
        response = self.app.post("/add", data={"title": "Meeting on the first Monday of next month"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 7)).first()
        self.assertIsNotNone(event)

        # 2nd tuesday of next month
        response = self.app.post("/add", data={"title": "Meeting on the 2nd Tuesday of next month"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 8)).first()
        self.assertIsNotNone(event)

        # Second wednesday of next month
        response = self.app.post("/add", data={"title": "Meeting on the second Wednesday of next month"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 9)).first()
        self.assertIsNotNone(event)

        # 3rd thursday of next month
        response = self.app.post("/add", data={"title": "Meeting on the 3rd Thursday of next month"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 17)).first()
        self.assertIsNotNone(event)

        # Third friday of next month
        response = self.app.post("/add", data={"title": "Meeting on the third Friday of next month"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 18)).first()
        self.assertIsNotNone(event)

        # Last saturday of next month
        response = self.app.post("/add", data={"title": "Meeting on the last Saturday of next month"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 26)).first()
        self.assertIsNotNone(event)
    
    @freeze_time("2025-06-17 12:00:00")
    def test_nth_weekday_of_next_month_with_time(self):
        ''' 
        Test parsing "[nth] [weekday] of next month" with time. 
        '''
        response = self.app.post("/add", data={"title": "Meeting on the 1st Sunday of next month at 8:00 AM"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 6, 8, 0)).first()
        self.assertIsNotNone(event)

        response = self.app.post("/add", data={"title": "Meeting on the 1st Sunday of next month at noon"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 6, 12, 0)).first()
        self.assertIsNotNone(event)

        response = self.app.post("/add", data={"title": "Meeting on the 1st Sunday of next month at midnight"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 6, 0, 0)).first()
        self.assertIsNotNone(event)
    
    def test_invalid_datetimes(self):
        '''
        Test invalid dates & times.
        Events should still be added to the database, but their date_time should be None & their title should not be cleaned.
        '''
        titles_with_invalid_datetimes = [
            "Meeting on 2025-02-29",  # Invalid leap year
            "Meeting on 30/02/2025", 
            "Meeting at 32:00"
        ]
        for title in titles_with_invalid_datetimes:
            response = self.app.post("/add", data={"title": title}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            event = Event.query.filter_by(title=title).first() 
            self.assertIsNotNone(event)
            self.assertIsNone(event.date_time)
    

class TestTitleCleaning(TestCaseBaseSetup):
    ''' 
    Test the title cleaning functionality. 
    Unit tests in this class should be P2P (Pass-to-Pass)
    '''
    @freeze_time("2025-06-17 12:00:00")
    def test_cleaning_yyyy_mm_dd(self):
        ''' Test cleaning titles with dates in the format yyyy-mm-dd. '''
        # With time
        response = self.app.post("/add", data={"title": "Meeting on 2025/10/20 at 8:00 AM"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 10, 20, 8, 0)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")

        # Without time
        response = self.app.post("/add", data={"title": "Meeting on 2025-10-03"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 10, 3)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")

    @freeze_time("2025-06-17 12:00:00")
    def test_cleaning_dd_mm_yyyy(self):
        ''' Test cleaning titles with dates in the format dd-mm-yyyy. '''
        # With time
        response = self.app.post("/add", data={"title": "Meeting on 20-10-2025 at 8:30"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 10, 20, 8, 30)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")

        # Without time
        response = self.app.post("/add", data={"title": "Meeting on 03/10/2026"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2026, 10, 3)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")

    @freeze_time("2025-06-17 12:00:00")
    def test_cleaning_dd_mm(self):
        ''' Test cleaning titles with dates in the format dd-mm. '''
        # With time
        response = self.app.post("/add", data={"title": "Meeting on 20-10 at 3:30 PM"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 10, 20, 15, 30)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")

        # Without time
        response = self.app.post("/add", data={"title": "Meeting on 03-10"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 10, 3)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")
    
    @freeze_time("2025-06-17 12:00:00")
    def test_clean_12_hour_time_only(self):
        ''' Test cleaning titles with 12-hour time formats without a specified date (should be interpreted as "today"). '''
        response = self.app.post("/add", data={"title": "Meeting at 1:00 PM"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 6, 17, 13, 0)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")
    
    @freeze_time("2025-06-17 12:00:00")
    def test_clean_24_hour_time_only(self):
        ''' Test cleaning titles with 24-hour time formats without a specified date '''
        # Note: Since 8:30 AM of "today" is in the past, it should be interpreted as "tomorrow".
        response = self.app.post("/add", data={"title": "Meeting @ 8:30"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 6, 18, 8, 30)).first() 
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")

    @freeze_time("2025-06-17 12:00:00")
    def test_clean_midnight(self):
        ''' Test cleaning titles with "midnight" '''
        response = self.app.post("/add", data={"title": "Meeting on 2025/07/24 at midnight"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 24, 0, 0)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")

    @freeze_time("2025-06-17 12:00:00")
    def test_clean_noon(self):
        ''' Test cleaning titles with "noon" '''
        response = self.app.post("/add", data={"title": "Meeting on 2025/07/24 at noon"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 24, 12, 0)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")

    @freeze_time("2025-06-17 12:00:00")
    def test_clean_nth_weekday_of_next_month(self):
        ''' Test cleaning titles with "[nth] [weekday] of next month" in them. '''
        # 1st sunday of next month
        response = self.app.post("/add", data={"title": "Meeting on the 1st Sunday of next month"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 6)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")

        # Third friday of next month
        response = self.app.post("/add", data={"title": "Meeting on the third Friday of next month"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 18)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")

        # Last saturday of next month
        response = self.app.post("/add", data={"title": "Meeting on the last Saturday of next month"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 7, 26)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")

    @freeze_time("2025-06-17 12:00:00")
    def test_at_preposition(self):
        '''Test cleaning titles with "at" preposition in them.'''
        # "at" only with regards to a time
        response = self.app.post("/add", data={"title": "Meeting at 8:00 AM"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 6, 18, 8, 0)).first()  # Note: Date is tomorrow since 8:00 AM of today is in the past
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")

        # "at" not with regards to a time
        response = self.app.post("/add", data={"title": "Meeting at the hotel"}, follow_redirects=True)
        event = Event.query.filter_by(title="Meeting at the hotel").first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting at the hotel")

        # "at" for both a time and not
        response = self.app.post("/add", data={"title": "Meeting at the hotel at 10:00 AM"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 6, 18, 10, 0)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting at the hotel")
        
    @freeze_time("2025-06-17 12:00:00")
    def test_at_symbol(self):
        '''Test cleaning titles with "@" symbol in them.'''
        # "@" only with regards to a time
        response = self.app.post("/add", data={"title": "Meeting @ 4:00 PM"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 6, 17, 16, 0)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting")

        # "@" not with regards to a time
        response = self.app.post("/add", data={"title": "Meeting @ the hotel"}, follow_redirects=True)
        event = Event.query.filter_by(title="Meeting @ the hotel").first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting @ the hotel")

        # "@" for both a time and not
        response = self.app.post("/add", data={"title": "Meeting @ the hotel @ 10:00 AM"}, follow_redirects=True)
        event = Event.query.filter_by(date_time=datetime(2025, 6, 18, 10, 0)).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Meeting @ the hotel")


class TestNthOfMonth(TestCaseBaseSetup):
    ''' 
    Test the parsing & cleaning of "nth of month" dates.
    These are NEW unit tests that should **not** be P2P. 
    '''

    ORDINAL_STRINGS = [
        "first", "second", "third", "fourth", "fifth",
        "sixth", "seventh", "eighth", "ninth", "tenth",
        "eleventh", "twelfth", "thirteenth", "fourteenth",
        "fifteenth", "sixteenth", "seventeenth", "eighteenth",
        "nineteenth", "twentieth", "twenty-first", "twenty-second",
        "twenty-third", "twenty-fourth", "twenty-fifth",
        "twenty-sixth", "twenty-seventh", "twenty-eighth",
        "twenty-ninth", "thirtieth", "thirty-first"
    ]

    ORDINAL_NUMERALS = [
        "1st", "2nd", "3rd", "4th", "5th",
        "6th", "7th", "8th", "9th", "10th",
        "11th", "12th", "13th", "14th",
        "15th", "16th", "17th", "18th",
        "19th", "20th", "21st", "22nd",
        "23rd", "24th", "25th",
        "26th","27th", "28th", 
        "29th", "30th", "31st"
    ]

    MONTHS = [
        "January", "February", "March", "April", "May", "June", 
        "July", "August", "September", "October","November", "December" 
    ]

    MONTH_PATTERN = re.compile(r"\b(?:" + "|".join(MONTHS) + r")\b", re.IGNORECASE)

    @classmethod
    def setUpClass(cls):
        ''' Set up the class for testing "nth of month" dates '''
        super().setUpClass()
        cls.event_titles = cls.generate_event_titles_with_expected_results()

    @classmethod
    def get_expected_datetime_result(cls, ordinal_idx: int, month_string: str, expected_hour: int = 0, expected_minute: int = 0) -> datetime:
        ''' Generate the expected datetime result for an "nth of month" date. '''
        day_number = ordinal_idx + 1 # 1 (not 0) for the first ordinal
        month_number = datetime.strptime(month_string, "%B").month

        # Since tests are frozen on June 17, 2025 at 12:00 PM, 
        # all January to May dates should be interpreted as 2026, 
        # and all July to December dates should be interpreted as 2025.
        # The year of June dates will depend on the day_number .
        # 17th of January and before should be interpreted as 2026 because midnight and 10:00 AM of 2025 are already past.
        if month_number <= 5 or (month_number == 6 and day_number <= 17):
            year = 2026
        else:
            year = 2025

        return datetime(year, month_number, day_number, expected_hour, expected_minute)

    @classmethod
    def generate_event_titles_with_expected_results(cls):
        '''
        Generate a dict event titles with expected results for "nth of month" dates. 
        Key: The event title
        Values: Tuple of (expected datetime, expected cleaned title)
        '''
        event_titles = {}

        # With numerals
        for i, (ordinal_numeral, month) in enumerate(zip(cls.ORDINAL_NUMERALS, itertools.cycle(cls.MONTHS))):
            event_title = f"Meeting on the {ordinal_numeral} of {month} at the hotel"
            expected_cleaned_title = "Meeting at the hotel"
            if i % 2 == 0:
                # With time (~50% of events)
                event_title += " at 10:00 AM"
                expected_date = cls.get_expected_datetime_result(i, month, 10, 0)
            else:  
                expected_date = cls.get_expected_datetime_result(i, month)
            event_titles[event_title] = (expected_date, expected_cleaned_title)

        # With letters
        for i, (ordinal_string, month) in enumerate(zip(cls.ORDINAL_STRINGS, itertools.cycle(reversed(cls.MONTHS)))):
            # Substitute "June" for "May" when ordinal is "thirty-first"
            # Events with invalid dates will be generated in the appropriate unit test instead
            month = "May" if ordinal_string == "thirty-first" else month
            event_title = f"Assignment due on the {ordinal_string} of {month}"
            expected_cleaned_title = "Assignment due"
            if i % 2 == 0:
                # With time (~50% of events)
                event_title += " at 23:59"
                expected_date = cls.get_expected_datetime_result(i, month, 23, 59)
            else:
                expected_date = cls.get_expected_datetime_result(i, month)
            event_titles[event_title] = (expected_date, expected_cleaned_title)

        return event_titles

    @freeze_time("2025-06-17 12:00:00")
    def test_nth_of_month(self):
        ''' 
        Test parsing "nth of month" dates, both with numerals and letters, with and without times.
        A total of 62 events are tested, with 31 using numerals and 31 using letters.
        '''
        for title, (expected_date, expected_cleaned_title) in self.event_titles.items():
            response = self.app.post("/add", data={"title": title}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            event = Event.query.filter_by(date_time=expected_date).first()
            self.assertIsNotNone(event)  # Test that the date was parsed correctly 
            self.assertEqual(event.title, expected_cleaned_title) # Test that the title was cleaned correctly

    @freeze_time("2025-06-17 12:00:00")
    def test_nth_of_month_with_year(self):
        ''' 
        Test parsing "nth of month" dates with a year in the title, both with numerals and letters, with and without times.
        A total of 62 events are tested, with 31 using numerals and 31 using letters.
        '''
        for title, (expected_date, expected_cleaned_title) in self.event_titles.items():
            # Insert year after the month in the title
            match = self.MONTH_PATTERN.search(title)
            if match:
                month_end_idx = match.span()[1]
                title = title[:month_end_idx] + f" {expected_date.year}" + title[month_end_idx:]

            response = self.app.post("/add", data={"title": title}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            event = Event.query.filter_by(date_time=expected_date).first()
            self.assertIsNotNone(event) # Test that the date was parsed correctly
            self.assertEqual(event.title, expected_cleaned_title) # Test that the title was cleaned correctly
            
    @freeze_time("2025-06-17 12:00:00")
    def test_nth_of_month_valid_leap_year(self):
        ''' 
        Test parsing "29th of February" for a valid leap year (2028).
        NOTE: Already passes in preedit codebase, making this a P2P unit test.
        '''
        response = self.app.post("/add", data={"title": "Vacation on the 29th of February 2028 by the river"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        event = Event.query.filter_by(date_time=datetime(2028, 2, 29)).first()
        self.assertIsNotNone(event)  # Test that the date was parsed correctly
        self.assertEqual(event.title, "Vacation by the river")  # Test that the title was cleaned correctly
   
    @freeze_time("2025-06-17 12:00:00")
    def test_invalid_nth_of_month(self):
        '''
        Test parsing "nth of month" dates with invalid dates.
        Events should still be added to the database, but their date_time should be None & their title should not be cleaned.
        '''
        titles_with_invalid_dates = [
            "Meeting on the 29th of February 2026",  # Non-leap year 
            "Meeting on the twenty-ninth of February 2026",  # Non-leap year
            "Meeting on the 30th of February",
            "Meeting on the thirtieth of February", 
            "Meeting on the 31st of April",    
            "Meeting on the 31st of June",      
            "Meeting on the thirty-first of September",
            "Meeting on the thirty-first of November",
            "Meeting on the 32nd of December",
            "Meeting on the thirty-second of January",
            "Meeting on the 100th of December",
            "Meeting on the last of December",  # Should be "last **day** of December" to be truly unambiguous and valid
        ]
        for title in titles_with_invalid_dates:
            response = self.app.post("/add", data={"title": title}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            event = Event.query.filter_by(title=title).first()
            self.assertIsNotNone(event)  # Test that the title was cleaned correctly
            self.assertIsNone(event.date_time) # Test that the date was (correctly) not set to an impossible date


if __name__ == "__main__":
    unittest.main()
