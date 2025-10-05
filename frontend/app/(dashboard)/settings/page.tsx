'use client';

import Card from "@/components/ui/Card";
import { Settings as SettingsIcon, Building2, Bell, Shield, Database, Palette, User } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="p-6 space-y-6 bg-gradient-to-br from-gray-50 to-white min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-slate-600 mt-1">Manage your account and application preferences</p>
        </div>
      </div>

      {/* Settings Grid */}
      <div className="grid gap-6">
        {/* Company Profile */}
        <Card className="p-6 border-l-4 border-navy-600">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-navy-50 rounded-xl">
              <Building2 className="w-6 h-6 text-navy-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Company Profile</h2>
              <p className="text-sm text-slate-600 mb-4">
                Manage your company information and team settings
              </p>
              <button className="px-4 py-2 bg-navy-600 text-white text-sm font-medium rounded-lg hover:bg-navy-700 transition-colors">
                Edit Profile
              </button>
            </div>
          </div>
        </Card>

        {/* User Account */}
        <Card className="p-6 border-l-4 border-slate-400">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-slate-100 rounded-xl">
              <User className="w-6 h-6 text-slate-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">User Account</h2>
              <p className="text-sm text-slate-600 mb-4">
                Update your personal information and password
              </p>
              <button className="px-4 py-2 border border-slate-300 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-50 transition-colors">
                Manage Account
              </button>
            </div>
          </div>
        </Card>

        {/* Notifications */}
        <Card className="p-6 border-l-4 border-orange-500">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-orange-50 rounded-xl">
              <Bell className="w-6 h-6 text-orange-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Notifications</h2>
              <p className="text-sm text-slate-600 mb-4">
                Configure email and push notification preferences
              </p>
              <div className="space-y-3">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" defaultChecked className="w-4 h-4 text-navy-600 rounded focus:ring-navy-500" />
                  <span className="text-sm text-gray-700">Email notifications for new hot leads</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" defaultChecked className="w-4 h-4 text-navy-600 rounded focus:ring-navy-500" />
                  <span className="text-sm text-gray-700">Weekly digest reports</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 text-navy-600 rounded focus:ring-navy-500" />
                  <span className="text-sm text-gray-700">SMS alerts for urgent leads</span>
                </label>
              </div>
            </div>
          </div>
        </Card>

        {/* Integrations */}
        <Card className="p-6 border-l-4 border-blue-500">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-blue-50 rounded-xl">
              <Database className="w-6 h-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Integrations</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                      <Database className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">Supabase</h3>
                      <p className="text-sm text-slate-600">Database and authentication</p>
                    </div>
                  </div>
                  <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">Connected</span>
                </div>

                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                      <Shield className="w-5 h-5 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">Stripe</h3>
                      <p className="text-sm text-slate-600">Payment processing</p>
                    </div>
                  </div>
                  <button className="px-3 py-1 border border-slate-300 text-slate-700 text-xs font-medium rounded-lg hover:bg-white transition-colors">
                    Configure
                  </button>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Appearance */}
        <Card className="p-6 border-l-4 border-indigo-500">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-indigo-50 rounded-xl">
              <Palette className="w-6 h-6 text-indigo-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Appearance</h2>
              <p className="text-sm text-slate-600 mb-4">
                Customize the look and feel of your dashboard
              </p>
              <div className="flex gap-3">
                <div className="px-4 py-2 bg-navy-600 text-white text-sm font-medium rounded-lg">
                  Navy Blue
                </div>
                <div className="px-4 py-2 border border-slate-300 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-50 transition-colors cursor-not-allowed opacity-50">
                  Light Mode
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
