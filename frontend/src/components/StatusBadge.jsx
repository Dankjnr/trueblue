const URGENCY = {
  red: { label: "2+ days out", dot: "bg-red-500", text: "text-red-200", bg: "bg-red-500/15" },
  orange: { label: "Tomorrow", dot: "bg-amber-500", text: "text-amber-200", bg: "bg-amber-500/15" },
  green: { label: "Today", dot: "bg-emerald-500", text: "text-emerald-200", bg: "bg-emerald-500/15" },
};

const STATUS_LABEL = {
  requested: "Requested",
  shortlisted: "Shortlisted",
  assigned: "Awaiting response",
  accepted: "Accepted",
  in_progress: "In progress",
  completed: "Completed",
  declined: "Declined",
  cancelled: "Cancelled",
};

export function UrgencyBadge({ urgency }) {
  const cfg = URGENCY[urgency] ?? URGENCY.red;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${cfg.bg} ${cfg.text}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} aria-hidden />
      {cfg.label}
    </span>
  );
}

export function StatusBadge({ status }) {
  const label = STATUS_LABEL[status] ?? status;
  const palette =
    status === "completed" || status === "accepted" ? "bg-emerald-500/15 text-emerald-200" :
    status === "assigned" || status === "shortlisted" || status === "requested" ? "bg-amber-500/15 text-amber-200" :
    status === "declined" || status === "cancelled" ? "bg-red-500/15 text-red-200" :
    "bg-slate-500/20 text-slate-200";

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${palette}`}>
      {label}
    </span>
  );
}
