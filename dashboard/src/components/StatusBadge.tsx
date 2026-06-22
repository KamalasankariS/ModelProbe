type Status = "pass" | "fail" | "error" | "skipped";

const styles: Record<Status, string> = {
  pass: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
  fail: "bg-red-50 text-red-700 ring-1 ring-red-200",
  error: "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
  skipped: "bg-stone-100 text-stone-500 ring-1 ring-stone-200",
};

export default function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] ?? styles.skipped}`}>
      {status}
    </span>
  );
}
