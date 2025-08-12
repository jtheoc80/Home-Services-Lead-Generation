// app/page.tsx

import Link from "next/link";

export const metadata = {
  title: "LeadLedger Pro — Fresh Local Permit Leads",
  description: "Find permits by trade and zip. Updated hourly. Start a free trial.",
  openGraph: { title: "LeadLedger Pro", description: "Fresh local permit leads", type: "website" },
  twitter: { card: "summary_large_image", title: "LeadLedger Pro", description: "Fresh local permit leads" }
};

export default function Home() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <section className="text-center">
        <h1 className="text-4xl md:text-6xl font-bold tracking-tight">Fresh local permit leads for contractors</h1>
        <p className="mt-4 text-lg text-gray-600">Target by trade and zip. Hourly refresh. No cold lists.</p>
        
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link 
            href="/signup" 
            className="rounded-md bg-indigo-600 px-6 py-3 text-white font-semibold hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors duration-200"
            aria-label="Start your free trial - no credit card required"
          >
            Start free trial
          </Link>
          <Link 
            href="/dashboard?demo=true" 
            className="rounded-md border border-gray-300 px-6 py-3 font-semibold text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors duration-200"
            aria-label="View sample permit leads data"
          >
            See sample leads
          </Link>
        </div>

        <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { title: "Public records data", sub: "Verified sources" },
            { title: "Hourly refresh", sub: "Near-real-time" },
            { title: "Cancel anytime", sub: "No contracts" },
          {TRUST_BADGES.map((b, i) => (
            <div key={i} className="rounded-lg border border-gray-200 p-4 bg-white shadow-sm">
              <div className="text-sm font-medium text-gray-900">{b.title}</div>
              <div className="text-sm text-gray-500 mt-1">{b.sub}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-16">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">How it works</h2>
        <ol className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { n: "1", t: "Pick markets & trades", d: "Choose counties/zips and the trades you care about." },
            { n: "2", t: "We ingest permits hourly", d: "We pull from county/city systems and normalize." },
            { n: "3", t: "Work your queue", d: "Filter, export, and contact homeowners or GCs." },
          ].map((s) => (
            <li key={s.n} className="rounded-lg border border-gray-200 p-4 bg-white shadow-sm">
              <div className="text-indigo-600 font-bold text-lg mb-2">{s.n}</div>
              <div className="font-medium text-gray-900 mb-2">{s.t}</div>
              <div className="text-sm text-gray-600">{s.d}</div>
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}