import { ReactNode } from "react";

export default function Card({ title, children, className = "" }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <div className={`bg-panel border border-border rounded-lg p-4 ${className}`}>
      {title && <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3">{title}</h2>}
      {children}
    </div>
  );
}
