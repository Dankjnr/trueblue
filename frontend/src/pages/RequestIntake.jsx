import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import api from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

const emptyForm = {
  customer_full_name: "",
  customer_phone: "",
  location_summary: "",
  cleaners_needed: 1,
  gender_preference: "any",
  requested_date: "",
  requires_access_code: false,
  access_code_location: "",
  access_code: "",
};

export default function RequestIntake() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user?.role === "admin";
  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  function update(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      let customerId = null;
      if (isAdmin) {
        const customerRes = await api.post("/customers/", {
          full_name: form.customer_full_name,
          phone_number: form.customer_phone,
        });
        customerId = customerRes.data.id;
      }

      const payload = {
        location_summary: form.location_summary,
        cleaners_needed: Number(form.cleaners_needed),
        gender_preference: form.gender_preference,
        requested_date: form.requested_date,
        requires_access_code: form.requires_access_code,
        access_code_location: form.requires_access_code ? form.access_code_location : "",
        access_code: form.requires_access_code ? form.access_code : "",
        intake_channel: isAdmin ? "phone" : "app",
        ...(isAdmin ? { customer: customerId } : {}),
      };
      const res = await api.post("/jobs/", payload);
      navigate(`/jobs/${res.data.id}`);
    } catch (err) {
      const data = err?.response?.data;
      const fieldErrors = Object.entries(data || {})
        .flatMap(([key, value]) => (Array.isArray(value) ? value : [value]))
        .filter(Boolean)
        .map((item) => (typeof item === "string" ? item : item?.detail || item?.message || "This field is invalid."));
      setError(fieldErrors[0] || data?.detail || "Something didn't validate — check the fields and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-[1100px] px-3 py-6 md:px-4 md:py-8">
      <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
        <div className="rounded-[24px] border border-[#2a3947] bg-[#111b26] p-5 text-white shadow-[0_20px_50px_rgba(15,23,42,0.18)] md:p-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-300">TrueBlue</p>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight md:text-3xl">
            {isAdmin ? "Phone-in request" : "Request a cleaner"}
          </h1>
          <p className="mt-3 max-w-md text-sm text-slate-200">
            {isAdmin
              ? "Capture the job details and let the system shortlist suitable cleaners in seconds."
              : "Tell us where you need help and when. We’ll match the right cleaner and keep the process transparent."}
          </p>

          <div className="mt-8 grid gap-3">
            {[
              ["Fast matching", "Eligibility and readiness filters"],
              ["Status visibility", "Track requests from intake to completion"],
              ["Secure handoff", "Access details shared only when needed"],
            ].map(([title, copy]) => (
              <div key={title} className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm">
                <div className="text-sm font-medium text-white">{title}</div>
                <div className="mt-1 text-xs text-slate-300">{copy}</div>
              </div>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="card mt-2 space-y-4 p-4 md:p-5">
          {isAdmin && (
            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="label">Customer name</label>
                <input
                  className="field"
                  value={form.customer_full_name}
                  onChange={(e) => update("customer_full_name", e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="label">Customer phone</label>
                <input
                  className="field"
                  value={form.customer_phone}
                  onChange={(e) => update("customer_phone", e.target.value)}
                  required
                />
              </div>
            </div>
          )}

          <div>
            <label className="label">Location</label>
            <input
              className="field"
              placeholder="e.g. 14 Okpanam Road, Asaba"
              value={form.location_summary}
              onChange={(e) => update("location_summary", e.target.value)}
              required
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <label className="label">Cleaners needed</label>
              <input
                type="number"
                min={1}
                className="field"
                value={form.cleaners_needed}
                onChange={(e) => update("cleaners_needed", e.target.value)}
                required
              />
            </div>
            <div className="sm:col-span-2">
              <label className="label">Gender preference</label>
              <select
                className="field"
                value={form.gender_preference}
                onChange={(e) => update("gender_preference", e.target.value)}
              >
                <option value="any">No preference</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>
          </div>

          <div>
            <label className="label">Date needed</label>
            <input
              type="date"
              className="field"
              value={form.requested_date}
              onChange={(e) => update("requested_date", e.target.value)}
              required
            />
          </div>

          <label className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={form.requires_access_code}
              onChange={(e) => update("requires_access_code", e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 accent-sky-600"
            />
            This job needs an access code
          </label>

          <AnimatePresence initial={false}>
            {form.requires_access_code && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.18 }}
                className="grid gap-3 overflow-hidden md:grid-cols-2"
              >
                <div>
                  <label className="label">Where it applies</label>
                  <input
                    className="field"
                    placeholder="e.g. estate gate"
                    value={form.access_code_location}
                    onChange={(e) => update("access_code_location", e.target.value)}
                  />
                </div>
                <div>
                  <label className="label">Access code</label>
                  <input
                    className="field"
                    value={form.access_code}
                    onChange={(e) => update("access_code", e.target.value)}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {error && <p className="text-sm text-rose-600">{error}</p>}

          <button className="btn-primary w-full" disabled={submitting}>
            {submitting ? "Submitting…" : "Submit request"}
          </button>
        </form>
      </div>
    </div>
  );
}
