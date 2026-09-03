#!/bin/bash

# TIDE-HF Phase 2 - Database Viewer Script

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  📊 TIDE-HF Database Viewer                               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

DB_FILE="backend/medical.db"

if [ ! -f "$DB_FILE" ]; then
    echo "❌ Database not found at: $DB_FILE"
    echo "   Start the backend first to create the database."
    exit 1
fi

echo "✅ Database found: $DB_FILE"
echo ""

# Function to display a table
show_table() {
    local table_name=$1
    local title=$2
    local query=$3

    echo "═══════════════════════════════════════════════════════════"
    echo "$title"
    echo "═══════════════════════════════════════════════════════════"

    local count=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM $table_name;")
    echo "Total records: $count"
    echo ""

    if [ "$count" -gt 0 ]; then
        sqlite3 -header -column "$DB_FILE" "$query"
    else
        echo "  No records found."
    fi
    echo ""
}

# Show statistics
echo "📊 DATABASE STATISTICS"
echo "─────────────────────────────────────────────────────────────"
echo "  Users:           $(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM users;')"
echo "  Patients:        $(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM patients;')"
echo "  Medical Records: $(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM medical_records;')"
echo "  Uploaded Files:  $(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM uploaded_files;')"
echo "  Lab Data:        $(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM lab_data;')"
echo "  Wearable Data:   $(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM wearable_data;')"
echo ""

# Show tables
show_table "users" "👥 USERS" \
    "SELECT substr(id, 1, 8) as id, email, full_name, role, datetime(created_at) as created
     FROM users
     ORDER BY created_at DESC
     LIMIT 10;"

show_table "patients" "🏥 PATIENTS" \
    "SELECT substr(id, 1, 8) as id, patient_id, first_name, last_name, gender,
            date(date_of_birth) as dob, datetime(created_at) as created
     FROM patients
     ORDER BY created_at DESC
     LIMIT 10;"

show_table "medical_records" "📋 MEDICAL RECORDS" \
    "SELECT substr(id, 1, 8) as id, substr(patient_id, 1, 8) as patient,
            visit_type, is_followup,
            height_cm, weight_kg, round(bmi, 1) as bmi,
            datetime(visit_date) as visit
     FROM medical_records
     ORDER BY visit_date DESC
     LIMIT 10;"

show_table "uploaded_files" "📁 UPLOADED FILES" \
    "SELECT substr(id, 1, 8) as id, file_name, file_type,
            round(file_size/1024.0, 1) as size_kb,
            datetime(uploaded_at) as uploaded
     FROM uploaded_files
     ORDER BY uploaded_at DESC
     LIMIT 10;"

echo "═══════════════════════════════════════════════════════════"
echo "💡 TIPS:"
echo "═══════════════════════════════════════════════════════════"
echo "  • Run this script anytime: ./view_data.sh"
echo "  • Direct access: sqlite3 backend/medical.db"
echo "  • GUI tool: Download DB Browser for SQLite"
echo "  • API access: http://localhost:8000/api/docs"
echo ""
echo "🔍 To query specific data:"
echo "  sqlite3 backend/medical.db \"SELECT * FROM patients;\""
echo ""
