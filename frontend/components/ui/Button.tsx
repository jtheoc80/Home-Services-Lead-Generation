"use client";
import clsx from "clsx";
import { ButtonHTMLAttributes } from "react";

export default function Button({
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" }) {
  const variant =
    props.variant ?? "primary";
  return (
    <button
      {...props}
      className={clsx(
        "h-9 px-4 rounded-lg text-sm font-medium transition",
        variant === "primary" &&
          "bg-navy-600 text-white hover:bg-navy-700",
        variant === "ghost" &&
          "text-slate-700 hover:bg-slate-100",
        className
      )}
    />
  );
}