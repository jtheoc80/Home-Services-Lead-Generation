"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { getSupabaseClient, isSupabaseConfigured } from "@/lib/supabase-browser";

interface LogoutButtonProps {
  children?: React.ReactNode;
  className?: string;
  variant?: "button" | "link";
  showIcon?: boolean;
}

export default function LogoutButton({ 
  children, 
  className = "", 
  variant = "button",
  showIcon = true 
}: LogoutButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleLogout = async () => {
    if (!isSupabaseConfigured()) {
      console.warn("Supabase not configured, redirecting to login");
      router.push("/login");
      return;
    }

    try {
      setIsLoading(true);
      const supabase = getSupabaseClient();
      
      const { error } = await supabase.auth.signOut();
      
      if (error) {
        console.error("Logout error:", error);
        // Still redirect even if there's an error
      }
      
      // Redirect to login page
      router.push("/login");
    } catch (error) {
      console.error("Logout failed:", error);
      // Redirect anyway for better UX
      router.push("/login");
    } finally {
      setIsLoading(false);
    }
  };

  const buttonContent = (
    <>
      {showIcon && <LogOut className="w-4 h-4" />}
      {children || "Logout"}
    </>
  );

  if (variant === "link") {
    return (
      <button
        onClick={handleLogout}
        disabled={isLoading}
        className={`inline-flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors ${isLoading ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
      >
        {buttonContent}
      </button>
    );
  }

  return (
    <button
      onClick={handleLogout}
      disabled={isLoading}
      className={`inline-flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl transition-colors ${isLoading ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
    >
      {buttonContent}
    </button>
  );
}