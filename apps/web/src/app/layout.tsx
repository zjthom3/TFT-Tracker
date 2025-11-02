"use client";

import "../styles/globals.css";
import type { ReactNode } from "react";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="h-full bg-neutral-950 text-neutral-100">
      <body className="min-h-full bg-gradient-to-br from-neutral-950 via-neutral-900 to-neutral-950">
        {children}
      </body>
    </html>
  );
}
