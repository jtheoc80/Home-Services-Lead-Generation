/**
 * HealthStatus component displays the backend health status in development mode
 */

import React, { useState, useEffect } from 'react';
import { fetchHealthStatus, HealthStatus as HealthStatusType } from '@/lib/apiClient';

interface HealthStatusProps {
  className?: string;
}

export default function HealthStatus({ className = '' }: HealthStatusProps) {
  const [health, setHealth] = useState<HealthStatusType | null>(null);
  const [loading, setLoading] = useState(true);

  // Only show in development mode
  const isDevelopment = process.env.NODE_ENV === 'development';

  useEffect(() => {
    if (!isDevelopment) {
      setLoading(false);
      return;
    }

    const checkHealth = async () => {
      try {
        const status = await fetchHealthStatus();
        setHealth(status);
      } catch (error) {
        console.error('Failed to check health status:', error);
        setHealth({
          status: 'unknown',
          timestamp: new Date().toISOString(),
          details: 'Failed to check status',
        });
      } finally {
        setLoading(false);
      }
    };

    // Initial check
    checkHealth();

    // Set up periodic health checks every 30 seconds
    const interval = setInterval(checkHealth, 30000);

    return () => clearInterval(interval);
  }, [isDevelopment]);

  // Don't render anything if not in development
  if (!isDevelopment) {
    return null;
  }

  if (loading) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
        <span className="text-sm text-gray-500">Checking backend...</span>
      </div>
    );
  }

  if (!health) {
    return null;
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'unhealthy':
        return 'bg-red-500';
      default:
        return 'bg-yellow-500';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'Backend Online';
      case 'unhealthy':
        return 'Backend Offline';
      default:
        return 'Backend Unknown';
    }
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`} title={health.details}>
      <div className={`w-2 h-2 rounded-full ${getStatusColor(health.status)}`}></div>
      <span className="text-sm text-gray-600">
        {getStatusText(health.status)}
      </span>
      {health.status === 'healthy' && (
        <span className="text-xs text-gray-400">
          ({new Date(health.timestamp).toLocaleTimeString()})
        </span>
      )}
    </div>
  );
}