'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase-browser';

export type Lead = {
  id: string;
  name: string;
  trade: string;
  county: string;
  status: 'New' | 'Qualified' | 'Contacted' | 'Won' | 'Lost';
  phone: string | null;
  email: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

function applyChange(
  payload: { eventType: 'INSERT' | 'UPDATE' | 'DELETE'; new?: Lead; old?: Lead },
  current: Lead[]
): Lead[] {
  switch (payload.eventType) {
    case 'INSERT':
      return [payload.new as Lead, ...current];
    case 'UPDATE':
      return current.map((r) => (r.id === payload.new!.id ? (payload.new as Lead) : r));
    case 'DELETE':
      return current.filter((r) => r.id !== payload.old!.id);
    default:
      return current;
  }
}

export function useLeads() {
  const [leads, setLeads] = useState<Lead[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // initial fetch
  useEffect(() => {
    if (!supabase) {
      setError('Supabase client not configured');
      return;
    }
    
    let cancelled = false;
    supabase.from('leads').select('*').order('created_at', { ascending: false })
      .then(({ data, error }) => {
        if (cancelled) return;
        if (error) setError(error.message);
        else setLeads(data as Lead[]);
      });
    return () => { cancelled = true; };
  }, []);

  // realtime subscription
  useEffect(() => {
    if (!supabase) return;
    
    const channel = supabase
      .channel('leads-changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'leads' },
        (payload: { eventType: 'INSERT' | 'UPDATE' | 'DELETE'; new?: Lead; old?: Lead }) => {
          setLeads((prev) => (prev ? applyChange(payload, prev) : prev));
        }
      )
      .subscribe((status) => {
        if (status === 'CHANNEL_ERROR') setError('Realtime channel error');
      });

    return () => { supabase.removeChannel(channel); };
  }, []);

  return { leads, error };
}