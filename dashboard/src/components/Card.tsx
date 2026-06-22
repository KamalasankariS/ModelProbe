import { ReactNode } from "react";

export default function Card({ title, children, className = "" }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <div className={`bg-white border border-border rounded-xl p-5 shadow-sm ${className}`}>
      {title && <h2 className="text-xs font-semibold text-stone-400 uppercase tracking-wider mb-3">{title}</h2>}
      {children}
    </div>
  );
}
