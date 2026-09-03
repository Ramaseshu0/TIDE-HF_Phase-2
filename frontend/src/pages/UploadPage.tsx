import { useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Image as ImageIcon, Activity, X, Check, User, Heart, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../services/api';

interface UploadedFile {
  file: File;
  name: string;
  size: number;
  type: string;
  modality?: string;
}

interface PatientFormData {
  patientName: string;
  patientId: string;
  age: string;
  sex: string;
  height: string;
  weight: string;
  visitType: 'baseline' | 'followup';
  conditions: string[];
  medications: string;
}

export default function UploadPage() {
  const [selectedTab, setSelectedTab] = useState<'patient' | 'ehr' | 'image' | 'wearable'>('patient');
  const [ehrFiles, setEhrFiles] = useState<UploadedFile[]>([]);
  const [imageFiles, setImageFiles] = useState<UploadedFile[]>([]);
  const [selectedModality, setSelectedModality] = useState('Echo');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [savedPatientId, setSavedPatientId] = useState<string | null>(null);

  // Patient form data
  const [patientForm, setPatientForm] = useState<PatientFormData>({
    patientName: '',
    patientId: '',
    age: '',
    sex: '',
    height: '',
    weight: '',
    visitType: 'baseline',
    conditions: [],
    medications: ''
  });

  const handleInputChange = (field: keyof PatientFormData, value: string) => {
    setPatientForm(prev => ({ ...prev, [field]: value }));
  };

  const toggleCondition = (condition: string) => {
    setPatientForm(prev => ({
      ...prev,
      conditions: prev.conditions.includes(condition)
        ? prev.conditions.filter(c => c !== condition)
        : [...prev.conditions, condition]
    }));
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>, type: 'ehr' | 'image') => {
    const files = event.target.files;
    if (!files) return;

    const newFiles: UploadedFile[] = Array.from(files).map(file => ({
      file: file,
      name: file.name,
      size: file.size,
      type: file.type,
      modality: type === 'image' ? selectedModality : undefined
    }));

    if (type === 'ehr') {
      setEhrFiles(prev => [...prev, ...newFiles]);
      toast.success(`${newFiles.length} file(s) added`);
    } else {
      setImageFiles(prev => [...prev, ...newFiles]);
      toast.success(`${newFiles.length} image(s) added with ${selectedModality} tag`);
    }
  };

  const removeFile = (index: number, type: 'ehr' | 'image') => {
    if (type === 'ehr') {
      setEhrFiles(prev => prev.filter((_, i) => i !== index));
    } else {
      setImageFiles(prev => prev.filter((_, i) => i !== index));
    }
    toast.success('File removed');
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const handleSavePatient = async () => {
    // Validation
    if (!patientForm.patientName.trim()) {
      toast.error('Please enter patient name');
      return;
    }
    if (!patientForm.age || !patientForm.sex) {
      toast.error('Please fill in age and sex');
      return;
    }

    setIsSubmitting(true);
    const loadingToast = toast.loading('Saving patient information...');

    try {
      // Split name into first and last
      const nameParts = patientForm.patientName.trim().split(' ');
      const firstName = nameParts[0];
      const lastName = nameParts.slice(1).join(' ') || nameParts[0];

      // Create patient
      const patientData = {
        patient_id: patientForm.patientId || `PAT-${Date.now()}`,
        first_name: firstName,
        last_name: lastName,
        date_of_birth: new Date(new Date().getFullYear() - parseInt(patientForm.age), 0, 1).toISOString(),
        gender: patientForm.sex,
        allergies: patientForm.conditions.join(', '),
        current_medications: patientForm.medications
      };

      console.log('Creating patient with data:', patientData);
      const response = await api.createPatient(patientData);
      console.log('Patient created successfully:', response);

      const createdPatientId = response.patient.id;
      setSavedPatientId(createdPatientId);

      // If we have height and weight, create a medical record
      if (patientForm.height && patientForm.weight) {
        const recordData = {
          patient_id: createdPatientId,
          visit_date: new Date().toISOString(),
          is_followup: patientForm.visitType === 'followup',
          visit_type: patientForm.visitType === 'baseline' ? 'Baseline' : 'Follow-up',
          height_cm: parseFloat(patientForm.height),
          weight_kg: parseFloat(patientForm.weight)
        };

        console.log('Creating medical record with data:', recordData);
        await api.createMedicalRecord(createdPatientId, recordData);
        console.log('Medical record created successfully');
      }

      toast.success('✅ Patient information saved to database!', { id: loadingToast, duration: 3000 });

      // Reset form
      setPatientForm({
        patientName: '',
        patientId: '',
        age: '',
        sex: '',
        height: '',
        weight: '',
        visitType: 'baseline',
        conditions: [],
        medications: ''
      });
    } catch (error: any) {
      console.error('Error saving patient:', error);
      toast.error(error.response?.data?.detail || 'Failed to save patient information', { id: loadingToast });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleProcessEHR = async () => {
    if (ehrFiles.length === 0) {
      toast.error('Please upload at least one file');
      return;
    }

    if (!savedPatientId) {
      toast.error('Please save patient information first');
      return;
    }

    setIsSubmitting(true);
    const loadingToast = toast.loading('Processing documents with OCR...');

    try {
      let successCount = 0;
      let failCount = 0;

      for (const uploadedFile of ehrFiles) {
        try {
          console.log(`Uploading EHR document: ${uploadedFile.name}`);
          const result = await api.uploadEHRDocument(uploadedFile.file, savedPatientId);
          console.log(`EHR document uploaded successfully:`, result);
          successCount++;
        } catch (error) {
          console.error(`Failed to upload ${uploadedFile.name}:`, error);
          failCount++;
        }
      }

      if (successCount > 0) {
        toast.success(`✅ ${successCount} document(s) uploaded and processed with OCR!`, {
          id: loadingToast,
          duration: 3000
        });
        setEhrFiles([]);
      } else {
        toast.error(`Failed to upload documents. Please try again.`, { id: loadingToast });
      }

      if (failCount > 0) {
        toast.error(`${failCount} document(s) failed to upload`, { duration: 3000 });
      }
    } catch (error: any) {
      console.error('Error processing EHR:', error);
      toast.error('Failed to process documents', { id: loadingToast });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUploadImages = async () => {
    if (imageFiles.length === 0) {
      toast.error('Please upload at least one image');
      return;
    }

    if (!savedPatientId) {
      toast.error('Please save patient information first');
      return;
    }

    setIsSubmitting(true);
    const loadingToast = toast.loading('Uploading medical images...');

    try {
      const files = imageFiles.map(f => f.file);
      console.log(`Uploading ${files.length} medical images...`);

      const result = await api.uploadMultipleFiles(files, savedPatientId);
      console.log('Medical images uploaded successfully:', result);

      toast.success(`✅ ${imageFiles.length} image(s) uploaded successfully!`, {
        id: loadingToast,
        duration: 3000
      });

      // Clear files after upload
      setImageFiles([]);
    } catch (error: any) {
      console.error('Error uploading images:', error);
      toast.error(error.response?.data?.detail || 'Failed to upload images', { id: loadingToast });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <Link to="/dashboard" className="text-blue-400 hover:text-blue-300 mb-4 inline-block">
            ← Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold text-white">Upload Patient Data</h1>
          <p className="text-gray-400 mt-2">Structured patient data intake - Stage 1</p>
          {savedPatientId && (
            <div className="mt-3 inline-flex items-center px-3 py-1 bg-green-900/30 border border-green-700 rounded-lg">
              <Check className="w-4 h-4 text-green-400 mr-2" />
              <span className="text-sm text-green-400">Patient saved - ready to upload documents</span>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex space-x-2 mb-6 bg-gray-800 rounded-xl p-1 border border-gray-700">
          <button
            onClick={() => setSelectedTab('patient')}
            className={`flex-1 px-4 py-3 font-semibold rounded-lg transition-all duration-200 ${
              selectedTab === 'patient'
                ? 'bg-gray-900 text-white shadow-lg'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <User className="w-4 h-4 inline mr-2" />
            Patient Info
          </button>
          <button
            onClick={() => setSelectedTab('ehr')}
            className={`flex-1 px-4 py-3 font-semibold rounded-lg transition-all duration-200 ${
              selectedTab === 'ehr'
                ? 'bg-gray-900 text-white shadow-lg'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <FileText className="w-4 h-4 inline mr-2" />
            EHR Document
          </button>
          <button
            onClick={() => setSelectedTab('image')}
            className={`flex-1 px-4 py-3 font-semibold rounded-lg transition-all duration-200 ${
              selectedTab === 'image'
                ? 'bg-gray-900 text-white shadow-lg'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <ImageIcon className="w-4 h-4 inline mr-2" />
            Medical Images
          </button>
          <button
            onClick={() => setSelectedTab('wearable')}
            className={`flex-1 px-4 py-3 font-semibold rounded-lg transition-all duration-200 ${
              selectedTab === 'wearable'
                ? 'bg-gray-900 text-white shadow-lg'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Activity className="w-4 h-4 inline mr-2" />
            Wearable Data
          </button>
        </div>

        {/* Content */}
        <div className="bg-gray-800/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-8">
          {/* PATIENT INFO TAB */}
          {selectedTab === 'patient' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-white mb-2">Patient & Visit Information</h2>
                <p className="text-sm text-gray-400 mb-6">Captured at baseline visit - demographics and medical history</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Patient Name *</label>
                  <input
                    type="text"
                    placeholder="e.g. Rosa Martinez"
                    value={patientForm.patientName}
                    onChange={(e) => handleInputChange('patientName', e.target.value)}
                    className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Patient ID</label>
                  <input
                    type="text"
                    placeholder="Auto-assigned if blank"
                    value={patientForm.patientId}
                    onChange={(e) => handleInputChange('patientId', e.target.value)}
                    className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Age *</label>
                  <input
                    type="number"
                    placeholder="58"
                    value={patientForm.age}
                    onChange={(e) => handleInputChange('age', e.target.value)}
                    className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Sex *</label>
                  <select
                    value={patientForm.sex}
                    onChange={(e) => handleInputChange('sex', e.target.value)}
                    className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select</option>
                    <option value="female">Female</option>
                    <option value="male">Male</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Height (cm)</label>
                  <input
                    type="number"
                    placeholder="170"
                    value={patientForm.height}
                    onChange={(e) => handleInputChange('height', e.target.value)}
                    className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Weight (kg)</label>
                  <input
                    type="number"
                    placeholder="76"
                    value={patientForm.weight}
                    onChange={(e) => handleInputChange('weight', e.target.value)}
                    className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">Visit Type</label>
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={() => handleInputChange('visitType', 'baseline')}
                    className={`px-4 py-2 font-semibold rounded-full transition-all duration-200 ${
                      patientForm.visitType === 'baseline'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    Baseline (first visit)
                  </button>
                  <button
                    onClick={() => handleInputChange('visitType', 'followup')}
                    className={`px-4 py-2 font-semibold rounded-full transition-all duration-200 ${
                      patientForm.visitType === 'followup'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    Follow-up
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">Known Conditions</label>
                <div className="flex flex-wrap gap-3">
                  {['Diabetes', 'Hypertension', 'Prior MI', 'CKD', 'Arrhythmia'].map((condition) => (
                    <button
                      key={condition}
                      onClick={() => toggleCondition(condition)}
                      className={`px-4 py-2 font-semibold rounded-full transition-all duration-200 ${
                        patientForm.conditions.includes(condition)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {patientForm.conditions.includes(condition) && <Check className="w-4 h-4 inline mr-1" />}
                      {condition}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Current Medications</label>
                <textarea
                  rows={3}
                  placeholder="e.g. Metoprolol 50mg, Lisinopril 10mg"
                  value={patientForm.medications}
                  onChange={(e) => handleInputChange('medications', e.target.value)}
                  className="w-full px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <button
                onClick={handleSavePatient}
                disabled={isSubmitting}
                className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold py-3 px-4 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <span>💾 Save Patient Information</span>
                )}
              </button>
            </div>
          )}

          {/* EHR DOCUMENT TAB */}
          {selectedTab === 'ehr' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-white mb-2">Upload EHR Document</h2>
                <p className="text-sm text-gray-400 mb-6">Upload PDF or image files - OCR will automatically extract data</p>
                {!savedPatientId && (
                  <div className="mb-4 p-3 bg-yellow-900/30 border border-yellow-700 rounded-lg">
                    <p className="text-sm text-yellow-400">⚠️ Please save patient information first</p>
                  </div>
                )}
              </div>

              <div className="border-2 border-dashed border-gray-600 rounded-xl p-12 text-center hover:border-blue-500 transition-all duration-200 bg-gray-700/30">
                <input
                  type="file"
                  id="ehr-upload"
                  multiple
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={(e) => handleFileUpload(e, 'ehr')}
                  className="hidden"
                />
                <label htmlFor="ehr-upload" className="cursor-pointer">
                  <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-white font-semibold mb-2">Click to browse or drag files here</p>
                  <p className="text-sm text-gray-400">PDF, JPG, PNG up to 10MB</p>
                  <p className="text-sm text-blue-400 mt-2">✨ OCR will automatically extract patient data</p>
                </label>
              </div>

              {ehrFiles.length > 0 && (
                <div className="space-y-3">
                  <p className="text-sm font-medium text-gray-300">{ehrFiles.length} file(s) ready to process</p>
                  {ehrFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-gray-700/50 border border-gray-600 rounded-xl">
                      <div className="flex items-center space-x-3">
                        <FileText className="w-5 h-5 text-blue-400" />
                        <div>
                          <p className="text-sm font-medium text-white">{file.name}</p>
                          <p className="text-xs text-gray-400">{formatFileSize(file.size)}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => removeFile(index, 'ehr')}
                        className="text-red-400 hover:text-red-300 transition-colors"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <button
                onClick={handleProcessEHR}
                disabled={isSubmitting || ehrFiles.length === 0 || !savedPatientId}
                className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-semibold py-3 px-4 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <span>🔍 Process with OCR & Save</span>
                )}
              </button>
            </div>
          )}

          {/* MEDICAL IMAGES TAB */}
          {selectedTab === 'image' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-white mb-2">Upload Medical Images</h2>
                <p className="text-sm text-gray-400 mb-6">DICOM, JPG, PNG - Tag each file by modality</p>
                {!savedPatientId && (
                  <div className="mb-4 p-3 bg-yellow-900/30 border border-yellow-700 rounded-lg">
                    <p className="text-sm text-yellow-400">⚠️ Please save patient information first</p>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">Select Modality</label>
                <div className="flex flex-wrap gap-3">
                  {['Echo', 'Cardiac MRI', 'CT angio', 'Chest X-ray'].map((modality) => (
                    <button
                      key={modality}
                      onClick={() => setSelectedModality(modality)}
                      className={`px-4 py-2 font-semibold rounded-full transition-all duration-200 ${
                        selectedModality === modality
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {modality}
                    </button>
                  ))}
                </div>
              </div>

              <div className="border-2 border-dashed border-gray-600 rounded-xl p-12 text-center hover:border-blue-500 transition-all duration-200 bg-gray-700/30">
                <input
                  type="file"
                  id="image-upload"
                  multiple
                  accept=".dcm,.jpg,.jpeg,.png,.pdf"
                  onChange={(e) => handleFileUpload(e, 'image')}
                  className="hidden"
                />
                <label htmlFor="image-upload" className="cursor-pointer">
                  <ImageIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-white font-semibold mb-2">Click to browse or drag images here</p>
                  <p className="text-sm text-gray-400">DICOM, PDF report, JPG, or PNG</p>
                  <p className="text-sm text-blue-400 mt-2">Files will be tagged with: <span className="font-bold">{selectedModality}</span></p>
                </label>
              </div>

              {imageFiles.length > 0 && (
                <div className="space-y-3">
                  <p className="text-sm font-medium text-gray-300">{imageFiles.length} image(s) ready to upload</p>
                  {imageFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-gray-700/50 border border-gray-600 rounded-xl">
                      <div className="flex items-center space-x-3">
                        <ImageIcon className="w-5 h-5 text-green-400" />
                        <div>
                          <p className="text-sm font-medium text-white">{file.name}</p>
                          <p className="text-xs text-gray-400">{formatFileSize(file.size)} • Tagged: {file.modality}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => removeFile(index, 'image')}
                        className="text-red-400 hover:text-red-300 transition-colors"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <button
                onClick={handleUploadImages}
                disabled={isSubmitting || imageFiles.length === 0 || !savedPatientId}
                className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-semibold py-3 px-4 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Uploading...</span>
                  </>
                ) : (
                  <span>📤 Upload Medical Images</span>
                )}
              </button>
            </div>
          )}

          {/* WEARABLE DATA TAB */}
          {selectedTab === 'wearable' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-white mb-2">Connect Wearable Device</h2>
                <p className="text-sm text-gray-400 mb-6">Connect your wearable to sync health data automatically</p>
              </div>

              <div className="space-y-4">
                {[
                  { name: 'Fitbit', icon: Activity, color: 'purple' },
                  { name: 'Apple Watch', icon: Heart, color: 'red' },
                  { name: 'Whoop', icon: Activity, color: 'yellow' },
                  { name: 'No wearable - manual entry', icon: FileText, color: 'gray' }
                ].map((device) => (
                  <button
                    key={device.name}
                    className="w-full flex items-center justify-between p-4 bg-gray-700/50 border border-gray-600 hover:border-blue-500 rounded-xl transition-all duration-200 group"
                  >
                    <div className="flex items-center space-x-4">
                      <device.icon className="w-6 h-6 text-gray-400 group-hover:text-white transition-colors" />
                      <span className="text-white font-medium">{device.name}</span>
                    </div>
                    <span className="text-blue-400 group-hover:text-blue-300 font-semibold">Connect →</span>
                  </button>
                ))}
              </div>

              <div className="mt-6 p-4 bg-blue-900/20 border border-blue-700 rounded-xl">
                <p className="text-sm text-blue-300">
                  💡 Wearable integration allows continuous monitoring of heart rate, activity levels, and sleep patterns for comprehensive patient data.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
