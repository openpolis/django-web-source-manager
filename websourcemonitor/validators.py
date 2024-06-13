"""validators."""
from lxml import etree
from django.core.exceptions import ValidationError


def validate_xpath(value):
    try:
        etree.XPath(value)
    except etree.XPathSyntaxError:
        raise ValidationError(f"{value} is not a valid XPath expression.")
