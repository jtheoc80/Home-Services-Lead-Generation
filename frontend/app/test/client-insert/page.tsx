'use client';

import { useState } from 'react';
import { createClient } from '@supabase/supabase-js';

export default function ClientInsertPage() {
  const [result, setResult] = useState<{ error?: string; details?: any; success?: boolean; data?: any } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleInsert = async () => {
    setLoading(true);
    setResult(null);

    try {
      // Create Supabase client directly in the browser
      const supabase = createClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
      );

      // Insert the specified data into public.leads
      const { data, error } = await supabase
        .from('leads')
        .insert([{ name: "Client", source: "client" }])
        .select('*')
        .single();

      if (error) {
        setResult({ error: error.message, details: error });
      } else {
        setResult({ success: true, data });
      }
    } catch (error) {
      setResult({ error: 'Unexpected error occurred', details: error });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Client Insert Test</h1>
      <p>
        This page demonstrates inserting data directly into public.leads using 
        createClient(NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY) in the browser.
      </p>
      
      <div style={{ margin: '20px 0' }}>
        <button 
          onClick={handleInsert} 
          disabled={loading}
          style={{
            padding: '12px 24px',
            fontSize: '16px',
            backgroundColor: '#0070f3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          {loading ? 'Inserting...' : 'Insert { name:"Client", source:"client" }'}
        </button>
      </div>

      {result && (
        <div style={{ 
          marginTop: '20px', 
          padding: '16px', 
          backgroundColor: '#f5f5f5', 
          borderRadius: '4px',
          border: '1px solid #ddd'
        }}>
          <h3>Result:</h3>
          <pre style={{ 
            backgroundColor: '#fff', 
            padding: '12px', 
            borderRadius: '4px',
            overflow: 'auto',
            fontSize: '14px',
            fontFamily: 'monospace'
          }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}