import unittest
import requests_mock

from bunq.sdk.model.generated import endpoint, object_

from buaut import utils

class UtilsTest(unittest.TestCase):
    def test_convert_to_amount(self):
        # Test with integer
        response = utils.convert_to_amount(20, "EUR")
        self.assertEqual(response._value_field_for_request, "20.00")
        self.assertEqual(response._currency_field_for_request, "EUR")

        # Test with str
        response = utils.convert_to_amount("20", "EUR")
        self.assertEqual(response._value_field_for_request, "20.00")
        self.assertEqual(response._currency_field_for_request, "EUR")


if __name__ == '__main__':
    unittest.main()