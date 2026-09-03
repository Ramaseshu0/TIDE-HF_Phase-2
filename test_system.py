#!/usr/bin/env python3
"""
Comprehensive System Test - TIDE-HF Phase 2
Tests patient creation, file upload, and data persistence
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:8000/api"

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_test(message):
    print(f"{BLUE}[TEST]{RESET} {message}")

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def print_info(message):
    print(f"{YELLOW}ℹ️  {message}{RESET}")

# Test data
TEST_EMAIL = "test.doctor@example.com"
TEST_PASSWORD = "TestPass123!"

def test_health_check():
    """Test 1: Health Check"""
    print_test("Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed: {data}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False

def test_login():
    """Test 2: Login with existing test account"""
    print_test("Testing login...")
    try:
        # Try logging in with existing test account
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": "doctor@example.com", "password": "SecurePass123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print_success(f"Login successful! Token: {token[:20]}...")
            return token
        else:
            print_error(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Login error: {e}")
        return None

def test_create_patient(token):
    """Test 3: Create Patient"""
    print_test("Testing patient creation...")
    try:
        patient_data = {
            "patient_id": f"TEST-PAT-{int(time.time())}",
            "first_name": "Test",
            "last_name": "Patient",
            "date_of_birth": "1965-01-01T00:00:00",
            "gender": "male",
            "allergies": "Diabetes, Hypertension",
            "current_medications": "Metoprolol 50mg, Lisinopril 10mg"
        }

        response = requests.post(
            f"{BASE_URL}/patients/",
            json=patient_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 201:
            data = response.json()
            patient_id = data.get("patient_id")
            print_success(f"Patient created! ID: {patient_id}")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            return patient_id
        else:
            print_error(f"Patient creation failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Patient creation error: {e}")
        return None

def test_create_medical_record(token, patient_id):
    """Test 4: Create Medical Record"""
    print_test("Testing medical record creation...")
    try:
        record_data = {
            "patient_id": patient_id,
            "visit_date": datetime.utcnow().isoformat(),
            "is_followup": False,
            "visit_type": "Baseline",
            "height_cm": 175.0,
            "weight_kg": 80.0,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "heart_rate": 72
        }

        response = requests.post(
            f"{BASE_URL}/patients/{patient_id}/records",
            json=record_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 201:
            data = response.json()
            record_id = data.get("record_id")
            print_success(f"Medical record created! ID: {record_id}")
            return record_id
        else:
            print_error(f"Medical record creation failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Medical record error: {e}")
        return None

def test_get_patient(token, patient_id):
    """Test 5: Retrieve Patient"""
    print_test("Testing patient retrieval...")
    try:
        response = requests.get(
            f"{BASE_URL}/patients/{patient_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            data = response.json()
            print_success("Patient retrieved successfully!")
            print_info(f"Patient: {data.get('first_name')} {data.get('last_name')}")
            print_info(f"Gender: {data.get('gender')}, DOB: {data.get('date_of_birth')}")
            return True
        else:
            print_error(f"Patient retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Patient retrieval error: {e}")
        return False

def test_get_patient_records(token, patient_id):
    """Test 6: Retrieve Patient Records"""
    print_test("Testing patient records retrieval...")
    try:
        response = requests.get(
            f"{BASE_URL}/patients/{patient_id}/records",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            data = response.json()
            record_count = data.get("total_records", 0)
            print_success(f"Records retrieved! Total: {record_count}")
            if record_count > 0:
                print_info(f"Latest visit: {data['records'][0]['visit_date']}")
                print_info(f"Vitals: {data['records'][0]['vitals']}")
            return True
        else:
            print_error(f"Records retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Records retrieval error: {e}")
        return False

def check_database():
    """Test 7: Check Database"""
    print_test("Checking database contents...")
    try:
        import sqlite3
        conn = sqlite3.connect('medical.db')
        cursor = conn.cursor()

        # Count patients
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        print_success(f"Patients in database: {patient_count}")

        # Count medical records
        cursor.execute("SELECT COUNT(*) FROM medical_records")
        record_count = cursor.fetchone()[0]
        print_success(f"Medical records in database: {record_count}")

        # Count users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print_success(f"Users in database: {user_count}")

        # Show latest patient
        cursor.execute("SELECT patient_id, first_name, last_name, gender FROM patients ORDER BY created_at DESC LIMIT 1")
        latest = cursor.fetchone()
        if latest:
            print_info(f"Latest patient: {latest[0]} - {latest[1]} {latest[2]} ({latest[3]})")

        conn.close()
        return True
    except Exception as e:
        print_error(f"Database check error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print(f"{BLUE}🧪 TIDE-HF Phase 2 - System Test Suite{RESET}")
    print("="*60 + "\n")

    results = {}

    # Test 1: Health Check
    results['health'] = test_health_check()
    print()

    # Test 2: Login
    token = test_login()
    results['login'] = token is not None
    print()

    if not token:
        print_error("Cannot proceed without authentication token")
        return

    # Test 3: Create Patient
    patient_id = test_create_patient(token)
    results['create_patient'] = patient_id is not None
    print()

    if not patient_id:
        print_error("Cannot proceed without patient ID")
        return

    # Test 4: Create Medical Record
    record_id = test_create_medical_record(token, patient_id)
    results['create_record'] = record_id is not None
    print()

    # Test 5: Get Patient
    results['get_patient'] = test_get_patient(token, patient_id)
    print()

    # Test 6: Get Patient Records
    results['get_records'] = test_get_patient_records(token, patient_id)
    print()

    # Test 7: Check Database
    results['database'] = check_database()
    print()

    # Summary
    print("="*60)
    print(f"{BLUE}📊 Test Summary{RESET}")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = f"{GREEN}✅ PASSED{RESET}" if result else f"{RED}❌ FAILED{RESET}"
        print(f"{test_name.replace('_', ' ').title()}: {status}")

    print("\n" + "="*60)
    if passed == total:
        print(f"{GREEN}🎉 ALL TESTS PASSED! ({passed}/{total}){RESET}")
    else:
        print(f"{YELLOW}⚠️  SOME TESTS FAILED ({passed}/{total}){RESET}")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_all_tests()
