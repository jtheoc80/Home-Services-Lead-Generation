'use client';

import { useEffect, useState } from 'react';
import { supabase, isSupabaseConfigured } from '@/lib/supabase-browser';
import { Lead } from '../../types/supabase';

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
 * This provides backward compatibility with the existing dashboard
 */
export function useEnhancedLeads(): { 
  leads: EnhancedLead[] | null; 
  error: string | null; 
  loading: boolean;
} {
  const { leads, error, loading } = useLeads();
  
  const enhancedLeads = leads?.map((lead): EnhancedLead => {
    return {
      ...lead,
      // Use real score from database or provide a default
      score: lead.lead_score || 75,
      scoreBreakdown: {
        recency: 20,
        residential: 15,
        value: 25,
        workClass: 15,
      },
      // Use service field as tradeType
      tradeType: lead.service || 'General',
      // Use actual value from database
      permitValue: lead.value || 50000,
      // Format relative time from created_at
      lastUpdated: formatRelativeTime(lead.created_at),
      // Generate permit number from real data
      permitNumber: lead.permit_id || `TX${new Date(lead.created_at).getFullYear()}-${lead.id.slice(-6)}`
    };
  }) || null;
  
  return { leads: enhancedLeads, error, loading };
}

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
 * Format a date string to relative time (e.g., "2 hours ago")
 */
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInMs = now.getTime() - date.getTime();
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

  if (diffInMinutes < 1) return 'Just now';
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
  if (diffInHours < 24) return `${diffInHours}h ago`;
  if (diffInDays < 7) return `${diffInDays}d ago`;
  if (diffInDays < 30) return `${Math.floor(diffInDays / 7)}w ago`;
  if (diffInDays < 365) return `${Math.floor(diffInDays / 30)}mo ago`;
  return `${Math.floor(diffInDays / 365)}y ago`;
}