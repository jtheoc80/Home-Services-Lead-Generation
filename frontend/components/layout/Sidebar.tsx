"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, FileText, Table2, Settings } from "lucide-react";
import clsx from "clsx";

const items = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/leads", label: "Leads", icon: Table2 },
  { href: "/permits", label: "Permits", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings }
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 border-r bg-white">
      <div className="h-16 flex items-center gap-2 px-5 border-b">
        <div className="size-8 rounded-xl bg-gradient-to-br from-indigo-500 to-sky-500" />
        <div className="leading-tight">
          <div className="font-semibold tracking-tight">Lead Ledger Pro</div>
          <div className="text-xs text-slate-500">Contractor CRM</div>
        </div>
      </div>
      <nav className="px-2 space-y-1">
        {items.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={clsx(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm hover:bg-gray-100",
              pathname === href
                ? "bg-gray-100 text-brand-700"
                : "text-gray-700"
            )}
          >
            <Icon size={18} />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}