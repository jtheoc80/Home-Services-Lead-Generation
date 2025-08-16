import React from 'react';
import { Users, TrendingUp, Target, DollarSign } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  loading?: boolean;
}

function MetricCard({ title, value, change, changeLabel, icon, loading }: MetricCardProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gray-200 rounded"></div>
            <div className="w-24 h-4 bg-gray-200 rounded"></div>
          </div>
          <div className="w-12 h-8 bg-gray-200 rounded"></div>
        </div>
        <div className="mt-4">
          <div className="w-16 h-6 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            {icon}
          </div>
          <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        </div>
        {change !== undefined && (
          <div className={`flex items-center text-sm ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            <span>{change >= 0 ? '+' : ''}{change}%</span>
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-2xl font-semibold text-gray-900">{value}</p>
        {changeLabel && (
          <p className="text-sm text-gray-500">{changeLabel}</p>
        )}
      </div>
    </div>
  );
}

interface MetricsCardsProps {
  totalLeads: number;
  totalValue: number;
  averageScore: number;
  newLeads?: number;
  loading?: boolean;
}

export default function MetricsCards({
  totalLeads,
  totalValue,
  averageScore,
  newLeads,
  loading = false
}: MetricsCardsProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCard
        title="Total Leads"
        value={loading ? "—" : totalLeads}
        change={12}
        changeLabel="from last week"
        icon={<Users className="w-5 h-5 text-blue-600" />}
        loading={loading}
      />
      
      <MetricCard
        title="Total Value"
        value={loading ? "—" : formatCurrency(totalValue)}
        change={8}
        changeLabel="this month"
        icon={<DollarSign className="w-5 h-5 text-green-600" />}
        loading={loading}
      />
      
      <MetricCard
        title="Average Score"
        value={loading ? "—" : `${Math.round(averageScore)}/100`}
        change={5}
        changeLabel="improvement"
        icon={<Target className="w-5 h-5 text-purple-600" />}
        loading={loading}
      />
      
      {newLeads !== undefined && (
        <MetricCard
          title="New Leads"
          value={loading ? "—" : newLeads}
          change={15}
          changeLabel="today"
          icon={<TrendingUp className="w-5 h-5 text-orange-600" />}
          loading={loading}
        />
      )}
    </div>
  );
}