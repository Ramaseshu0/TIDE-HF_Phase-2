export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'admin' | 'doctor' | 'viewer';
  organization?: string;
  specialty?: string;
  mfa_enabled: boolean;
}

export interface Patient {
  id: string;
  patient_id: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  date_of_birth: string;
  gender: 'male' | 'female' | 'other';
  email?: string;
  phone?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  address?: {
    line1?: string;
    line2?: string;
    city?: string;
    state?: string;
    zip_code?: string;
    country?: string;
  };
  blood_type?: string;
  allergies?: string;
  chronic_conditions?: string;
  current_medications?: string;
  created_at: string;
  updated_at: string;
}

export interface MedicalRecord {
  id: string;
  patient_id: string;
  visit_date: string;
  is_followup: boolean;
  followup_of?: string;
  visit_type?: string;
  chief_complaint?: string;
  present_illness?: string;
  diagnosis?: string;
  treatment_plan?: string;
  notes?: string;
  vitals?: {
    height_cm?: number;
    weight_kg?: number;
    bmi?: number;
    blood_pressure?: string;
    heart_rate?: number;
    temperature_celsius?: number;
    respiratory_rate?: number;
    oxygen_saturation?: number;
  };
}

export interface UploadedFile {
  file_id: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  is_dicom: boolean;
  uploaded_at: string;
  uploaded_by: string;
}

export interface OCRData {
  patient_name?: string;
  date_of_birth?: string;
  gender?: string;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  heart_rate?: number;
  temperature_celsius?: number;
  weight_kg?: number;
  height_cm?: number;
  diagnosis?: string;
  blood_type?: string;
  allergies?: string;
  current_medications?: string;
}

export interface WearableDevice {
  type: string;
  name: string;
  description: string;
  data_available: string[];
  requires_oauth: boolean;
  status: string;
}

export interface WearableData {
  id: string;
  wearable_type: string;
  device_name?: string;
  recorded_at: string;
  heart_rate?: number;
  steps?: number;
  calories?: number;
  sleep_hours?: number;
  oxygen_saturation?: number;
  blood_pressure?: string;
  synced_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  mfa_token?: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  role?: string;
  organization?: string;
  license_number?: string;
  specialty?: string;
}
