import { ReactNode } from "react";
import clsx from "clsx";

export default function Badge({
  children,
  variant = "default"
}: { 
  children: ReactNode; 
  variant?: "default" | "success" | "warning" | "danger"
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        variant === "default" && "bg-gray-100 text-gray-800",
        variant === "success" && "bg-green-100 text-green-800",
        variant === "warning" && "bg-yellow-100 text-yellow-800", 
        variant === "danger" && "bg-red-100 text-red-800"
      )}
    >
      {children}
    </span>
  );
}