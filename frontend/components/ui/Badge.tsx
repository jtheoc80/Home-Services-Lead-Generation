import { ReactNode } from "react";
import clsx from "clsx";

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'texas' | 'score';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export default function Badge({
  children,
  variant = 'default',
  size = 'md',
  className
}: BadgeProps) {
  const baseClasses = "inline-flex items-center font-medium rounded-full";
  
  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-sm",
    lg: "px-3 py-1.5 text-base"
  };

  const variantClasses = {
    default: "bg-gray-100 text-gray-800 border border-gray-200",
    success: "bg-success-100 text-success-800 border border-success-200",
    warning: "bg-warning-100 text-warning-800 border border-warning-200",
    danger: "bg-danger-100 text-danger-800 border border-danger-200",
    texas: "bg-texas-100 text-texas-800 border border-texas-200",
    score: "bg-gradient-to-r from-success-500 to-brand-500 text-white border-0 shadow-soft"
  };

  return (
    <span className={clsx(
      baseClasses,
      sizeClasses[size],
      variantClasses[variant],
      className
    )}>
      {children}
    </span>
  );
}