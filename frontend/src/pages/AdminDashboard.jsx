import { AnimatePresence } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import api from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import JobCard from "../components/JobCard.jsx";

const URGENCY_ORDER = { green: 0, orange: 1, red: 2 };

export default function AdminDashboard() {
  const { user, promoteAdmin } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState("urgency");
  const [adminUsername, setAdminUsername] = useState("");
  const [adminMessage, setAdminMessage] = useState("");
  const [adminError, setAdminError] = useState("");
  const [promoting, setPromoting] = useState(false);
  const [toolsOpen, setToolsOpen] = useState(false);

  useEffect(() => {
    api.get("/jobs/").then((res) => {
      setJobs(res.data.results ?? res.data);
      setLoading(false);
    });
  }, []);

  const visibleJobs = useMemo(() => {
    let list = jobs;
    if (statusFilter !== "all") {
      list = list.filter((j) => j.status === statusFilter);
    }
    return [...list].sort((a, b) => {
      if (sortBy === "urgency") return URGENCY_ORDER[a.urgency] - URGENCY_ORDER[b.urgency];
      return new Date(a.requested_date) - new Date(b.requested_date);
    });
  }, [jobs, statusFilter, sortBy]);

  const counts = useMemo(() => {
    return jobs.reduce(
      (acc, j) => {
        acc[j.urgency] = (acc[j.urgency] || 0) + 1;
        return acc;
      },
      { green: 0, orange: 0, red: 0 }
    );
  }, [jobs]);

  async function handlePromoteAdmin(e) {
    e.preventDefault();
    setAdminError("");
    setAdminMessage("");
    const username = adminUsername.trim();
    if (!username) {
      setAdminError("Enter a username to upgrade.");
      return;
    }

    setPromoting(true);
    try {
      const response = await promoteAdmin({ username });
      setAdminMessage(response.detail || "User promoted to admin.");
      setAdminUsername("");
    } catch (err) {
      setAdminError(err?.response?.data?.detail || "User could not be promoted.");
    } finally {
      setPromoting(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#11161b] px-4 py-8 md:px-6 md:py-10">
      <div className="mx-auto max-w-6xl rounded-[18px] bg-[#12171d] p-4 md:p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-[12px] font-medium uppercase tracking-[0.18em] text-slate-400">TrueBlue</p>
            <h1 className="mt-2 text-[32px] font-medium text-white md:text-[42px]">Operations dashboard</h1>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setToolsOpen((value) => !value)}
              className="rounded-xl border border-[#2b3036] bg-[#1d2127] px-4 py-3 text-base font-medium text-white"
            >
              Admin tools
            </button>
            <Link to="/jobs/new" className="btn-primary rounded-xl px-5 py-3 text-base font-medium">
              Log phone-in request
            </Link>
          </div>
        </div>

        {toolsOpen && user?.role === "admin" && (
          <form onSubmit={handlePromoteAdmin} className="mt-6 rounded-[12px] border border-[#2b3036] bg-[#171c22] p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-end">
              <div className="flex-1">
                <label className="label">Upgrade a user</label>
                <input
                  className="field"
                  type="text"
                  value={adminUsername}
                  onChange={(e) => setAdminUsername(e.target.value)}
                  placeholder="Username"
                />
              </div>
              <button type="submit" className="btn-secondary md:min-w-[180px]" disabled={promoting}>
                {promoting ? "Updating…" : "Upgrade user"}
              </button>
            </div>
            {adminError && <p className="mt-3 text-sm text-rose-300">{adminError}</p>}
            {adminMessage && <p className="mt-3 text-sm text-emerald-300">{adminMessage}</p>}
          </form>
        )}

        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {[
            { value: counts.green, label: "Today", tone: "success" },
            { value: counts.orange, label: "Tomorrow", tone: "warning" },
            { value: counts.red, label: "Later", tone: "danger" },
          ].map((item) => (
            <div key={item.label} className="rounded-[12px] border border-[#2b3036] bg-[#171c22] p-4">
              <div className={`border-l-4 pl-3 text-[26px] font-semibold ${
                item.tone === "success" ? "border-emerald-500 text-white" :
                item.tone === "warning" ? "border-amber-500 text-white" :
                "border-red-500 text-white"}`}>
                {item.value}
              </div>
              <div className="mt-3 text-[15px] text-slate-200">{item.label}</div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex flex-col gap-3 md:flex-row md:items-center">
          <select className="field w-full md:w-auto" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">All statuses</option>
            <option value="requested">Requested</option>
            <option value="shortlisted">Shortlisted</option>
            <option value="assigned">Awaiting response</option>
            <option value="accepted">Accepted</option>
            <option value="in_progress">In progress</option>
            <option value="completed">Completed</option>
            <option value="declined">Declined</option>
          </select>
          <select className="field w-full md:w-auto" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="urgency">Sort by urgency</option>
            <option value="date">Sort by date</option>
          </select>
        </div>

        {loading ? (
          <p className="mt-8 text-sm text-slate-500">Loading jobs…</p>
        ) : visibleJobs.length === 0 ? (
          <p className="mt-8 text-sm text-slate-500">No jobs match this filter.</p>
        ) : (
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            <AnimatePresence initial={false}>
              {visibleJobs.map((job) => (
                <JobCard key={job.id} job={job} />
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
}
