import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, FileText, Image, Activity } from 'lucide-react';

export default function ViewerPage() {
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <Link to="/dashboard" className="text-blue-400 hover:text-blue-300 mb-4 inline-block">
            ← Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold text-white">Data Viewer</h1>
          <p className="text-gray-400 mt-2">Search and view patient medical records</p>
        </div>

        {/* Search Bar */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 mb-6">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by patient name or ID..."
                className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center">
              <Filter className="w-5 h-5 mr-2" />
              Filters
            </button>
          </div>
        </div>

        {/* Data Type Tabs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <button className="p-6 bg-gray-800 border-2 border-blue-500 rounded-xl hover:bg-gray-700 transition text-left">
            <FileText className="w-8 h-8 text-blue-400 mb-2" />
            <h3 className="text-lg font-semibold text-white">Patient Records</h3>
            <p className="text-sm text-gray-400 mt-1">View medical history and notes</p>
          </button>

          <button className="p-6 bg-gray-800 border-2 border-gray-700 rounded-xl hover:bg-gray-700 transition text-left">
            <Image className="w-8 h-8 text-green-400 mb-2" />
            <h3 className="text-lg font-semibold text-white">DICOM Viewer</h3>
            <p className="text-sm text-gray-400 mt-1">View medical imaging (MRI, CT, X-ray)</p>
          </button>

          <button className="p-6 bg-gray-800 border-2 border-gray-700 rounded-xl hover:bg-gray-700 transition text-left">
            <Activity className="w-8 h-8 text-purple-400 mb-2" />
            <h3 className="text-lg font-semibold text-white">Wearable Data</h3>
            <p className="text-sm text-gray-400 mt-1">Monitor patient vitals over time</p>
          </button>
        </div>

        {/* Placeholder Content */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-12 text-center">
          <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No patients found</h3>
          <p className="text-gray-400">Search for a patient to view their records</p>
        </div>
      </div>
    </div>
  );
}
