import "./globals.css";

import type { ReactNode } from "react";

import Sidebar from "@/components/layout/Sidebar";
import Sidebar from "../components/layout/Sidebar";
import Topbar from "../components/layout/Topbar";

export const metadata = {
  title: "LeadLedder Pro",
  description: "Leads & permits for contractors"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex-1 flex flex-col">
            <Topbar />
            <main className="p-6 bg-gray-50 min-h-[calc(100vh-64px)]">
              <div className="mx-auto max-w-7xl">{children}</div>
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}