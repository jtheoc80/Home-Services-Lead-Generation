"use client";

import { useState, useEffect } from "react";
import { Bell, Search, Settings, User, ChevronDown, MapPin, Clock, Zap, Menu } from "lucide-react";
import Badge from "@/components/ui/Badge";

interface TopbarProps {
  onMenuClick?: () => void;
}

export default function Topbar({ onMenuClick }: TopbarProps) {
  const [showNotifications, setShowNotifications] = useState(false);
  const [greeting, setGreeting] = useState("Good day");
  
  useEffect(() => {
    const currentHour = new Date().getHours();
    if (currentHour < 12) setGreeting("Good morning");
    else if (currentHour < 17) setGreeting("Good afternoon");
    else setGreeting("Good evening");
  }, []);

  return (
    <header className="h-16 bg-white/80 backdrop-blur-sm border-b border-gray-200/50 flex items-center sticky top-0 z-40">
      <div className="mx-auto w-full max-w-7xl px-3 sm:px-6 flex items-center justify-between gap-2">
        {/* Left Section with Hamburger */}
        <div className="flex items-center space-x-3 sm:space-x-6">
          {/* Mobile Menu Button */}
          {onMenuClick && (
            <button
              onClick={onMenuClick}
              className="lg:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}
          
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600 font-medium hidden sm:inline">{greeting}</span>
            <span className="text-lg">👋</span>
          </div>
          
          {/* Live Status Indicators - Hidden on small screens */}
          <div className="hidden md:flex items-center space-x-4">
            <div className="flex items-center space-x-1 text-xs">
              <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
              <span className="text-gray-600">Live Data</span>
            </div>
            
            <div className="flex items-center space-x-1 text-xs text-gray-500">
              <Clock className="w-3 h-3" />
              <span>Last sync: 2m ago</span>
            </div>
          </div>
        </div>

        {/* Center Section - Search (Hidden on mobile) */}
        <div className="hidden lg:flex flex-1 max-w-md mx-8">
          <div className="relative w-full">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search leads, permits, counties..."
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-navy-500 focus:border-navy-500 focus:bg-white transition-colors"
            />
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center space-x-2 sm:space-x-4">
          {/* Quick Stats - Hidden on smaller screens */}
          <div className="hidden xl:flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm">
              <MapPin className="w-4 h-4 text-navy-600" />
              <span className="text-slate-600">4 Counties</span>
            </div>
            
            <div className="flex items-center space-x-2 text-sm">
              <Zap className="w-4 h-4 text-navy-600" />
              <span className="text-slate-600">24 New</span>
            </div>
          </div>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors"
            >
              <Bell className="w-5 h-5" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-danger-500 rounded-full flex items-center justify-center">
                <span className="text-[10px] text-white font-bold">3</span>
              </div>
            </button>
            
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 max-w-[calc(100vw-2rem)] bg-white rounded-2xl shadow-soft-xl border border-gray-200 py-2 z-50">
                <div className="px-4 py-2 border-b border-gray-100">
                  <h3 className="font-semibold text-gray-900">Notifications</h3>
                </div>
                
                <div className="space-y-1 max-h-64 overflow-y-auto">
                  <div className="px-4 py-3 hover:bg-slate-50 cursor-pointer">
                    <div className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-navy-500 rounded-full mt-2"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">New high-score lead</p>
                        <p className="text-xs text-slate-600">Johnson Residence - Score: 87</p>
                        <p className="text-xs text-slate-400">2 minutes ago</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="px-4 py-3 hover:bg-slate-50 cursor-pointer">
                    <div className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-navy-500 rounded-full mt-2"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">Harris County sync complete</p>
                        <p className="text-xs text-slate-600">187 new permits processed</p>
                        <p className="text-xs text-slate-400">1 hour ago</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="px-4 py-3 hover:bg-gray-50 cursor-pointer">
                    <div className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-success-500 rounded-full mt-2"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">Lead converted</p>
                        <p className="text-xs text-gray-600">Wilson Pool Installation - $75K</p>
                        <p className="text-xs text-gray-400">2 hours ago</p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="px-4 py-2 border-t border-gray-100">
                  <button className="text-sm text-navy-600 hover:text-navy-700 font-medium">
                    View all notifications
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Settings - Hidden on very small screens */}
          <button className="hidden sm:block p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors">
            <Settings className="w-5 h-5" />
          </button>

          {/* User Profile */}
          <div className="flex items-center space-x-2 sm:space-x-3 pl-2 sm:pl-4 border-l border-gray-200">
            <div className="hidden md:block text-right">
              <div className="text-sm font-medium text-gray-900">Texas Contractor</div>
              <div className="text-xs text-gray-600">Premium Plan</div>
            </div>
            
            <div className="relative group">
              <button className="flex items-center space-x-1 sm:space-x-2 p-1 rounded-xl hover:bg-gray-100 transition-colors">
                <div className="size-8 rounded-xl bg-gradient-to-br from-navy-600 to-navy-700 text-white grid place-items-center font-semibold text-sm shadow-soft">
                  TC
                </div>
                <ChevronDown className="w-4 h-4 text-slate-600 group-hover:text-slate-900 hidden sm:block" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
