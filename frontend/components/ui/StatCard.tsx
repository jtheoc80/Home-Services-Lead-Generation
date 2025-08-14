import { ReactNode } from "react";
import Card from "./Card";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import clsx from "clsx";

interface StatCardProps {
  label: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: ReactNode;
  variant?: 'default' | 'texas' | 'success' | 'warning' | 'danger';
  loading?: boolean;
}

export default function StatCard({
  label,
  value,
  change,
  changeLabel,
  icon,
  variant = 'default',
  loading = false
}: StatCardProps) {
  const getTrendIcon = () => {
    if (change === undefined) return <Minus className="w-4 h-4" />;
    if (change > 0) return <TrendingUp className="w-4 h-4" />;
    if (change < 0) return <TrendingDown className="w-4 h-4" />;
    return <Minus className="w-4 h-4" />;
  };

  const getTrendColor = () => {
    if (change === undefined) return "text-gray-400";
    if (change > 0) return "text-success-600";
    if (change < 0) return "text-danger-600";
    return "text-gray-400";
  };

  if (loading) {
    return (
      <Card className="p-6 animate-pulse">
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          <div className="h-3 bg-gray-200 rounded w-2/3"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6 hover:shadow-soft-lg transition-shadow duration-300" hover>
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <p className="text-sm font-medium text-gray-600">{label}</p>
          <p className="text-3xl font-bold text-gray-900 tracking-tight">{value}</p>
          
          {(change !== undefined || changeLabel) && (
            <div className={clsx("flex items-center space-x-1 text-sm", getTrendColor())}>
              {getTrendIcon()}
              <span>
                {change !== undefined && (
                  <span className="font-medium">
                    {change > 0 ? '+' : ''}{change}%
                  </span>
                )}
                {changeLabel && (
                  <span className="ml-1 text-gray-500">{changeLabel}</span>
                )}
              </span>
            </div>
          )}
        </div>
        
        {icon && (
          <div className={clsx(
            "p-3 rounded-xl",
            variant === 'texas' && "bg-texas-100 text-texas-600",
            variant === 'success' && "bg-success-100 text-success-600",
            variant === 'warning' && "bg-warning-100 text-warning-600",
            variant === 'danger' && "bg-danger-100 text-danger-600",
            variant === 'default' && "bg-brand-100 text-brand-600"
          )}>
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
}