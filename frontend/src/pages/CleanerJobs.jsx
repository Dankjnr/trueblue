import { useEffect, useState } from "react";

import api from "../api/client.js";
import JobCard from "../components/JobCard.jsx";

export default function CleanerJobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/jobs/").then((res) => {
      setJobs(res.data.results ?? res.data);
      setLoading(false);
    });
  }, []);

  const ongoing = jobs.filter((job) => ["assigned", "accepted", "in_progress"].includes(job.status));
  const completed = jobs.filter((job) => job.status === "completed");
  const offers = jobs.filter((job) => ["requested", "shortlisted", "assigned"].includes(job.status));

  return (
    <div className="min-h-[calc(100vh-72px)] bg-[#11161b] px-4 py-10">
      <div className="mx-auto max-w-6xl px-2">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-medium text-white md:text-4xl">
            Hi Chidera, {ongoing.length} job{ongoing.length === 1 ? "" : "s"} today
          </h1>
        </div>

        {loading ? (
          <p className="mt-10 text-center text-lg text-slate-300">Loading…</p>
        ) : jobs.length === 0 ? (
          <p className="mt-10 text-center text-xl text-slate-300">Nothing here yet.</p>
        ) : (
          <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <div className="space-y-3">
              {offers.length === 0 ? (
                <div className="rounded-[16px] border border-[#2b3036] bg-[#171b20] p-6 text-center text-lg text-slate-300">
                  No active offers right now.
                </div>
              ) : (
                offers.map((job) => (
                  <JobCard key={job.id} job={job} />
                ))
              )}
            </div>

            <aside className="rounded-[18px] border border-[#2b3036] bg-[#171b20] p-4 md:p-5">
              <div className="mb-4">
                <h2 className="text-xl font-medium text-white">Overview</h2>
              </div>
              <div className="space-y-3 text-slate-200">
                <div className="flex items-center justify-between rounded-xl border border-[#2b3036] bg-[#1d2127] px-3 py-3">
                  <span>Offers</span>
                  <span className="text-lg font-semibold text-white">{offers.length}</span>
                </div>
                <div className="flex items-center justify-between rounded-xl border border-[#2b3036] bg-[#1d2127] px-3 py-3">
                  <span>Ongoing</span>
                  <span className="text-lg font-semibold text-white">{ongoing.length}</span>
                </div>
                <div className="flex items-center justify-between rounded-xl border border-[#2b3036] bg-[#1d2127] px-3 py-3">
                  <span>Completed</span>
                  <span className="text-lg font-semibold text-white">{completed.length}</span>
                </div>
              </div>
            </aside>
          </div>
        )}
      </div>
    </div>
  );
}
