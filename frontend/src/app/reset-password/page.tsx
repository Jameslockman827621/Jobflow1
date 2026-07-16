"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { getApiBase } from "@/lib/apiBase";

function ResetForm() {
  const params = useSearchParams();
  const router = useRouter();
  const token = params.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setMsg("");
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    if (!token) {
      setError("Missing reset token — use the link from your email");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${getApiBase()}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || "Reset failed");
      setMsg(data.message || "Password updated");
      setTimeout(() => router.push("/login"), 1500);
    } catch (err: any) {
      setError(err.message || "Reset failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm bg-white border border-slate-200 rounded-xl p-6 space-y-4">
        <h1 className="text-xl font-semibold text-slate-900">Reset password</h1>
        {error && <p className="text-sm text-red-600">{error}</p>}
        {msg && <p className="text-sm text-teal-700">{msg}</p>}
        <input
          type="password"
          placeholder="New password"
          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Confirm password"
          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 text-sm font-semibold rounded-lg bg-navy-900 text-white disabled:opacity-50"
        >
          {loading ? "Updating…" : "Update password"}
        </button>
        <Link href="/login" className="block text-center text-sm text-teal-600">
          Back to sign in
        </Link>
      </form>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-500">Loading…</div>}>
      <ResetForm />
    </Suspense>
  );
}
