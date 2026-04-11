type Status = "pass" | "fail" | "error" | "skipped";

const styles: Record<Status, string> = {
  pass: "bg-success/20 text-success",
  fail: "bg-danger/20 text-danger",
  error: "bg-warning/20 text-warning",
  skipped: "bg-muted/20 text-muted",
};

export default function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles[status] ?? styles.skipped}`}>
      {status}
    </span>
  );
}
