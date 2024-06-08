"""Tests template."""

import pytest

from src.collections_import.ExternalCSVHandlerClass import convert_dates
from src.collections_import.ImportSheetGenerator import (
    ImportGenerationException,
    get_hash,
)


def test_convert_dates():
    """Provide some basic date conversion tests."""
    date = "1/2/2024"
    assert convert_dates(date) == "2024"
    assert convert_dates(date, False) == "2024-02-01"
    # If the date can't be converted because it is already the correct
    # format for some other unknown type then the data is returned
    # as-is.
    date = "2024-01-01"
    assert convert_dates(date) == date
    date = "random data"
    assert convert_dates(date) == date


def test_get_hash():
    """Provide some basic testing for get hash."""
    test_row = {"MD5_HASH": "cafef00d"}
    assert get_hash(test_row) == "cafef00d"
    test_row = {"NOHASH": "badf00d"}
    with pytest.raises(ImportGenerationException) as exception_info:
        get_hash(test_row)
    assert "hashes aren't configured" in str(exception_info.value)
