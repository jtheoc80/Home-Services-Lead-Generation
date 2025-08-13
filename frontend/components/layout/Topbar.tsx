"use client";

export default function Topbar() {
  return (
    <header className="h-16 bg-white border-b flex items-center">
      <div className="mx-auto w-full max-w-7xl px-6 flex items-center justify-between">
        <div className="text-sm text-gray-500">Good morning 👋</div>
        <div className="flex items-center gap-3">
          <div className="text-sm text-gray-600">Acme Roofing</div>
          <div className="size-8 rounded-full bg-brand-500 text-white grid place-items-center font-semibold">
            AR
          </div>
        </div>
      </div>
    </header>
  );
}