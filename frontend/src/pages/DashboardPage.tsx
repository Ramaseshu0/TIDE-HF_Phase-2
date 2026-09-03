import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import {
  LayoutDashboard,
  Upload,
  Eye,
  Settings,
  LogOut,
  Users,
  FileText,
  Activity,
  Heart,
  Clock,
  TrendingUp,
  AlertCircle,
  ChevronRight,
  Bell,
  Search,
} from 'lucide-react';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const stats = [
    {
      label: 'Total Patients',
      value: '0',
      change: '+0%',
      icon: Users,
      color: 'from-blue-500 to-blue-600',
      bgColor: 'bg-blue-500/10',
      iconColor: 'text-blue-400',
    },
    {
      label: 'Medical Records',
      value: '0',
      change: '+0%',
      icon: FileText,
      color: 'from-green-500 to-green-600',
      bgColor: 'bg-green-500/10',
      iconColor: 'text-green-400',
    },
    {
      label: 'Active Monitoring',
      value: '0',
      change: '+0%',
      icon: Activity,
      color: 'from-purple-500 to-purple-600',
      bgColor: 'bg-purple-500/10',
      iconColor: 'text-purple-400',
    },
    {
      label: 'Pending Reviews',
      value: '0',
      change: '0%',
      icon: AlertCircle,
      color: 'from-orange-500 to-orange-600',
      bgColor: 'bg-orange-500/10',
      iconColor: 'text-orange-400',
    },
  ];

  const quickActions = [
    {
      title: 'Upload Patient Data',
      description: 'Add new patient records and medical data',
      icon: Upload,
      link: '/upload',
      color: 'from-blue-500 to-blue-600',
      iconBg: 'bg-blue-500/10',
    },
    {
      title: 'View Patient Records',
      description: 'Access and review medical histories',
      icon: Eye,
      link: '/viewer',
      color: 'from-green-500 to-green-600',
      iconBg: 'bg-green-500/10',
    },
  ];

  const recentActivity = [
    {
      type: 'info',
      message: 'System initialized and ready',
      time: 'Just now',
      icon: Heart,
    },
  ];

  return (
    <div className="min-h-screen flex bg-gray-900">
      {/* Sidebar */}
      <div className="w-72 bg-gray-800/50 backdrop-blur-xl border-r border-gray-700/50 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-700/50">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center">
              <Heart className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">QAS AI</h1>
              <p className="text-xs text-gray-400">Medical System</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          <Link
            to="/dashboard"
            className="flex items-center px-4 py-3 text-white bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl shadow-lg shadow-blue-500/20 transform transition-all duration-200"
          >
            <LayoutDashboard className="w-5 h-5 mr-3" />
            <span className="font-medium">Dashboard</span>
          </Link>

          <Link
            to="/upload"
            className="flex items-center px-4 py-3 text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-xl transition-all duration-200 group"
          >
            <Upload className="w-5 h-5 mr-3 group-hover:scale-110 transition-transform" />
            <span>Upload Data</span>
          </Link>

          <Link
            to="/viewer"
            className="flex items-center px-4 py-3 text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-xl transition-all duration-200 group"
          >
            <Eye className="w-5 h-5 mr-3 group-hover:scale-110 transition-transform" />
            <span>View Data</span>
          </Link>

          <Link
            to="/settings"
            className="flex items-center px-4 py-3 text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-xl transition-all duration-200 group"
          >
            <Settings className="w-5 h-5 mr-3 group-hover:rotate-90 transition-transform duration-300" />
            <span>Settings</span>
          </Link>
        </nav>

        {/* User Profile */}
        <div className="p-4 border-t border-gray-700/50">
          <div className="bg-gray-700/30 rounded-xl p-4 mb-3">
            <div className="flex items-center mb-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center mr-3">
                <span className="text-white font-bold text-lg">
                  {user?.full_name?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">
                  {user?.full_name || 'User'}
                </p>
                <p className="text-xs text-gray-400 capitalize">{user?.role || 'User'}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center px-4 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all duration-200"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        {/* Header */}
        <div className="bg-gray-800/30 backdrop-blur-xl border-b border-gray-700/50 px-8 py-6 sticky top-0 z-10">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white mb-1">
                Welcome back, {user?.full_name?.split(' ')[0] || 'Doctor'}! 👋
              </h2>
              <p className="text-gray-400 flex items-center space-x-2">
                <Clock className="w-4 h-4" />
                <span>{currentTime.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
                <span className="text-gray-600">•</span>
                <span>{currentTime.toLocaleTimeString()}</span>
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button className="relative p-3 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-xl transition-all duration-200">
                <Search className="w-5 h-5" />
              </button>
              <button className="relative p-3 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-xl transition-all duration-200">
                <Bell className="w-5 h-5" />
                <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
            </div>
          </div>
        </div>

        <div className="p-8">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {stats.map((stat, index) => (
              <div
                key={index}
                className="bg-gray-800/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6 hover:border-gray-600/50 transition-all duration-300 hover:transform hover:scale-105 cursor-pointer group"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 ${stat.bgColor} rounded-xl group-hover:scale-110 transition-transform duration-300`}>
                    <stat.icon className={`w-6 h-6 ${stat.iconColor}`} />
                  </div>
                  <div className="flex items-center space-x-1 text-sm">
                    <TrendingUp className="w-4 h-4 text-green-400" />
                    <span className="text-green-400 font-medium">{stat.change}</span>
                  </div>
                </div>
                <div>
                  <p className="text-gray-400 text-sm mb-1">{stat.label}</p>
                  <p className="text-3xl font-bold text-white">{stat.value}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Quick Actions */}
            <div className="lg:col-span-2">
              <div className="bg-gray-800/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-white">Quick Actions</h3>
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {quickActions.map((action, index) => (
                    <Link
                      key={index}
                      to={action.link}
                      className="group relative bg-gradient-to-br from-gray-700/30 to-gray-700/10 hover:from-gray-700/50 hover:to-gray-700/30 border border-gray-600/30 hover:border-gray-600/50 rounded-xl p-6 transition-all duration-300 overflow-hidden"
                    >
                      <div className={`absolute inset-0 bg-gradient-to-br ${action.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`}></div>
                      <div className="relative">
                        <div className={`inline-flex p-3 ${action.iconBg} rounded-xl mb-4 group-hover:scale-110 transition-transform duration-300`}>
                          <action.icon className={`w-6 h-6 bg-gradient-to-br ${action.color} bg-clip-text text-transparent`} style={{ WebkitTextFillColor: 'transparent' }} />
                        </div>
                        <h4 className="text-white font-semibold mb-2">{action.title}</h4>
                        <p className="text-gray-400 text-sm">{action.description}</p>
                        <ChevronRight className="absolute bottom-6 right-6 w-5 h-5 text-gray-600 group-hover:text-gray-400 group-hover:translate-x-1 transition-all duration-300" />
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="lg:col-span-1">
              <div className="bg-gray-800/50 backdrop-blur-xl border border-gray-700/50 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-white">Recent Activity</h3>
                  <Activity className="w-5 h-5 text-gray-400" />
                </div>
                <div className="space-y-4">
                  {recentActivity.map((activity, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 bg-gray-700/20 rounded-xl hover:bg-gray-700/30 transition-colors duration-200">
                      <div className="p-2 bg-blue-500/10 rounded-lg">
                        <activity.icon className="w-4 h-4 text-blue-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white">{activity.message}</p>
                        <p className="text-xs text-gray-400 mt-1">{activity.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* System Status */}
          <div className="mt-6 bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-green-500/20 rounded-2xl p-6">
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <div>
                <p className="text-white font-medium">System Online</p>
                <p className="text-sm text-gray-400">All services operational • Last checked: Just now</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
