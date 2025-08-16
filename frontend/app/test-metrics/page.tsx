import React from 'react';
import MetricsCards from '../../components/MetricsCards';

// Simple test component to demonstrate MetricsCards functionality
export default function TestMetricsCards() {
  const sampleMetrics = {
    totalLeads: 42,
    totalValue: 892500,
    averageScore: 78,
    newLeads: 8,
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          MetricsCards Component Test
        </h1>
        
        <div className="space-y-8">
          <div>
            <h2 className="text-xl font-semibold text-gray-700 mb-4">With Sample Data</h2>
            <MetricsCards 
              totalLeads={sampleMetrics.totalLeads}
              totalValue={sampleMetrics.totalValue}
              averageScore={sampleMetrics.averageScore}
              newLeads={sampleMetrics.newLeads}
              loading={false}
            />
          </div>
          
          <div>
            <h2 className="text-xl font-semibold text-gray-700 mb-4">Loading State</h2>
            <MetricsCards 
              totalLeads={0}
              totalValue={0}
              averageScore={0}
              newLeads={0}
              loading={true}
            />
          </div>
        </div>
      </div>
    </div>
  );
}