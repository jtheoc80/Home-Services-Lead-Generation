'use client';

import { useEffect, useState } from 'react';
import { supabase, isSupabaseConfigured } from '@/lib/supabase-browser';
import { Lead } from '../../types/supabase';

// Extended Lead interface with computed fields for UI
export interface EnhancedLead extends Lead {
  score?: number;
  scoreBreakdown?: {
    recency: number;
    residential: number;
    value: number;
    workClass: number;
  };
  tradeType?: string;
  permitValue?: number;
  lastUpdated?: string;
  permitNumber?: string;
}

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

/**
 * Custom hook to fetch and manage leads from Supabase
 * Provides real-time updates via Supabase subscriptions
 */
export function useLeads() {
  const [leads, setLeads] = useState<Lead[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Initial fetch
  useEffect(() => {
    if (!isSupabaseConfigured()) {
      setError('Supabase client not configured. Please check your environment variables.');
      setLoading(false);
      return;
    }
    
    if (!supabase) {
      setError('Supabase client not available');
      setLoading(false);
      return;
    }
    
    let cancelled = false;
    
    const fetchLeads = async () => {
      try {
        const { data, error } = await supabase!
          .from('leads')
          .select('*')
          .order('created_at', { ascending: false });
        
        if (cancelled) return;
        
        if (error) {
          setError(`Failed to fetch leads: ${error.message}`);
        } else {
          setLeads(data as Lead[]);
        }
      } catch (err: any) {
        if (cancelled) return;
        setError(`Network error: ${err?.message || 'Unknown error'}`);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    
    fetchLeads();
    
    return () => { 
      cancelled = true; 
    };
  }, []);

  // Realtime subscription
  useEffect(() => {
    if (!supabase || !isSupabaseConfigured()) return;
    
    const channel = supabase
      .channel('leads-changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'leads' },
        (payload: any) => {
          setLeads((prev) => (prev ? applyChange(payload, prev) : prev));
        }
      )
      .subscribe((status) => {
        if (status === 'CHANNEL_ERROR') {
          setError('Real-time subscription error. Updates may not be live.');
        }
      });

    return () => { 
      if (supabase) {
        supabase.removeChannel(channel); 
      }
    };
  }, []);

  return { leads, error, loading };
}

/**
 * Enhanced hook that adds computed fields to leads for richer UI display
 */
export function useEnhancedLeads(): { 
  leads: EnhancedLead[] | null; 
  error: string | null; 
  loading: boolean;
} {
  const { leads, error, loading } = useLeads();
  
  const enhancedLeads = leads?.map((lead): EnhancedLead => {
    // Generate mock enhanced data for demo purposes
    // In a real app, this would come from additional database queries or computations
    const score = Math.floor(Math.random() * 40) + 60; // Random score 60-100
    const permitValue = Math.floor(Math.random() * 80000) + 20000; // Random value $20k-$100k
    
    return {
      ...lead,
      score,
      scoreBreakdown: {
        recency: Math.floor(score * 0.25),
        residential: Math.floor(score * 0.20),
        value: Math.floor(score * 0.30),
        workClass: Math.floor(score * 0.25),
      },
      tradeType: lead.service || 'General',
      permitValue,
      lastUpdated: formatRelativeTime(lead.created_at),
      permitNumber: `TX${new Date(lead.created_at).getFullYear()}-${String(lead.id).padStart(6, '0')}`
    };
  }) || null;
  
  return { leads: enhancedLeads, error, loading };
}

/**
 * Format a date string to relative time (e.g., "2 hours ago")
 */
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffMins < 60) return `${diffMins} minutes ago`;
  if (diffHours < 24) return `${diffHours} hours ago`;
  if (diffDays < 7) return `${diffDays} days ago`;
  
  return date.toLocaleDateString();
}