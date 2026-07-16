"use client";

import { useState } from "react";
import Link from "next/link";
import { getApiBase } from "@/lib/apiBase";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMsg("");
    try {
      const res = await fetch(`${getApiBase()}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json().catch(() => ({}));
      setMsg(data.message || "If that email is registered, a reset link has been sent.");
    } catch {
      setMsg("Could not send reset email. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm bg-white border border-slate-200 rounded-xl p-6 space-y-4">
        <h1 className="text-xl font-semibold text-slate-900">Forgot password</h1>
        <p className="text-sm text-slate-500">We will email a reset link if an account exists for that address.</p>
        <input
          type="email"
          required
          placeholder="Email"
          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        {msg && <p className="text-sm text-teal-700">{msg}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 text-sm font-semibold rounded-lg bg-navy-900 text-white disabled:opacity-50"
        >
          {loading ? "Sending…" : "Send reset link"}
        </button>
        <Link href="/login" className="block text-center text-sm text-teal-600">
          Back to sign in
        </Link>
      </form>
    </div>
  );
}
