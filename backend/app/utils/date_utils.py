from datetime import date, datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def parse_date(date_str: str) -> Optional[date]:
    """Parse date string from various formats

    Supports:
    - YYYYMMDD (20190805)
    - YYYY-MM-DD (2019-08-05)
    - YYYY/MM/DD (2019/08/05)
    - ISO format (2019-08-05T00:00:00)

    Args:
        date_str: Date string in various formats

    Returns:
        date object, or None if parsing fails
    """
    if not date_str or not date_str.strip():
        return None

    date_str = date_str.strip()

    # Try different formats
    formats = [
        "%Y%m%d",       # 20190805
        "%Y-%m-%d",     # 2019-08-05
        "%Y/%m/%d",     # 2019/08/05
        "%d/%m/%Y",     # 05/08/2019
        "%d-%m-%Y",     # 05-08-2019
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    # Try ISO format parsing
    try:
        return datetime.fromisoformat(date_str.split('T')[0]).date()
    except ValueError:
        pass

    logger.warning(f"Failed to parse date: {date_str}")
    return None


def format_date(d: Optional[date], format: str = "%Y-%m-%d") -> str:
    """Format date object to string

    Args:
        d: date object
        format: Output format (default: YYYY-MM-DD)

    Returns:
        Formatted date string, or empty string if date is None
    """
    if not d:
        return ""

    try:
        return d.strftime(format)
    except Exception as e:
        logger.warning(f"Failed to format date {d}: {e}")
        return ""


def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """Parse datetime string from various formats

    Args:
        datetime_str: Datetime string

    Returns:
        datetime object, or None if parsing fails
    """
    if not datetime_str or not datetime_str.strip():
        return None

    try:
        return datetime.fromisoformat(datetime_str)
    except ValueError:
        pass

    # Try common formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(datetime_str.strip(), fmt)
        except ValueError:
            continue

    logger.warning(f"Failed to parse datetime: {datetime_str}")
    return None
