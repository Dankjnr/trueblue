import { AnimatePresence, motion } from "framer-motion";

export default function CleanerShortlist({ assignments, onAssign, assigning }) {
  const candidates = assignments.filter((a) => a.status === "recommended" || a.status === "offered");

  if (candidates.length === 0) {
    return <p className="text-sm text-slate-300">No shortlist generated yet.</p>;
  }

  return (
    <ul className="space-y-2">
      <AnimatePresence initial={false}>
        {candidates.map((a, i) => (
          <motion.li
            key={a.id}
            layout
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 8 }}
            transition={{ duration: 0.18, delay: i * 0.03 }}
            className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-white/5 p-3"
          >
            <div>
              <p className="text-sm font-medium text-white">{a.cleaner.user.first_name} {a.cleaner.user.last_name}</p>
              <p className="mt-0.5 text-xs text-slate-300">
                Score {Number(a.rank_score).toFixed(2)} · Rating {a.cleaner.rating} · {a.cleaner.completed_jobs} jobs done
                {a.rank_breakdown?.distance_km != null && <> · {a.rank_breakdown.distance_km} km away</>}
              </p>
            </div>
            <button
              className="btn-secondary text-xs"
              disabled={assigning || a.status === "offered"}
              onClick={() => onAssign(a.cleaner.id)}
            >
              {a.status === "offered" ? "Offer sent" : "Assign"}
            </button>
          </motion.li>
        ))}
      </AnimatePresence>
    </ul>
  );
}
