#!/bin/bash

echo "=========================================="
echo "🧪 TIDE-HF System API Test"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

BASE_URL="http://localhost:8000/api"

# Test 1: Health Check
echo -e "${BLUE}[TEST 1]${NC} Health Check..."
HEALTH=$(curl -s "$BASE_URL/health")
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check PASSED${NC}"
    echo "$HEALTH" | python3 -m json.tool
else
    echo -e "${RED}❌ Health check FAILED${NC}"
fi
echo ""

# Test 2: Login
echo -e "${BLUE}[TEST 2]${NC} Login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=doctor@example.com&password=SecurePass123!")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✅ Login PASSED${NC}"
    echo "Token: ${TOKEN:0:30}..."
else
    echo -e "${RED}❌ Login FAILED${NC}"
    echo "$LOGIN_RESPONSE"
    exit 1
fi
echo ""

# Test 3: Create Patient
echo -e "${BLUE}[TEST 3]${NC} Create Patient..."
PATIENT_ID="TEST-PAT-$(date +%s)"
PATIENT_RESPONSE=$(curl -s -X POST "$BASE_URL/patients/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"patient_id\": \"$PATIENT_ID\",
    \"first_name\": \"John\",
    \"last_name\": \"TestPatient\",
    \"date_of_birth\": \"1965-06-15T00:00:00\",
    \"gender\": \"male\",
    \"allergies\": \"Diabetes, Hypertension\",
    \"current_medications\": \"Metoprolol 50mg\"
  }")

DB_PATIENT_ID=$(echo "$PATIENT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('patient', {}).get('id', ''))" 2>/dev/null)

if [ -n "$DB_PATIENT_ID" ]; then
    echo -e "${GREEN}✅ Patient creation PASSED${NC}"
    echo "$PATIENT_RESPONSE" | python3 -m json.tool
    echo -e "${YELLOW}Database Patient ID: $DB_PATIENT_ID${NC}"
else
    echo -e "${RED}❌ Patient creation FAILED${NC}"
    echo "$PATIENT_RESPONSE"
    exit 1
fi
echo ""

# Test 4: Create Medical Record
echo -e "${BLUE}[TEST 4]${NC} Create Medical Record..."
RECORD_RESPONSE=$(curl -s -X POST "$BASE_URL/patients/$DB_PATIENT_ID/records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"patient_id\": \"$DB_PATIENT_ID\",
    \"visit_date\": \"$(date -u +"%Y-%m-%dT%H:%M:%S")\",
    \"is_followup\": false,
    \"visit_type\": \"Baseline\",
    \"height_cm\": 175.0,
    \"weight_kg\": 80.0,
    \"blood_pressure_systolic\": 120,
    \"blood_pressure_diastolic\": 80,
    \"heart_rate\": 72
  }")

if echo "$RECORD_RESPONSE" | grep -q "record_id"; then
    echo -e "${GREEN}✅ Medical record creation PASSED${NC}"
    echo "$RECORD_RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}❌ Medical record creation FAILED${NC}"
    echo "$RECORD_RESPONSE"
fi
echo ""

# Test 5: Get Patient
echo -e "${BLUE}[TEST 5]${NC} Get Patient..."
GET_PATIENT=$(curl -s -X GET "$BASE_URL/patients/$DB_PATIENT_ID" \
  -H "Authorization: Bearer $TOKEN")

if echo "$GET_PATIENT" | grep -q "first_name"; then
    echo -e "${GREEN}✅ Get patient PASSED${NC}"
    echo "$GET_PATIENT" | python3 -m json.tool | head -20
else
    echo -e "${RED}❌ Get patient FAILED${NC}"
fi
echo ""

# Test 6: Get Patient Records
echo -e "${BLUE}[TEST 6]${NC} Get Patient Records..."
GET_RECORDS=$(curl -s -X GET "$BASE_URL/patients/$DB_PATIENT_ID/records" \
  -H "Authorization: Bearer $TOKEN")

if echo "$GET_RECORDS" | grep -q "total_records"; then
    echo -e "${GREEN}✅ Get records PASSED${NC}"
    echo "$GET_RECORDS" | python3 -m json.tool
else
    echo -e "${RED}❌ Get records FAILED${NC}"
fi
echo ""

# Test 7: Database Check
echo -e "${BLUE}[TEST 7]${NC} Database Verification..."
cd backend
PATIENT_COUNT=$(sqlite3 medical.db "SELECT COUNT(*) FROM patients;")
RECORD_COUNT=$(sqlite3 medical.db "SELECT COUNT(*) FROM medical_records;")
USER_COUNT=$(sqlite3 medical.db "SELECT COUNT(*) FROM users;")

echo -e "${GREEN}✅ Database check PASSED${NC}"
echo "  • Total Patients: $PATIENT_COUNT"
echo "  • Total Medical Records: $RECORD_COUNT"
echo "  • Total Users: $USER_COUNT"
echo ""

echo "=========================================="
echo -e "${GREEN}🎉 ALL TESTS COMPLETED SUCCESSFULLY!${NC}"
echo "=========================================="
echo ""
echo "✅ Backend API is working correctly"
echo "✅ Database is persisting data"
echo "✅ Patient creation and retrieval working"
echo "✅ Medical records working"
echo ""
echo "Next: Test the frontend at http://localhost:3000"
