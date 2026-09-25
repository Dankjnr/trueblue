import { motion } from "framer-motion";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import api from "../api/client.js";
import CleanerShortlist from "../components/CleanerShortlist.jsx";
import { StatusBadge, UrgencyBadge } from "../components/StatusBadge.jsx";
import { useAuth } from "../context/AuthContext.jsx";

export default function JobDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [job, setJob] = useState(null);
  const [busy, setBusy] = useState(false);
  const [packet, setPacket] = useState({ start_time: "", timeframe_minutes: 60, special_instructions: "" });

  const load = useCallback(() => {
    return api.get(`/jobs/${id}/`).then((res) => setJob(res.data));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (!job) {
    return <div className="mx-auto max-w-2xl px-4 py-10 text-sm text-slate-500">Loading…</div>;
  }

  const isAdmin = user.role === "admin";
  const myAssignment = job.assignments.find((a) => a.cleaner.user?.id === user.id);
  const hasOffer = myAssignment?.status === "offered";

  async function withBusy(fn) {
    setBusy(true);
    try {
      await fn();
      await load();
    } finally {
      setBusy(false);
    }
  }

  const generateShortlist = () => withBusy(() => api.get(`/jobs/${id}/shortlist/`));
  const assignCleaner = (cleanerId) => withBusy(() => api.post(`/jobs/${id}/assign/`, { cleaner_id: cleanerId }));
  const respond = (accept) => withBusy(() => api.post(`/jobs/${id}/respond/`, { accept }));
  const complete = () => withBusy(() => api.post(`/jobs/${id}/complete/`));
  const sendPacket = () => withBusy(() => api.post(`/jobs/${id}/packet/`, packet));

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-semibold text-white">{job.location_summary}</h1>
            <p className="mt-1 text-sm text-slate-300">
              {job.customer?.full_name} · {job.requested_date}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <UrgencyBadge urgency={job.urgency} />
            <StatusBadge status={job.status} />
          </div>
        </div>

        <div className="card mt-6 divide-y divide-white/10">
          <div className="p-5 text-sm">
            <dl className="grid grid-cols-2 gap-y-2">
              <dt className="text-slate-300">Cleaners needed</dt>
              <dd className="text-white">{job.cleaners_needed}</dd>
              <dt className="text-slate-300">Gender preference</dt>
              <dd className="text-white capitalize">{job.gender_preference}</dd>
              {job.requires_access_code && (
                <>
                  <dt className="text-slate-300">Access code location</dt>
                  <dd className="text-white">{job.access_code_location}</dd>
                </>
              )}
              {job.access_code && (
                <>
                  <dt className="text-slate-300">Access code</dt>
                  <dd className="font-mono text-white">{job.access_code}</dd>
                </>
              )}
              {job.start_time && (
                <>
                  <dt className="text-slate-300">Start time</dt>
                  <dd className="text-white">{job.start_time}</dd>
                </>
              )}
              {job.special_instructions && (
                <>
                  <dt className="text-slate-300">Instructions</dt>
                  <dd className="text-white">{job.special_instructions}</dd>
                </>
              )}
            </dl>
          </div>

          {isAdmin && (job.status === "requested" || job.status === "shortlisted") && (
            <div className="p-5">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-white">Recommended cleaners</h2>
                <button className="btn-secondary text-xs" disabled={busy} onClick={generateShortlist}>
                  {job.assignments.length ? "Refresh shortlist" : "Generate shortlist"}
                </button>
              </div>
              <CleanerShortlist assignments={job.assignments} onAssign={assignCleaner} assigning={busy} />
            </div>
          )}

          {!isAdmin && hasOffer && (
            <div className="flex gap-2 p-5">
              <button className="btn-primary flex-1" disabled={busy} onClick={() => respond(true)}>
                Accept job
              </button>
              <button className="btn-secondary flex-1" disabled={busy} onClick={() => respond(false)}>
                Decline
              </button>
            </div>
          )}

          {isAdmin && job.status === "accepted" && (
            <div className="space-y-3 p-5">
              <h2 className="text-sm font-semibold text-white">Send job packet</h2>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Start time</label>
                  <input
                    type="time"
                    className="field"
                    value={packet.start_time}
                    onChange={(e) => setPacket((p) => ({ ...p, start_time: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="label">Timeframe (minutes)</label>
                  <input
                    type="number"
                    className="field"
                    value={packet.timeframe_minutes}
                    onChange={(e) => setPacket((p) => ({ ...p, timeframe_minutes: e.target.value }))}
                  />
                </div>
              </div>
              <div>
                <label className="label">Special instructions</label>
                <textarea
                  className="field"
                  rows={3}
                  value={packet.special_instructions}
                  onChange={(e) => setPacket((p) => ({ ...p, special_instructions: e.target.value }))}
                />
              </div>
              <button className="btn-primary w-full" disabled={busy} onClick={sendPacket}>
                Send packet to cleaner
              </button>
            </div>
          )}

          {job.status === "in_progress" && (
            <div className="p-5">
              <button className="btn-primary w-full" disabled={busy} onClick={complete}>
                Mark job completed
              </button>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
