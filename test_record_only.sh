#!/bin/bash

BASE_URL="http://localhost:8000/api"

# Login
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=doctor@example.com&password=SecurePass123!" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

# Get existing patient ID
PATIENT_ID=$(sqlite3 backend/medical.db "SELECT id FROM patients ORDER BY created_at DESC LIMIT 1;")

echo "Testing medical record creation..."
echo "Patient ID: $PATIENT_ID"
echo ""

# Try to create medical record with simpler data
curl -v -X POST "$BASE_URL/patients/$PATIENT_ID/records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"patient_id\": \"$PATIENT_ID\",
    \"is_followup\": false,
    \"visit_type\": \"Baseline\",
    \"height_cm\": 175.0,
    \"weight_kg\": 80.0
  }"

echo ""
