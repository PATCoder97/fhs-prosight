"""
API Key System Test Script

This script tests the entire API key authentication flow:
1. Create API key (requires admin JWT token)
2. Test API key authentication on import endpoints
3. Verify employee dormitory auto-update
4. Test API key management (list, revoke)

Usage:
    python test_api_key_system.py --admin-token YOUR_ADMIN_JWT_TOKEN
"""

import requests
import json
import sys
import argparse
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def log_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def log_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def log_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def test_create_api_key(admin_token):
    """Test 1: Create a new API key"""
    print("\n" + "="*60)
    print("TEST 1: Create API Key")
    print("="*60)

    url = f"{BASE_URL}/api-keys"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    data = {
        "name": "Test API Key",
        "description": "Automated test key",
        "scopes": ["evaluations:import", "dormitory-bills:import"],
        "expires_days": 30
    }

    log_info("Creating API key...")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        api_key = result.get("api_key")
        key_info = result.get("key_info")

        log_success(f"API key created successfully!")
        log_info(f"Key ID: {key_info['id'][:16]}...")
        log_info(f"Key Prefix: {key_info['key_prefix']}")
        log_info(f"Scopes: {key_info['scopes']}")

        return api_key, key_info['id']
    else:
        log_error(f"Failed to create API key: {response.status_code}")
        log_error(f"Response: {response.text}")
        return None, None

def test_list_api_keys(admin_token):
    """Test 2: List all API keys"""
    print("\n" + "="*60)
    print("TEST 2: List API Keys")
    print("="*60)

    url = f"{BASE_URL}/api-keys"
    headers = {"Authorization": f"Bearer {admin_token}"}

    log_info("Fetching API keys list...")
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        result = response.json()
        total = result.get("total", 0)
        keys = result.get("keys", [])

        log_success(f"Found {total} API key(s)")
        for key in keys:
            log_info(f"  - {key['name']} ({key['key_prefix']})")

        return True
    else:
        log_error(f"Failed to list API keys: {response.status_code}")
        return False

def test_import_dormitory_bills(api_key):
    """Test 3: Import dormitory bills with API key"""
    print("\n" + "="*60)
    print("TEST 3: Import Dormitory Bills with API Key")
    print("="*60)

    url = f"{BASE_URL}/dormitory-bills/import"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    # Sample test data
    data = {
        "bills": [
            {
                "employee_id": "VNW0018983",  # Use existing employee ID
                "term_code": "TEST001",
                "dorm_code": "TEST-A01",
                "factory_location": "Test Location",
                "elec_last_index": 1000.0,
                "elec_curr_index": 1250.0,
                "elec_usage": 250.0,
                "elec_amount": 1250000,
                "water_last_index": 500.0,
                "water_curr_index": 565.0,
                "water_usage": 65.0,
                "water_amount": 325000,
                "shared_fee": 100000,
                "management_fee": 200000,
                "total_amount": 1875000
            }
        ]
    }

    log_info("Importing dormitory bills...")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        summary = result.get("summary", {})

        log_success("Import successful!")
        log_info(f"Total records: {summary.get('total_records')}")
        log_info(f"Created: {summary.get('created')}")
        log_info(f"Updated: {summary.get('updated')}")
        log_info(f"Errors: {summary.get('errors')}")
        log_info(f"Employees updated: {summary.get('employees_updated')}")

        return True
    else:
        log_error(f"Import failed: {response.status_code}")
        log_error(f"Response: {response.text}")
        return False

def test_invalid_api_key():
    """Test 4: Test with invalid API key"""
    print("\n" + "="*60)
    print("TEST 4: Test Invalid API Key")
    print("="*60)

    url = f"{BASE_URL}/dormitory-bills/import"
    headers = {
        "X-API-Key": "fhs_invalid_key_12345",
        "Content-Type": "application/json"
    }
    data = {"bills": []}

    log_info("Testing with invalid API key...")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 401:
        log_success("Correctly rejected invalid API key (401)")
        return True
    else:
        log_error(f"Unexpected status code: {response.status_code}")
        return False

def test_missing_api_key():
    """Test 5: Test without API key"""
    print("\n" + "="*60)
    print("TEST 5: Test Missing API Key")
    print("="*60)

    url = f"{BASE_URL}/dormitory-bills/import"
    headers = {"Content-Type": "application/json"}
    data = {"bills": []}

    log_info("Testing without API key...")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 401:
        log_success("Correctly rejected missing API key (401)")
        return True
    else:
        log_error(f"Unexpected status code: {response.status_code}")
        return False

def test_revoke_api_key(admin_token, key_id):
    """Test 6: Revoke API key"""
    print("\n" + "="*60)
    print("TEST 6: Revoke API Key")
    print("="*60)

    url = f"{BASE_URL}/api-keys/{key_id}"
    headers = {"Authorization": f"Bearer {admin_token}"}

    log_info(f"Revoking API key {key_id[:16]}...")
    response = requests.delete(url, headers=headers)

    if response.status_code == 200:
        log_success("API key revoked successfully!")
        return True
    else:
        log_error(f"Failed to revoke API key: {response.status_code}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test API Key Authentication System')
    parser.add_argument('--admin-token', required=True, help='Admin JWT token')
    parser.add_argument('--base-url', default=BASE_URL, help='Base API URL')
    args = parser.parse_args()

    global BASE_URL
    BASE_URL = args.base_url

    print("\n" + "="*60)
    print("🚀 API Key System Test Suite")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {
        "passed": 0,
        "failed": 0
    }

    # Test 1: Create API key
    api_key, key_id = test_create_api_key(args.admin_token)
    if api_key:
        results["passed"] += 1
    else:
        results["failed"] += 1
        log_error("Cannot proceed without API key. Exiting...")
        sys.exit(1)

    # Test 2: List API keys
    if test_list_api_keys(args.admin_token):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 3: Import dormitory bills
    if test_import_dormitory_bills(api_key):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 4: Invalid API key
    if test_invalid_api_key():
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 5: Missing API key
    if test_missing_api_key():
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 6: Revoke API key
    if test_revoke_api_key(args.admin_token, key_id):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"Total Tests: {results['passed'] + results['failed']}")
    print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.END}")
    print(f"{Colors.RED}Failed: {results['failed']}{Colors.END}")

    if results["failed"] == 0:
        print(f"\n{Colors.GREEN}🎉 All tests passed!{Colors.END}")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}❌ Some tests failed. Please review.{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
