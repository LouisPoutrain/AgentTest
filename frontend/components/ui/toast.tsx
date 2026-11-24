"use client";

import { Toaster as SonnerToaster } from "sonner";

export function Toaster() {
  return (
    <SonnerToaster
      position="bottom-right"
      richColors
      closeButton
      duration={4000}
      className="sonner-toaster"
      toastOptions={{
        style: {
          background: "var(--bg-primary)",
          color: "var(--text-primary)",
          border: "1px solid var(--border)",
        },
        classNames: {
          title: "font-medium",
          description: "text-[11px] opacity-70",
          error: "border-red-500/30 bg-red-500/10 text-red-400",
          success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
          warning: "border-amber-500/30 bg-amber-500/10 text-amber-400",
          info: "border-blue-500/30 bg-blue-500/10 text-blue-400",
        },
      }}
    />
  );
}
