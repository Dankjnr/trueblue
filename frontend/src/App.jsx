import { useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";

import api from "./api/client.js";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import { useAuth } from "./context/AuthContext.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import CleanerJobs from "./pages/CleanerJobs.jsx";
import JobDetail from "./pages/JobDetail.jsx";
import Login from "./pages/Login.jsx";
import RequestIntake from "./pages/RequestIntake.jsx";

function CustomerDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    api.get("/jobs/").then((res) => {
      setJobs(res.data.results ?? res.data);
    });
  }, []);

  const summary = useMemo(() => {
    const active = jobs.filter((job) => !["completed", "cancelled", "declined"].includes(job.status));
    const current = [...jobs]
      .filter((job) => !["completed", "cancelled", "declined"].includes(job.status))
      .sort((a, b) => new Date(b.requested_date) - new Date(a.requested_date))[0];
    const recent = [...jobs].sort((a, b) => new Date(b.requested_date) - new Date(a.requested_date)).slice(0, 4);

    return { active: active.length, current, recent };
  }, [jobs]);

  const statusText = {
    requested: "Requested",
    assigned: "Cleaner assigned",
    accepted: "Cleaner accepted",
    in_progress: "In progress",
    completed: "Completed",
    declined: "Declined",
    cancelled: "Cancelled",
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 md:px-6 md:py-10">
      <div className="rounded-[24px] border border-[#2b3947] bg-[#111b26] p-5 text-white shadow-[0_20px_50px_rgba(15,23,42,0.18)] md:p-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-3xl font-medium text-white md:text-5xl">
              Welcome back, {user?.first_name || user?.username || "there"}
            </h1>
            <p className="mt-2 text-lg text-slate-200">
              {summary.active} active request{summary.active === 1 ? "" : "s"}, {jobs.filter((job) => job.status === "completed").length} completed
            </p>
          </div>
          <button className="btn-primary h-14 min-w-[190px] rounded-xl text-lg font-medium" onClick={() => navigate("/jobs/new")}>
            + New request
          </button>
        </div>

        <div className="mt-8 rounded-[18px] border border-[#2b3947] bg-[#1a2430] p-4 md:p-5">
          {summary.current ? (
            <>
              <div className="flex items-start justify-between gap-3">
                <div className="text-xl font-medium text-white md:text-2xl">
                  {new Date(summary.current.requested_date).toLocaleDateString("en-GB", { day: "numeric", month: "short" })} · {statusText[summary.current.status] || "Active"}
                </div>
                <span className="inline-flex rounded-full bg-[#2b9d69] px-3 py-1 text-sm font-medium text-white">
                  {summary.current.status === "completed" ? "Completed" : "Confirmed"}
                </span>
              </div>
              <div className="mt-5 flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#5e85d5] text-lg font-semibold text-white">
                  {(summary.current.assigned_cleaner?.name || "CO").slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <div className="text-2xl font-medium text-white">{summary.current.assigned_cleaner?.name || "Cleaner assigned"}</div>
                  <div className="mt-1 text-base text-slate-200">{summary.current.location_summary || "Request in progress"}</div>
                </div>
              </div>
            </>
          ) : (
            <div className="py-6 text-xl text-slate-300">No active request right now.</div>
          )}
        </div>

        <div className="mt-8">
          <h2 className="text-2xl font-medium text-white">Recent requests</h2>
          <div className="mt-4 space-y-4">
            {summary.recent.length === 0 ? (
              <div className="text-lg text-slate-300">No requests yet.</div>
            ) : (
              summary.recent.map((job) => (
                <div key={job.id} className="flex items-center justify-between border-b border-[#2b3947] py-4 text-lg text-white">
                  <div>
                    {new Date(job.requested_date).toLocaleDateString("en-GB", { day: "numeric", month: "short" })} · {job.cleaners_needed} cleaner{job.cleaners_needed > 1 ? "s" : ""}
                  </div>
                  <span className="text-slate-300">{statusText[job.status] || "Active"}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Home() {
  const { user } = useAuth();
  if (!user) return null;
  if (user.role === "admin") return <AdminDashboard />;
  if (user.role === "cleaner") return <CleanerJobs />;
  return <CustomerDashboard />;
}

function Nav() {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <header className="border-b border-[#2b3036] bg-[#11161b]">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 md:px-6">
        <div className="flex items-center gap-3 text-white">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-lg">
            ◌
          </div>
          <span className="text-3xl font-medium leading-none">TrueBlue</span>
        </div>

        <div className="flex items-center gap-3 text-sm text-slate-300">
          <span className="hidden sm:inline">{user.first_name || user.username}</span>
          <button className="btn-ghost text-xs" onClick={logout}>
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-[#0d1320] text-slate-100">
      <Nav />
      <div className="bg-[#0d1320]">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Home />
              </ProtectedRoute>
            }
          />
          <Route
            path="/jobs/new"
            element={
              <ProtectedRoute roles={["admin", "customer"]}>
                <RequestIntake />
              </ProtectedRoute>
            }
          />
          <Route
            path="/jobs/:id"
            element={
              <ProtectedRoute>
                <JobDetail />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  );
}
