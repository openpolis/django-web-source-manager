"""Webapp validators tests."""

from django.test import TestCase
from django.core.exceptions import ValidationError

from websourcemonitor.validators import validate_xpath


class ValidatorTests(TestCase):
    """Validator test class."""

    def test_validate_xpath_ok(self):
        """Validate_xpath correct xpath test."""
        try:
            validate_xpath("//*[@id=\"wpsportletdx\"]/div[3]/div/div")
        except ValidationError:
            self.fail("validate_xpath raised ValidationError unexpectedly.")

    def test_validate_xpath_ko(self):
        """Validate_xpath wrong xpath test."""
        with self.assertRaises(
            ValidationError,
            msg="//*[#id=\"wpsportletdx\"]/div[3]/div/div non è un xpath corretto."
        ):
            validate_xpath("//*[#id=\"wpsportletdx\"]/div[3]/div/div")
