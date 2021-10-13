import checkin
import pytz
import unittest
import vcr
from datetime import datetime

my_vcr = vcr.VCR(cassette_library_dir="tests/website_responses")
flight = ["2021-11-10 17:50", "LAX"]
user_info = ["000000", "James", "Williams"]

class FlightTimeTestCase(unittest.TestCase):
    @my_vcr.use_cassette("test_airport_timezone")
    def test_convert_to_utc(self):
        self.assertEqual(checkin.convert_to_utc(flight), datetime(2021, 11, 11, 1, 50))

    @my_vcr.use_cassette()
    def test_airport_timezone(self):
        self.assertEqual(checkin.get_airport_timezone(flight), pytz.timezone("America/Los_Angeles"))
