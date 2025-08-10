'use client';
import { useEffect, useState } from 'react';

export default function LeadsPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [form, setForm] = useState({ name:'', phone:'', email:'', address:'', city:'', state:'', zip:'' });

  useEffect(() => {
    fetch('/api/leads').then(r => r.json()).then(d => setRows(d.data ?? []));
  }, []);

  return (
    <div style={{ padding: 24, maxWidth: 760 }}>
      <h1>Leads</h1>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          const res = await fetch('/api/leads', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(form)
          });
          const d = await res.json();
          if (res.ok) setRows(r => [d.data, ...r]);
          setForm({ name:'', phone:'', email:'', address:'', city:'', state:'', zip:'' });
        }}
        style={{ display:'grid', gap: 8, margin: '16px 0' }}
      >
        {Object.keys(form).map((k) => (
          <input key={k} placeholder={k} value={(form as any)[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} />
        ))}
        <button type="submit">Add lead</button>
      </form>

      <ul>
        {rows.slice(0, 10).map((r:any) => (
          <li key={r.id}>{r.created_at} — {r.name ?? '(no name)'} — {r.city}, {r.state}</li>
        ))}
      </ul>
    </div>
  );
}