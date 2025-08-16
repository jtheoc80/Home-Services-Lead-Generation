"use client";

import SignUpForm from "@/components/auth/SignUpForm";

// Override the main layout for auth pages by rendering our own structure
export default function SignUpPage() {
  return (
    <div className="fixed inset-0 min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 z-[9999]">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow-lg">
        <SignUpForm />
      </div>
    </div>
  );
}