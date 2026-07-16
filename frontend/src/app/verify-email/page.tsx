"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { getApiBase } from "@/lib/apiBase";

function VerifyInner() {
  const params = useSearchParams();
  const token = params.get("token") || "";
  const [status, setStatus] = useState<"pending" | "ok" | "error">("pending");
  const [message, setMessage] = useState("Verifying…");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("Missing verification token");
      return;
    }
    (async () => {
      try {
        const res = await fetch(`${getApiBase()}/auth/verify-email`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || "Verification failed");
        setStatus("ok");
        setMessage(data.message || "Email verified");
      } catch (err: any) {
        setStatus("error");
        setMessage(err.message || "Verification failed");
      }
    })();
  }, [token]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm bg-white border border-slate-200 rounded-xl p-6 text-center space-y-3">
        <h1 className="text-xl font-semibold text-slate-900">Email verification</h1>
        <p className={`text-sm ${status === "error" ? "text-red-600" : "text-teal-700"}`}>{message}</p>
        <Link href="/login" className="inline-block text-sm font-medium text-navy-900 underline">
          Continue to sign in
        </Link>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-500">Loading…</div>}>
      <VerifyInner />
    </Suspense>
  );
}
