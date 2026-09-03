import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class APIService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await this.client.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async register(data: any) {
    const response = await this.client.post('/auth/register', data);
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  async setupMFA() {
    const response = await this.client.post('/auth/mfa/setup');
    return response.data;
  }

  async verifyMFA(token: string) {
    const response = await this.client.post('/auth/mfa/verify', { token });
    return response.data;
  }

  // Patient endpoints
  async searchPatients(query: string) {
    const response = await this.client.get(`/patients/search?q=${query}`);
    return response.data;
  }

  async getPatient(patientId: string) {
    const response = await this.client.get(`/patients/${patientId}`);
    return response.data;
  }

  async createPatient(data: any) {
    const response = await this.client.post('/patients/', data);
    return response.data;
  }

  async updatePatient(patientId: string, data: any) {
    const response = await this.client.put(`/patients/${patientId}`, data);
    return response.data;
  }

  async getPatientRecords(patientId: string) {
    const response = await this.client.get(`/patients/${patientId}/records`);
    return response.data;
  }

  async createMedicalRecord(patientId: string, data: any) {
    const response = await this.client.post(`/patients/${patientId}/records`, data);
    return response.data;
  }

  // Upload endpoints
  async uploadFile(file: File, patientId: string, medicalRecordId?: string, performOCR?: boolean) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('patient_id', patientId);
    if (medicalRecordId) {
      formData.append('medical_record_id', medicalRecordId);
    }
    if (performOCR !== undefined) {
      formData.append('perform_ocr', String(performOCR));
    }

    const response = await this.client.post('/upload/file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async uploadEHRDocument(file: File, patientId: string, medicalRecordId?: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('patient_id', patientId);
    if (medicalRecordId) {
      formData.append('medical_record_id', medicalRecordId);
    }

    const response = await this.client.post('/upload/ehr-document', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async uploadMultipleFiles(files: File[], patientId: string, medicalRecordId?: string) {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    formData.append('patient_id', patientId);
    if (medicalRecordId) {
      formData.append('medical_record_id', medicalRecordId);
    }

    const response = await this.client.post('/upload/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async listPatientFiles(patientId: string, fileType?: string) {
    let url = `/upload/patient/${patientId}/files`;
    if (fileType) {
      url += `?file_type=${fileType}`;
    }
    const response = await this.client.get(url);
    return response.data;
  }

  // Viewer endpoints
  async getFileInfo(fileId: string) {
    const response = await this.client.get(`/viewer/file/${fileId}`);
    return response.data;
  }

  async downloadFile(fileId: string) {
    const response = await this.client.get(`/viewer/file/${fileId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async getDicomImage(fileId: string) {
    const response = await this.client.get(`/viewer/file/${fileId}/dicom-image`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async getDicomThumbnail(fileId: string) {
    const response = await this.client.get(`/viewer/file/${fileId}/dicom-thumbnail`);
    return response.data;
  }

  // Wearables endpoints
  async getSupportedDevices() {
    const response = await this.client.get('/wearables/supported-devices');
    return response.data;
  }

  async connectWearable(patientId: string, wearableType: string, deviceName?: string) {
    const response = await this.client.post('/wearables/connect', {
      patient_id: patientId,
      wearable_type: wearableType,
      device_name: deviceName,
    });
    return response.data;
  }

  async getPatientWearableData(patientId: string, wearableType?: string) {
    let url = `/wearables/patient/${patientId}/data`;
    if (wearableType) {
      url += `?wearable_type=${wearableType}`;
    }
    const response = await this.client.get(url);
    return response.data;
  }

  async getPatientDevices(patientId: string) {
    const response = await this.client.get(`/wearables/patient/${patientId}/devices`);
    return response.data;
  }
}

export default new APIService();
