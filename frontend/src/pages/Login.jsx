import { motion } from "framer-motion";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

const roleOptions = [
  { value: "customer", label: "Customer" },
  { value: "cleaner", label: "Cleaner" },
  { value: "admin", label: "Admin" },
];

export default function Login() {
  const { loginWithPassword, requestOtp, verifyOtp, registerAccount } = useAuth();
  const navigate = useNavigate();
  const [authView, setAuthView] = useState("signin");
  const [loginMode, setLoginMode] = useState("password");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("customer");

  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [otpSent, setOtpSent] = useState(false);

  const [regForm, setRegForm] = useState({
    username: "",
    first_name: "",
    last_name: "",
    phone_number: "",
    password: "",
    role: "customer",
    gender: "female",
  });

  const roleLabel = useMemo(
    () => roleOptions.find((option) => option.value === role)?.label || "Customer",
    [role],
  );

  function normalizeRole(value) {
    return roleOptions.some((option) => option.value === value) ? value : "customer";
  }

  function updateRegistration(field, value) {
    setRegForm((current) => ({ ...current, [field]: value }));
  }

  async function handlePasswordLogin(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setLoading(true);
    try {
      const selectedRole = normalizeRole(role);
      await loginWithPassword(username.trim(), password, selectedRole);
      navigate("/");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || "That username or password wasn’t recognised.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRequestOtp(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setLoading(true);
    try {
      const response = await requestOtp(phone.trim());
      setOtpSent(true);
      if (response?.debug_code) {
        setInfo(`Development mode is active. Use code ${response.debug_code} to continue.`);
      }
    } catch {
      setError("The code could not be sent. Check the number and try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOtp(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setLoading(true);
    try {
      await verifyOtp(phone.trim(), code.trim(), normalizeRole(role));
      navigate("/");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || "That code didn’t match the last SMS sent.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    setError("");
    setInfo("");
    setLoading(true);
    try {
      await registerAccount({
        username: regForm.username,
        first_name: regForm.first_name,
        last_name: regForm.last_name,
        phone_number: regForm.phone_number,
        password: regForm.password,
        role: regForm.role,
        ...(regForm.role === "cleaner" ? { gender: regForm.gender } : {}),
      });
      navigate("/");
    } catch (err) {
      const detail = err?.response?.data?.non_field_errors || err?.response?.data?.detail;
      const firstFieldError = Object.values(err?.response?.data || {}).flat().find(Boolean);
      setError(firstFieldError || detail || "We couldn’t create that account right now.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell min-h-screen px-4 py-8 md:px-6">
      <div className="mx-auto grid max-w-[1400px] overflow-hidden bg-[#11161b] lg:grid-cols-[1.12fr_0.88fr]">
        <motion.div
          initial={{ opacity: 0, x: -18 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
          className="relative flex min-h-[420px] items-center justify-center overflow-hidden bg-[#78aee9] p-6 text-[#0f172a] sm:p-8 lg:min-h-[520px] lg:p-12"
        >
          <div className="pointer-events-none absolute inset-0 opacity-70">
            <div className="absolute left-12 top-12 h-32 w-32 rounded-full bg-white/10 blur-3xl" />
            <div className="absolute bottom-10 left-1/2 h-44 w-44 -translate-x-1/2 rounded-full bg-[#5e95d5]/30 blur-3xl" />
          </div>

          <div className="relative z-10 flex flex-col items-center justify-center text-center">
            <div className="mb-8 flex h-28 w-28 items-center justify-center overflow-hidden rounded-[28px] border border-white/40 bg-white/12 shadow-lg shadow-[#5a87bf]/20">
              <img
                src="https://www.vhv.rs/dpng/d/493-4930851_happy-clean-happy-cleaning-hd-png-download.png"
                alt="Cleaner mascot"
                className="h-full w-full object-cover"
              />
            </div>
            <h1 className="text-[38px] font-medium leading-none text-white sm:text-[46px] md:text-[56px] lg:text-[62px]">
              TrueBlue
            </h1>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 18 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
          className="bg-[#11161b] p-6 text-white md:p-8 lg:p-10"
        >
          <div className="mb-8">
            <h2 className="text-[30px] font-medium leading-tight text-white sm:text-[36px] lg:text-[44px]">
              {authView === "signin" ? "Welcome back" : "Create account"}
            </h2>
            <p className="mt-2 text-base text-slate-300 sm:text-lg lg:text-[20px]">
              {authView === "signin" ? "Sign in to continue as customer" : "Create a profile to get started"}
            </p>
          </div>

          <div className="mb-6 flex rounded-xl border border-[#2d343b] bg-[#1d2228] p-1 text-lg">
            {[
              { value: "signin", label: "Sign in" },
              { value: "register", label: "Register" },
            ].map((item) => (
              <button
                key={item.value}
                type="button"
                onClick={() => {
                  setAuthView(item.value);
                  setError("");
                  setInfo("");
                  setShowForgotPassword(false);
                }}
                className={`flex-1 rounded-lg px-3 py-3 font-medium transition-colors ${
                  authView === item.value ? "bg-[#2a3037] text-white" : "text-slate-300"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          {authView === "signin" ? (
            <>
              <div className="mb-6 flex rounded-xl border border-[#2d343b] bg-[#1d2228] p-1 text-lg">
                {[
                  { value: "password", label: "Password" },
                  { value: "otp", label: "Phone code" },
                ].map((item) => (
                  <button
                    key={item.value}
                    type="button"
                    onClick={() => {
                      setLoginMode(item.value);
                      setOtpSent(false);
                      setError("");
                      setInfo("");
                      setShowForgotPassword(false);
                    }}
                    className={`flex-1 rounded-lg px-3 py-3 font-medium transition-colors ${
                      loginMode === item.value ? "bg-[#2a3037] text-white" : "text-slate-300"
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>

              {loginMode === "password" ? (
                <form onSubmit={handlePasswordLogin} className="space-y-5">
                  <div>
                    <label className="label">Role</label>
                    <select className="field" value={role} onChange={(e) => setRole(e.target.value)}>
                      {roleOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label">Username</label>
                    <input className="field" value={username} onChange={(e) => setUsername(e.target.value)} required />
                  </div>
                  <div>
                    <label className="label">Password</label>
                    <div className="relative">
                      <input
                        type={showPassword ? "text" : "password"}
                        className="field pr-12"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword((value) => !value)}
                        className="absolute inset-y-0 right-3 flex items-center text-slate-300 transition hover:text-white"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? (
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5">
                            <path d="M3 3l18 18" strokeLinecap="round" />
                            <path d="M10.58 10.58A2 2 0 0013.42 13.42" strokeLinecap="round" />
                            <path d="M9.88 5.08A10.82 10.82 0 0112 5c4.97 0 9 3.5 9 7 0 1.16-.27 2.27-.75 3.28" strokeLinecap="round" />
                            <path d="M6.61 6.61A14.1 14.1 0 003 12c0 3.5 4.03 7 9 7 1.77 0 3.42-.38 4.87-1.05" strokeLinecap="round" />
                          </svg>
                        ) : (
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5">
                            <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" strokeLinecap="round" strokeLinejoin="round" />
                            <circle cx="12" cy="12" r="3" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center justify-end">
                    <button
                      type="button"
                      onClick={() => setShowForgotPassword((value) => !value)}
                      className="text-[18px] font-medium text-[#5ca7ff] hover:text-[#79b6ff]"
                    >
                      Forgot password?
                    </button>
                  </div>

                  {showForgotPassword && (
                    <div className="rounded-xl border border-[#2d343b] bg-[#1d2228] p-3 text-base text-slate-300">
                      Password reset is not enabled in this build. Use the phone-code sign-in flow or contact an admin.
                    </div>
                  )}

                  {error && <p className="text-base text-rose-300">{error}</p>}
                  {info && <p className="text-base text-emerald-300">{info}</p>}
                  <button type="submit" className="btn-primary w-full rounded-xl py-3 text-base font-medium sm:py-4 sm:text-lg lg:text-[22px]" disabled={loading}>
                    {loading ? "Signing in…" : "Continue"}
                  </button>
                </form>
              ) : !otpSent ? (
                <form onSubmit={handleRequestOtp} className="space-y-5">
                  <div>
                    <label className="label">Phone number</label>
                    <input
                      className="field"
                      placeholder="+234…"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      required
                    />
                  </div>
                  {error && <p className="text-base text-rose-300">{error}</p>}
                  {info && <p className="text-base text-emerald-300">{info}</p>}
                  <button type="submit" className="btn-primary w-full rounded-xl py-3 text-base font-medium sm:py-4 sm:text-lg lg:text-[22px]" disabled={loading}>
                    {loading ? "Sending…" : "Send code"}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleVerifyOtp} className="space-y-5">
                  <div>
                    <label className="label">6-digit code</label>
                    <input className="field tracking-[0.3em] text-center" maxLength={6} value={code} onChange={(e) => setCode(e.target.value)} required />
                  </div>
                  {error && <p className="text-base text-rose-300">{error}</p>}
                  {info && <p className="text-base text-emerald-300">{info}</p>}
                  <button type="submit" className="btn-primary w-full rounded-xl py-3 text-base font-medium sm:py-4 sm:text-lg lg:text-[22px]" disabled={loading}>
                    {loading ? "Verifying…" : "Verify & continue"}
                  </button>
                  <button type="button" className="btn-ghost w-full text-base" onClick={() => setOtpSent(false)}>
                    Use a different number
                  </button>
                </form>
              )}
            </>
          ) : (
            <form onSubmit={handleRegister} className="space-y-5">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="label">First name</label>
                  <input value={regForm.first_name} onChange={(e) => updateRegistration("first_name", e.target.value)} className="field" required />
                </div>
                <div>
                  <label className="label">Last name</label>
                  <input value={regForm.last_name} onChange={(e) => updateRegistration("last_name", e.target.value)} className="field" required />
                </div>
              </div>

              <div>
                <label className="label">Username</label>
                <input value={regForm.username} onChange={(e) => updateRegistration("username", e.target.value)} className="field" required />
              </div>

              <div>
                <label className="label">Phone number</label>
                <input value={regForm.phone_number} onChange={(e) => updateRegistration("phone_number", e.target.value)} className="field" placeholder="+234…" required />
              </div>

              <div>
                <label className="label">Create role</label>
                <select value={regForm.role} onChange={(e) => updateRegistration("role", e.target.value)} className="field">
                  <option value="customer">Customer</option>
                  <option value="cleaner">Cleaner</option>
                </select>
              </div>

              {regForm.role === "cleaner" && (
                <div>
                  <label className="label">Gender</label>
                  <select value={regForm.gender} onChange={(e) => updateRegistration("gender", e.target.value)} className="field">
                    <option value="female">Female</option>
                    <option value="male">Male</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              )}

              <div>
                <label className="label">Password</label>
                <div className="relative">
                  <input
                    type={showRegisterPassword ? "text" : "password"}
                    value={regForm.password}
                    onChange={(e) => updateRegistration("password", e.target.value)}
                    className="field pr-12"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowRegisterPassword((value) => !value)}
                    className="absolute inset-y-0 right-3 flex items-center text-slate-300 transition hover:text-white"
                    aria-label={showRegisterPassword ? "Hide password" : "Show password"}
                  >
                    {showRegisterPassword ? (
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5">
                        <path d="M3 3l18 18" strokeLinecap="round" />
                        <path d="M10.58 10.58A2 2 0 0013.42 13.42" strokeLinecap="round" />
                        <path d="M9.88 5.08A10.82 10.82 0 0112 5c4.97 0 9 3.5 9 7 0 1.16-.27 2.27-.75 3.28" strokeLinecap="round" />
                        <path d="M6.61 6.61A14.1 14.1 0 003 12c0 3.5 4.03 7 9 7 1.77 0 3.42-.38 4.87-1.05" strokeLinecap="round" />
                      </svg>
                    ) : (
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5">
                        <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" strokeLinecap="round" strokeLinejoin="round" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {error && <p className="text-base text-rose-300">{error}</p>}
              {info && <p className="text-base text-emerald-300">{info}</p>}
              <button type="submit" className="btn-primary w-full rounded-xl py-3 text-base font-medium sm:py-4 sm:text-lg lg:text-[22px]" disabled={loading}>
                {loading ? "Creating account…" : "Create account"}
              </button>
            </form>
          )}
        </motion.div>
      </div>
    </div>
  );
}
