import httpx
import logging
from typing import Optional, Dict, List
import json

logger = logging.getLogger(__name__)


class FHSCovidClient:
    """Client for FHS COVID API - fetches employee vaccination info with bearer token"""

    def __init__(self):
        self.base_url = "https://www.fhs.com.tw/fhs_covid_api/api/reportVaccines/detail"
        self.timeout = 30.0

    async def _fetch_json(self, params: dict, token: str) -> Optional[Dict]:
        """Internal helper to fetch JSON from API with bearer token

        Returns None if request fails (no exceptions raised)
        """
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "FHSCovidClient/1.0",
            "Accept": "application/json; charset=utf-8",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(self.base_url, params=params, headers=headers)
                resp.raise_for_status()
                resp.encoding = "utf-8"  # Force UTF-8 for Chinese/Vietnamese text
                return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error(f"COVID API unauthorized: Invalid or expired token")
            else:
                logger.error(f"COVID API HTTP error: Status {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"COVID API request error: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"COVID API invalid JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"COVID API unexpected error: {e}")
            return None

    def _parse_user_data(self, data: Dict) -> Optional[Dict]:
        """Parse user data from COVID API JSON response

        COVID API returns a nested structure with 'user' key containing the employee data.
        Expected fields in 'user': userName, fullName, departmentCode, companyCode, phone, sex,
                                   identityNumber, birthday, nationality
        """
        try:
            if not data:
                return None

            # Log the raw data for debugging
            logger.info(f"COVID API raw response keys: {list(data.keys())}")

            # Extract user data from nested structure
            user_data = data.get("user")
            if not user_data:
                logger.error(f"COVID API response missing 'user' key. Available keys: {list(data.keys())}")
                return None

            logger.info(f"COVID API user data: {user_data}")

            # Map to standardized format
            parsed_data = {
                "employee_id": user_data.get("userName"),  # VNW0014732
                "name_tw": user_data.get("fullName"),  # Chinese name (潘英俊)
                "department_code": user_data.get("departmentCode"),  # 7820
                "phone1": user_data.get("phone"),
                "sex": user_data.get("sex"),  # 男/女
                "identity_number": user_data.get("identityNumber"),  # CMND/CCCD
                "dob": user_data.get("birthday"),  # ISO date format
                "nationality": user_data.get("nationality"),  # VN
            }

            # Log parsed data
            logger.info(f"COVID API parsed data: {parsed_data}")

            return parsed_data
        except Exception as e:
            logger.error(f"Failed to parse COVID user data: {e}")
            return None

    async def get_user_info(self, emp_id: int, token: str) -> Optional[Dict]:
        """Fetch single employee information from COVID API

        Args:
            emp_id: Employee ID (e.g., 6204)
            token: Bearer token for authentication

        Returns:
            Dict with employee data, or None if not found/error
        """
        # Convert to VNW00XXXXX format
        emp_id_str = f"VNW00{emp_id:05d}"

        # Build query params
        params = {
            "isFHS": "true",
            "isFull": "false",
            "userName": emp_id_str,
        }

        # Call API
        data = await self._fetch_json(params, token)

        if not data:
            logger.info(f"No data from COVID API for {emp_id_str}")
            return None

        # Parse response
        return self._parse_user_data(data)

    async def bulk_get_users(self, from_id: int, to_id: int, token: str) -> List[Optional[Dict]]:
        """Fetch multiple employees from COVID API

        Args:
            from_id: Starting employee ID (e.g., 6200)
            to_id: Ending employee ID (e.g., 6210)
            token: Bearer token (same for all requests)

        Returns:
            List of employee dicts (None for failed/not found IDs)
        """
        results = []

        for emp_id in range(from_id, to_id + 1):
            user_data = await self.get_user_info(emp_id, token)
            results.append(user_data)

        return results
