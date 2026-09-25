import { motion } from "framer-motion";
import { Link } from "react-router-dom";

import { StatusBadge, UrgencyBadge } from "./StatusBadge.jsx";

export default function JobCard({ job }) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
    >
      <Link
        to={`/jobs/${job.id}`}
        className="card block p-4 transition-colors duration-200 hover:border-[#3a4047]"
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[18px] font-medium text-white">{job.customer_name}</p>
            <p className="mt-1 text-[14px] text-slate-300">{job.location_summary}</p>
          </div>
          <UrgencyBadge urgency={job.urgency} />
        </div>

        <div className="mt-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-[12px] text-slate-200">
            <span>{job.requested_date}</span>
            <span aria-hidden>·</span>
            <span>{job.cleaners_needed} cleaner{job.cleaners_needed > 1 ? "s" : ""}</span>
          </div>
          <StatusBadge status={job.status} />
        </div>

        {job.assigned_cleaner && (
          <p className="mt-3 text-[12px] text-slate-200">
            {job.assigned_cleaner.status === "accepted" ? "Accepted by" : "Offered to"}{" "}
            <span className="text-white">{job.assigned_cleaner.name}</span>
          </p>
        )}
      </Link>
    </motion.div>
  );
}
