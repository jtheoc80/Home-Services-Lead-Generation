import clsx from "clsx";

interface ProgressProps {
  value: number; // 0-100
  className?: string;
  color?: 'default' | 'success' | 'warning' | 'danger' | 'texas';
  animated?: boolean;
}

export function Progress({
  value,
  className,
  color = 'default',
  animated = true
}: ProgressProps) {
  const clampedValue = Math.min(Math.max(value, 0), 100);

  const colorClasses = {
    default: "bg-brand-500",
    success: "bg-success-500",
    warning: "bg-warning-500",
    danger: "bg-danger-500",
    texas: "bg-texas-500"
  };

  return (
    <div className={clsx(
      "bg-gray-200 rounded-full overflow-hidden",
      className
    )}>
      <div
        className={clsx(
          "h-full rounded-full transition-all duration-700 ease-out",
          colorClasses[color],
          animated && "animate-pulse-soft"
        )}
        style={{ width: `${clampedValue}%` }}
      />
    </div>
  );
}