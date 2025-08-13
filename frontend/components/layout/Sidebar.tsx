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
    <aside className="w-64 border-r bg-white">
      <div className="p-4">
        <div className="font-semibold text-lg tracking-tight">
          <span className="text-brand-600">Lead</span>Ledder
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