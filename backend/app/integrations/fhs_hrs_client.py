import httpx
import logging
from typing import Optional, Dict, List
from datetime import date

logger = logging.getLogger(__name__)


class FHSHRSClient:
    """Client for FHS HRS API - fetches employee information without authentication"""

    def __init__(self):
        self.base_url = "https://www.fhs.com.tw/ads/api/Furnace/rest/json/hr"
        self.timeout = 30.0
        self.headers = {
            "User-Agent": "FHSHRSClient/1.0",
            "Accept": "text/plain; charset=utf-8",
        }

    async def _fetch_text(self, path: str) -> Optional[str]:
        """Internal helper to fetch raw text from API

        Returns None if request fails (no exceptions raised)
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=self.headers)
                resp.raise_for_status()
                resp.encoding = "utf-8"  # Force UTF-8 for Chinese/Vietnamese text
                return resp.text
        except httpx.HTTPStatusError as e:
            logger.error(f"HRS API HTTP error: {url} - Status {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"HRS API request error: {url} - {e}")
            return None
        except Exception as e:
            logger.error(f"HRS API unexpected error: {url} - {e}")
            return None

    def _parse_employee_data(self, raw_text: str) -> Optional[Dict]:
        """Parse pipe-separated employee data from HRS API response

        Expected format: 22 fields separated by |
        Fields: name_tw|name_en|dob|start_date|dept|job_title|...|phone2|spouse_name
        """
        try:
            # Extract first data block (before any duplicate entries)
            if not raw_text or not raw_text.strip():
                return None

            # Tránh trường hợp HRS trả về lặp dữ liệu
            raw_text = raw_text.split("o|o", 1)[0]

            # Split by pipe
            fields = raw_text.split('|')

            if len(fields) < 22:
                logger.warning(f"HRS API response has only {len(fields)} fields, expected 22")
                return None

            # Map to dictionary (based on PRD field order)
            return {
                "name_tw": fields[0].strip() if fields[0] else None,
                "name_en": fields[1].strip() if fields[1] else None,
                "dob": fields[2].strip() if fields[2] else None,  # YYYYMMDD
                "start_date": fields[3].strip() if fields[3] else None,
                "dept": fields[4].strip() if fields[4] else None,
                "job_title": fields[5].strip() if fields[5] else None,
                "job_type": fields[7].strip() if len(fields) > 7 and fields[7] else None,
                "department_code": fields[9].strip() if len(fields) > 9 and fields[9] else None,
                "salary": fields[13].strip() if len(fields) > 13 and fields[13] else "0",
                "address1": fields[17].strip() if len(fields) > 17 and fields[17] else None,  # Current address
                "address2": fields[18].strip() if len(fields) > 18 and fields[18] else None,  # Household
                "phone1": fields[19].strip() if len(fields) > 19 and fields[19] else None,
                "phone2": fields[20].strip() if len(fields) > 20 and fields[20] else None,
                "spouse_name": fields[21].strip() if len(fields) > 21 and fields[21] else None,
            }
        except Exception as e:
            logger.error(f"Failed to parse HRS employee data: {e}")
            return None

    async def get_employee_info(self, emp_id: int) -> Optional[Dict]:
        """Fetch single employee information from HRS API

        Args:
            emp_id: Employee ID (e.g., 6204)

        Returns:
            Dict with employee data, or None if not found/error
        """
        # Convert to VNW00XXXXX format
        emp_id_str = f"VNW00{emp_id:05d}"

        # Call API endpoint
        path = f"s10/{emp_id_str}"
        raw_text = await self._fetch_text(path)

        if not raw_text:
            logger.info(f"No data from HRS API for {emp_id_str}")
            return None

        # Parse response
        employee_data = self._parse_employee_data(raw_text)

        if employee_data:
            # Add employee_id to result
            employee_data["employee_id"] = emp_id_str

        return employee_data

    async def bulk_get_employees(self, from_id: int, to_id: int) -> List[Optional[Dict]]:
        """Fetch multiple employees from HRS API

        Args:
            from_id: Starting employee ID (e.g., 6200)
            to_id: Ending employee ID (e.g., 6210)

        Returns:
            List of employee dicts (None for failed/not found IDs)
        """
        results = []

        for emp_id in range(from_id, to_id + 1):
            employee_data = await self.get_employee_info(emp_id)
            results.append(employee_data)

        return results
