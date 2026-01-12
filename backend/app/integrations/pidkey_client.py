"""
PIDKey.com API Client

HTTP client for validating Microsoft product keys via PIDKey.com API.
Handles key formatting, API communication, retry logic, and error handling.
"""

import httpx
import logging
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class PIDKeyClient:
    """Client for PIDKey.com API - validates Microsoft product keys."""

    def __init__(self, api_key: str, base_url: str = "https://pidkey.com/ajax/pidms_api"):
        """
        Initialize PIDKey.com API client.

        Args:
            api_key: PIDKey.com API key for authentication
            base_url: Base URL for PIDKey.com API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = 30.0
        self.headers = {
            "User-Agent": "FHS-ProSight/1.0",
            "Accept": "application/json",
        }

    def _format_keys(self, keys: List[str]) -> str:
        """
        Normalize keys to \\r\\n-separated format without dashes.

        Args:
            keys: List of product keys (with or without dashes)

        Returns:
            Newline-separated string of normalized keys

        Example:
            ["6NRGD-KHFCF-Y4TF7", "8NFMQ-FTF43"] -> "6NRGDKHFCFY4TF7\\r\\n8NFMQFTF43"
        """
        normalized = []
        for key in keys:
            # Remove dashes, spaces, and any whitespace
            clean_key = key.replace("-", "").replace(" ", "").strip()
            if clean_key:  # Only add non-empty keys
                normalized.append(clean_key)

        # Join with \r\n as required by PIDKey.com API
        return "\\r\\n".join(normalized)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    async def check_keys(self, keys: List[str]) -> List[Dict]:
        """
        Check product keys against PIDKey.com API.

        Makes HTTP GET request to PIDKey.com with formatted keys and returns
        validation results including remaining activations and blocked status.

        Args:
            keys: List of product keys (with or without dashes)

        Returns:
            List of dicts with key information from API, each containing:
            - keyname: Key without dashes
            - keyname_with_dash: Key with dashes
            - prd: Product code
            - remaining: Activation count
            - blocked: Block status (-1=not blocked)
            - And 9 additional fields

        Raises:
            httpx.HTTPStatusError: If API returns error status
            httpx.TimeoutException: If request times out (with retry)
            httpx.NetworkError: If network issues occur (with retry)

        Example:
            >>> client = PIDKeyClient(api_key="xxx")
            >>> results = await client.check_keys(["6NRGD-KHFCF-Y4TF7"])
            >>> results[0]["remaining"]
            2185
        """
        if not keys:
            logger.warning("check_keys called with empty keys list")
            return []

        formatted_keys = self._format_keys(keys)

        params = {
            "keys": formatted_keys,
            "justgetdescription": "0",
            "apikey": self.api_key
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(
                    f"Calling PIDKey.com API with {len(keys)} keys "
                    f"(API key: {self.api_key[:8]}***)"
                )

                resp = await client.get(self.base_url, params=params, headers=self.headers)
                resp.raise_for_status()

                data = resp.json()

                logger.info(f"PIDKey.com API returned {len(data)} results")
                logger.debug(f"API response: {data}")

                return data

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error(
                f"PIDKey.com API HTTP error: {status_code} - {e.response.text[:200]}"
            )

            # Provide helpful error messages
            if status_code == 401:
                raise ValueError("Invalid PIDKey.com API key") from e
            elif status_code == 429:
                raise ValueError("PIDKey.com API rate limit exceeded") from e
            else:
                raise

        except httpx.TimeoutException as e:
            logger.error(f"PIDKey.com API timeout after {self.timeout}s: {e}")
            raise

        except httpx.NetworkError as e:
            logger.error(f"PIDKey.com API network error: {e}")
            raise

        except Exception as e:
            logger.error(f"PIDKey.com API unexpected error: {e}", exc_info=True)
            raise
