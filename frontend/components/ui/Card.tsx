import { ReactNode } from "react";
import clsx from "clsx";

interface CardProps {
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'glass' | 'gradient' | 'texas';
  hover?: boolean;
  glow?: boolean;
}

export default function Card({
  children,
  className,
  variant = 'default',
  hover = false,
  glow = false
}: CardProps) {
  const baseClasses = "rounded-2xl border transition-all duration-300";
  
  const variantClasses = {
    default: "bg-white border-gray-200 shadow-soft",
    glass: "bg-white/80 backdrop-blur-sm border-white/20 shadow-soft-lg",
    gradient: "bg-gradient-to-br from-navy-600 to-navy-700 border-navy-500 text-white shadow-glow",
    texas: "bg-gradient-to-br from-navy-600 to-navy-700 border-navy-500 text-white shadow-glow"
  };

  const hoverClasses = hover ? "hover:shadow-soft-xl hover:scale-[1.02] cursor-pointer" : "";
  const glowClasses = glow ? "animate-pulse-soft" : "";

  return (
    <div className={clsx(
      baseClasses,
      variantClasses[variant],
      hoverClasses,
      glowClasses,
      className
    )}>
      {children}
    </div>
  );
}