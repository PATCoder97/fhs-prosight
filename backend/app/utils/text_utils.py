import re
import logging

logger = logging.getLogger(__name__)


def chuan_hoa_ten(name: str) -> str:
    """Normalize Vietnamese name

    - Capitalize each word
    - Trim leading/trailing spaces
    - Replace multiple spaces with single space

    Args:
        name: Raw name string

    Returns:
        Normalized name
    """
    if not name:
        return ""

    # Strip and replace multiple spaces
    name = " ".join(name.split())

    # Capitalize each word
    return name.title()


def parse_number(num_str: str) -> int:
    """Parse numeric string to integer

    Handles:
    - Commas in numbers (7,205,600 → 7205600)
    - Empty strings → 0
    - Invalid numbers → 0

    Args:
        num_str: Numeric string (may contain commas)

    Returns:
        Integer value (0 if invalid)
    """
    if not num_str or not num_str.strip():
        return 0

    try:
        # Remove commas and whitespace
        clean_str = num_str.replace(",", "").strip()
        return int(clean_str)
    except ValueError:
        logger.warning(f"Failed to parse number: {num_str}")
        return 0


def first_block(raw_text: str) -> str:
    """Extract first data block from HRS API response

    HRS API sometimes returns duplicate entries. This function extracts
    only the first block before any repetition.

    Args:
        raw_text: Raw text from HRS API

    Returns:
        First data block (before any duplicate pattern)
    """
    if not raw_text:
        return ""

    # Simple approach: Take text before any obvious duplication
    # If the response contains the same name_tw twice, take only the first occurrence
    lines = raw_text.split('\n')
    if lines:
        return lines[0].strip()

    return raw_text.strip()


def clean_text(text: str) -> str:
    """Clean and normalize text

    - Strip leading/trailing whitespace
    - Replace multiple spaces with single space
    - Remove special characters if needed

    Args:
        text: Raw text

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Strip and normalize spaces
    text = " ".join(text.split())

    return text.strip()
