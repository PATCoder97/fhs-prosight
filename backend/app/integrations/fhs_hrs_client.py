import httpx
import logging
from typing import Optional, Dict, List
from datetime import date

logger = logging.getLogger(__name__)


def _parse_number(value: str) -> float:
    """Parse a string to float, return 0.0 if empty or invalid

    Args:
        value: String representation of number (may contain commas)

    Returns:
        Parsed float value, or 0.0 if parsing fails
    """
    if not value or not value.strip():
        return 0.0
    try:
        # Remove commas from numbers (e.g., "1,712,344" → "1712344")
        cleaned = value.strip().replace(',', '')
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0


def _first_block(raw_text: str) -> str:
    """Extract first data block from HRS response (avoid duplicate entries)

    Args:
        raw_text: Raw response text from HRS API

    Returns:
        First data block before any duplicates
    """
    if not raw_text or not raw_text.strip():
        return ""
    # HRS API sometimes returns duplicate data separated by "o|o"
    return raw_text.split("o|o", 1)[0].strip()


def _parse_salary_response(fields: List[str]) -> dict:
    """Parse HRS salary response into structured format.

    Args:
        fields: List of pipe-delimited fields from HRS API (45+ fields)

    Returns:
        dict with structure:
        {
            "summary": {tong_tien_cong, tong_tien_tru, thuc_linh},
            "income": {32 income fields},
            "deductions": {10 deduction fields}
        }
    """
    # Parse income fields (32 fields) - Correct mapping from actual HRS API
    income = {
        "luong_co_ban": _parse_number(fields[44]),
        "thuong_nang_suat": _parse_number(fields[2]),
        "thuong_tet": _parse_number(fields[3]),
        "tro_cap_com": _parse_number(fields[4]),
        "tro_cap_di_lai": _parse_number(fields[5]),
        "thuong_chuyen_can": _parse_number(fields[6]),
        "phu_cap_truc_ban": _parse_number(fields[7]),
        "phu_cap_ngon_ngu": _parse_number(fields[8]),
        "phu_cap_dac_biet": _parse_number(fields[9]),
        "phu_cap_chuyen_nganh": _parse_number(fields[10]),
        "phu_cap_tac_nghiep": _parse_number(fields[11]),
        "phu_cap_khu_vuc": _parse_number(fields[12]),
        "phu_cap_tc_dot_xuat": _parse_number(fields[13]),
        "phu_cap_ngay_nghi": _parse_number(fields[14]),
        "phu_cap_tc_khan_cap": _parse_number(fields[15]),
        "phu_cap_chuc_vu": _parse_number(fields[16]),
        "tro_cap_phong": _parse_number(fields[17]),
        "phat_bu": _parse_number(fields[18]),
        "thuong_cong_viec": _parse_number(fields[19]),
        "phi_khac": _parse_number(fields[20]),
        "cong": _parse_number(fields[21]),
        "tien_dong_phuc": _parse_number(fields[22]),
        "tro_cap_com2": _parse_number(fields[23]),
        "tro_cap_dt": _parse_number(fields[24]),
        "tro_cap_nghi": _parse_number(fields[25]),
        "phu_cap_tc_le": _parse_number(fields[26]),
        "phu_cap_ca": _parse_number(fields[27]),
        "phu_cap_tc2": _parse_number(fields[28]),
        "phu_cap_nghi2": _parse_number(fields[29]),
        "phu_cap_tc_kc": _parse_number(fields[30]),
        "phu_cap_tc_dem": _parse_number(fields[31]),
    }

    # Parse deduction fields (10 fields) - Correct mapping from actual HRS API
    deductions = {
        "bhxh": _parse_number(fields[33]),
        "bh_that_nghiep": _parse_number(fields[34]),
        "bhyt": _parse_number(fields[35]),
        "ky_tuc_xa": _parse_number(fields[36]),
        "tien_com": _parse_number(fields[37]),
        "dong_phuc": _parse_number(fields[38]),
        "cong_doan": _parse_number(fields[39]),
        "khac": _parse_number(fields[40]),
        "nghi_phep": _parse_number(fields[41]),
        "thue_thu_nhap": _parse_number(fields[42]),
    }

    # Calculate totals
    tong_tien_cong = _parse_number(fields[32])
    tong_tien_tru = sum(deductions.values())
    thuc_linh = _parse_number(fields[43])

    # Verify calculation (allow 100 VND tolerance for rounding)
    expected_net = tong_tien_cong - tong_tien_tru
    if abs(expected_net - thuc_linh) > 100:
        logger.warning(
            f"Salary calculation mismatch: "
            f"expected {expected_net:.2f} (income - deductions), "
            f"got {thuc_linh:.2f} from API. "
            f"Difference: {abs(expected_net - thuc_linh):.2f} VND"
        )

    return {
        "summary": {
            "tong_tien_cong": tong_tien_cong,
            "tong_tien_tru": tong_tien_tru,
            "thuc_linh": thuc_linh
        },
        "income": income,
        "deductions": deductions
    }


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

    async def get_salary_data(self, emp_id: int, year: int, month: int) -> Optional[dict]:
        """Fetch salary data (S16) from HRS API

        Args:
            emp_id: Employee ID number (e.g., 6204)
            year: Year (e.g., 2024)
            month: Month (1-12)

        Returns:
            dict with structure:
            {
                "summary": {tong_tien_cong, tong_tien_tru, thuc_linh},
                "income": {32 income fields},
                "deductions": {10 deduction fields}
            }
            Returns None if error or no data found.
        """
        path = f"s16/VNW00{emp_id:05d}vkokv{year}-{month:02d}"

        try:
            raw_text = await self._fetch_text(path)
            if not raw_text:
                logger.error(f"No salary data returned for emp_id={emp_id}, {year}-{month:02d}")
                return None

            fields = _first_block(raw_text).split("|")

            # Validate field count
            if len(fields) < 45:
                logger.error(
                    f"Dữ liệu lương không đủ trường: "
                    f"nhận {len(fields)} trường, cần ít nhất 45 trường. "
                    f"emp_id={emp_id}, {year}-{month:02d}"
                )
                return None

            # Parse and structure the response
            structured_data = _parse_salary_response(fields)

            logger.info(
                f"Successfully fetched salary for emp_id={emp_id}, {year}-{month:02d}. "
                f"Net salary: {structured_data['summary']['thuc_linh']:,.0f} VND"
            )

            return structured_data

        except Exception as e:
            logger.error(f"Error fetching salary data: {e}", exc_info=True)
            return None
