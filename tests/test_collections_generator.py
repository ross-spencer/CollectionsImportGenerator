"""Tests template."""


from src.collections_import.ExternalCSVHandlerClass import convert_dates


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
