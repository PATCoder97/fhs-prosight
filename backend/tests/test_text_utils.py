import pytest
from app.utils.text_utils import chuan_hoa_ten, parse_number, first_block, clean_text


class TestChuanHoaTen:
    """Test Vietnamese name normalization"""

    def test_normalize_vietnamese_name(self):
        """Test normalization of Vietnamese name with proper capitalization"""
        result = chuan_hoa_ten("phan anh tuấn")
        assert result == "Phan Anh Tuấn"

    def test_normalize_with_extra_spaces(self):
        """Test normalization with multiple spaces"""
        result = chuan_hoa_ten("  phan    anh   tuấn  ")
        assert result == "Phan Anh Tuấn"

    def test_normalize_empty_string(self):
        """Test normalization of empty string"""
        result = chuan_hoa_ten("")
        assert result == ""

    def test_normalize_none(self):
        """Test normalization of None"""
        result = chuan_hoa_ten(None)
        assert result == ""

    def test_normalize_already_capitalized(self):
        """Test normalization of already capitalized name"""
        result = chuan_hoa_ten("Phan Anh Tuấn")
        assert result == "Phan Anh Tuấn"


class TestParseNumber:
    """Test number parsing from strings"""

    def test_parse_number_with_commas(self):
        """Test parsing number with commas"""
        result = parse_number("7,205,600")
        assert result == 7205600

    def test_parse_simple_number(self):
        """Test parsing simple number without commas"""
        result = parse_number("1234567")
        assert result == 1234567

    def test_parse_number_with_spaces(self):
        """Test parsing number with spaces"""
        result = parse_number("  1,234  ")
        assert result == 1234

    def test_parse_empty_string(self):
        """Test parsing empty string returns 0"""
        result = parse_number("")
        assert result == 0

    def test_parse_none(self):
        """Test parsing None returns 0"""
        result = parse_number(None)
        assert result == 0

    def test_parse_invalid_string(self):
        """Test parsing invalid string returns 0"""
        result = parse_number("abc123")
        assert result == 0


class TestFirstBlock:
    """Test extracting first data block"""

    def test_first_block_multiline(self):
        """Test extracting first line from multiline text"""
        text = "First line\nSecond line\nThird line"
        result = first_block(text)
        assert result == "First line"

    def test_first_block_single_line(self):
        """Test extracting from single line"""
        text = "Single line only"
        result = first_block(text)
        assert result == "Single line only"

    def test_first_block_empty(self):
        """Test extracting from empty string"""
        result = first_block("")
        assert result == ""

    def test_first_block_none(self):
        """Test extracting from None"""
        result = first_block(None)
        assert result == ""


class TestCleanText:
    """Test text cleaning"""

    def test_clean_text_with_spaces(self):
        """Test cleaning text with extra spaces"""
        result = clean_text("  Hello   World  ")
        assert result == "Hello World"

    def test_clean_text_empty(self):
        """Test cleaning empty string"""
        result = clean_text("")
        assert result == ""

    def test_clean_text_none(self):
        """Test cleaning None"""
        result = clean_text(None)
        assert result == ""
