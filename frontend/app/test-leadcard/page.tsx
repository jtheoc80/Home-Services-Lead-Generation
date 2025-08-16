import React from 'react';
import LeadCard from '../../components/LeadCard';
import { Lead } from '../../../types/supabase';

// Sample lead data that matches our new interface
const sampleLeads: Lead[] = [
  {
    id: '123e4567-e89b-12d3-a456-426614174000',
    created_at: '2025-01-15T10:30:00Z',
    updated_at: '2025-01-15T12:15:00Z',
    name: 'John Smith',
    email: 'john@example.com',
    phone: '+1-713-555-0101',
    address: '123 Main St',
    city: 'Houston',
    state: 'TX',
    zip: '77001',
    county: 'Harris',
    service: 'HVAC Installation',
    status: 'new',
    source: 'website',
    lead_score: 85,
    score_label: 'High',
    value: 15000,
    permit_id: 'TX2024-001234',
    county_population: 4731145,
    user_id: null,
    metadata: null,
  },
  {
    id: '123e4567-e89b-12d3-a456-426614174001',
    created_at: '2025-01-14T14:20:00Z',
    updated_at: '2025-01-14T16:45:00Z',
    name: 'Sarah Johnson',
    email: 'sarah@example.com',
    phone: '+1-713-555-0102',
    address: '456 Oak Ave',
    city: 'Houston',
    state: 'TX',
    zip: '77002',
    county: 'Harris',
    service: 'Electrical Repair',
    status: 'qualified',
    source: 'referral',
    lead_score: 75,
    score_label: 'Medium',
    value: 8500,
    permit_id: 'TX2024-001235',
    county_population: 4731145,
    user_id: null,
    metadata: null,
  }
];

export default function TestLeadCard() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          LeadCard Component Test
        </h1>
        
        <div className="space-y-8">
          <div>
            <h2 className="text-xl font-semibold text-gray-700 mb-4">Compact View (Dashboard Style)</h2>
            <div className="space-y-4">
              {sampleLeads.map(lead => (
                <LeadCard
                  key={lead.id}
                  lead={lead}
                  compact={true}
                  showFeedback={false}
                />
              ))}
            </div>
          </div>
          
          <div>
            <h2 className="text-xl font-semibold text-gray-700 mb-4">Full View</h2>
            <div className="space-y-6">
              {sampleLeads.map(lead => (
                <LeadCard
                  key={lead.id}
                  lead={lead}
                  compact={false}
                  showFeedback={false}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}