"use client";
import clsx from "clsx";
import { ButtonHTMLAttributes } from "react";

export default function Button({
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" }) {
  const variant =
    (props as any).variant ?? "primary";
  return (
    <button
      {...props}
      className={clsx(
        "h-9 px-4 rounded-lg text-sm font-medium transition",
        variant === "primary" &&
          "bg-brand-600 text-white hover:bg-brand-700",
        variant === "ghost" &&
          "text-gray-700 hover:bg-gray-100",
        className
      )}
    />
  );
}