import pytest
from datetime import date, datetime
from app.utils.date_utils import parse_date, format_date, parse_datetime


class TestParseDate:
    """Test date parsing from various formats"""

    def test_parse_yyyymmdd(self):
        """Test parsing YYYYMMDD format"""
        result = parse_date("20190805")
        assert result == date(2019, 8, 5)

    def test_parse_yyyy_mm_dd_dash(self):
        """Test parsing YYYY-MM-DD format"""
        result = parse_date("2019-08-05")
        assert result == date(2019, 8, 5)

    def test_parse_yyyy_mm_dd_slash(self):
        """Test parsing YYYY/MM/DD format"""
        result = parse_date("2019/08/05")
        assert result == date(2019, 8, 5)

    def test_parse_dd_mm_yyyy_slash(self):
        """Test parsing DD/MM/YYYY format"""
        result = parse_date("05/08/2019")
        assert result == date(2019, 8, 5)

    def test_parse_empty_string(self):
        """Test parsing empty string returns None"""
        result = parse_date("")
        assert result is None

    def test_parse_none(self):
        """Test parsing None returns None"""
        result = parse_date(None)
        assert result is None

    def test_parse_invalid_format(self):
        """Test parsing invalid format returns None"""
        result = parse_date("invalid-date")
        assert result is None

    def test_parse_iso_format(self):
        """Test parsing ISO format with time"""
        result = parse_date("2019-08-05T10:30:00")
        assert result == date(2019, 8, 5)


class TestFormatDate:
    """Test date formatting"""

    def test_format_date_default(self):
        """Test formatting date with default format"""
        d = date(2019, 8, 5)
        result = format_date(d)
        assert result == "2019-08-05"

    def test_format_date_custom(self):
        """Test formatting date with custom format"""
        d = date(2019, 8, 5)
        result = format_date(d, format="%d/%m/%Y")
        assert result == "05/08/2019"

    def test_format_none(self):
        """Test formatting None returns empty string"""
        result = format_date(None)
        assert result == ""


class TestParseDatetime:
    """Test datetime parsing"""

    def test_parse_iso_datetime(self):
        """Test parsing ISO datetime"""
        result = parse_datetime("2019-08-05T10:30:00")
        assert result == datetime(2019, 8, 5, 10, 30, 0)

    def test_parse_datetime_with_space(self):
        """Test parsing datetime with space separator"""
        result = parse_datetime("2019-08-05 10:30:00")
        assert result == datetime(2019, 8, 5, 10, 30, 0)

    def test_parse_empty_string(self):
        """Test parsing empty string returns None"""
        result = parse_datetime("")
        assert result is None

    def test_parse_none(self):
        """Test parsing None returns None"""
        result = parse_datetime(None)
        assert result is None
