"use client";

import LogoutButton from "@/components/ui/LogoutButton";

interface DashboardHeaderProps {
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
}

export default function DashboardHeader({ 
  title, 
  subtitle, 
  children 
}: DashboardHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-8">
      {/* Left Section - Title and Subtitle */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
          {title}
        </h1>
        {subtitle && (
          <p className="text-lg text-gray-600">
            {subtitle}
          </p>
        )}
      </div>

      {/* Right Section - Actions */}
      <div className="flex items-center space-x-4">
        {children}
        <LogoutButton 
          variant="button"
          className="bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 hover:border-red-300"
        />
      </div>
    </div>
  );
}