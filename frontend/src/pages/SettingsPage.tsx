import { Link } from 'react-router-dom';
import { Shield, User, Bell } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <Link to="/dashboard" className="text-blue-400 hover:text-blue-300 mb-4 inline-block">
            ← Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold text-white">Settings</h1>
          <p className="text-gray-400 mt-2">Manage your account and security settings</p>
        </div>

        <div className="space-y-6">
          {/* Account Settings */}
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
            <div className="flex items-center mb-4">
              <User className="w-6 h-6 text-blue-400 mr-3" />
              <h2 className="text-xl font-semibold text-white">Account Information</h2>
            </div>
            <p className="text-gray-400">Manage your profile and account details</p>
          </div>

          {/* Security Settings */}
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
            <div className="flex items-center mb-4">
              <Shield className="w-6 h-6 text-green-400 mr-3" />
              <h2 className="text-xl font-semibold text-white">Security & Privacy</h2>
            </div>
            <div className="space-y-4">
              <button className="w-full text-left p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition">
                <p className="text-white font-medium">Two-Factor Authentication</p>
                <p className="text-sm text-gray-400 mt-1">Setup MFA for enhanced security</p>
              </button>

              <button className="w-full text-left p-4 bg-gray-700 hover:bg-gray-600 rounded-lg transition">
                <p className="text-white font-medium">Change Password</p>
                <p className="text-sm text-gray-400 mt-1">Update your account password</p>
              </button>
            </div>
          </div>

          {/* Notifications */}
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
            <div className="flex items-center mb-4">
              <Bell className="w-6 h-6 text-purple-400 mr-3" />
              <h2 className="text-xl font-semibold text-white">Notifications</h2>
            </div>
            <p className="text-gray-400">Configure your notification preferences</p>
          </div>
        </div>
      </div>
    </div>
  );
}
