"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, FileText, Table2, Settings, MapPin, BarChart3, Star } from "lucide-react";
import clsx from "clsx";

const items = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/leads", label: "Leads", icon: Table2 },
  { href: "/permits", label: "Permits", icon: FileText },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings }
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 border-r bg-gradient-to-b from-white to-slate-50/50 backdrop-blur-sm">
      <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-200/50">
        <div className="relative">
          <div className="size-10 rounded-2xl bg-gradient-to-br from-navy-600 via-navy-700 to-slate-700 shadow-soft animate-float" />
          <Star className="absolute inset-0 m-auto w-5 h-5 text-white" />
        </div>
        <div className="leading-tight">
          <div className="font-bold tracking-tight bg-gradient-to-r from-navy-700 to-slate-700 bg-clip-text text-transparent">
            LeadLedgerPro
          </div>
          <div className="text-xs text-slate-500 font-medium">Texas Edition</div>
        </div>
      </div>
      
      <nav className="p-4 space-y-2">
        {items.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href;
          
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all duration-200 group",
                isActive
                  ? "bg-gradient-to-r from-navy-600 to-navy-700 text-white shadow-soft"
                  : "text-slate-700 hover:bg-slate-100/80 hover:text-slate-900"
              )}
            >
              <Icon 
                size={20} 
                className={clsx(
                  "transition-transform duration-200",
                  isActive ? "text-white" : "text-slate-500 group-hover:text-slate-700",
                  "group-hover:scale-110"
                )} 
              />
              <span className="font-medium">{label}</span>
              {isActive && (
                <div className="ml-auto w-2 h-2 rounded-full bg-white/80 animate-pulse-soft" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Texas Stats Card */}
      <div className="mx-4 mt-8 p-4 rounded-2xl bg-gradient-to-br from-navy-50 to-slate-100 border border-slate-200">
        <div className="flex items-center gap-2 mb-3">
          <MapPin className="w-4 h-4 text-navy-600" />
          <span className="text-sm font-semibold text-navy-800">Texas Coverage</span>
        </div>
        
        <div className="space-y-2 text-xs">
          <div className="flex justify-between text-navy-700">
            <span>Active Counties:</span>
            <span className="font-semibold">4</span>
          </div>
          <div className="flex justify-between text-navy-700">
            <span>Total Permits:</span>
            <span className="font-semibold">3,959</span>
          </div>
          <div className="flex justify-between text-navy-700">
            <span>This Week:</span>
            <span className="font-semibold">+187</span>
          </div>
        </div>
        
        <div className="mt-3 pt-3 border-t border-slate-200">
          <div className="text-xs text-navy-600 text-center">
            <span className="font-medium">Next Update:</span> 6:00 AM UTC
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="absolute bottom-4 left-4 right-4 text-center">
        <div className="text-xs text-gray-400">
          <div className="font-medium">Version 2.0</div>
          <div>Houston • Dallas • Austin</div>
        </div>
      </div>
    </aside>
  );
}