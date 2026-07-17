"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import AppShell from "@/components/AppShell";
import { toast } from "sonner";

export default function ReferralsPage() {
  const router = useRouter();
  const { user, loading: authLoading, authFetch } = useAuth();
  const [code, setCode] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push("/login");
      return;
    }
    load();
  }, [user, authLoading, router]);

  async function load() {
    const [cRes, sRes] = await Promise.all([
      authFetch("/api/v1/referrals/code"),
      authFetch("/api/v1/referrals/stats"),
    ]);
    if (cRes.ok) setCode(await cRes.json());
    if (sRes.ok) setStats(await sRes.json());
  }

  async function invite(e: React.FormEvent) {
    e.preventDefault();
    setSending(true);
    try {
      const res = await authFetch("/api/v1/referrals/invite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || data.message || "Invite failed");
      toast.success(data.message || "Invite sent");
      setEmail("");
      await load();
    } catch (err: any) {
      toast.error(err.message || "Invite failed");
    } finally {
      setSending(false);
    }
  }

  async function copyLink() {
    if (!code?.link) return;
    await navigator.clipboard.writeText(code.link);
    toast.success("Referral link copied");
  }

  return (
    <AppShell>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Referrals</h1>
        <p className="text-sm text-slate-500 mt-1">
          Share JobScale — tracked invites only (credits are account ledger, not fake Stripe balance until claimed).
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-3">
          <p className="text-xs uppercase tracking-wide text-slate-400">Your code</p>
          <p className="text-2xl font-semibold tracking-wide text-slate-900">{code?.code || "—"}</p>
          <p className="text-xs text-slate-500 break-all">{code?.link}</p>
          <button
            type="button"
            onClick={copyLink}
            className="px-3 py-2 text-sm font-semibold rounded-lg bg-slate-900 text-white"
          >
            Copy link
          </button>
          <div className="pt-4 border-t border-slate-100 grid grid-cols-3 gap-2 text-center">
            <div>
              <p className="text-lg font-semibold tabular-nums">{code?.total_referrals ?? 0}</p>
              <p className="text-xs text-slate-500">Total</p>
            </div>
            <div>
              <p className="text-lg font-semibold tabular-nums">{code?.successful_referrals ?? 0}</p>
              <p className="text-xs text-slate-500">Successful</p>
            </div>
            <div>
              <p className="text-lg font-semibold tabular-nums">${code?.earnings ?? 0}</p>
              <p className="text-xs text-slate-500">Credits</p>
            </div>
          </div>
        </div>

        <form onSubmit={invite} className="bg-white border border-slate-200 rounded-xl p-6 space-y-3">
          <h2 className="text-sm font-semibold text-slate-900">Invite a friend</h2>
          <input
            type="email"
            required
            placeholder="friend@email.com"
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button
            type="submit"
            disabled={sending}
            className="px-4 py-2 text-sm font-semibold rounded-lg bg-teal-500 text-white disabled:opacity-50"
          >
            {sending ? "Sending…" : "Send invite"}
          </button>
        </form>
      </div>

      {stats?.referrals?.length > 0 && (
        <div className="mt-8 bg-white border border-slate-200 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-200 text-sm font-semibold">Invite history</div>
          <ul className="divide-y divide-slate-100">
            {stats.referrals.map((r: any, i: number) => (
              <li key={i} className="px-5 py-3 text-sm flex justify-between">
                <span>{r.email}</span>
                <span className="text-slate-500">{r.status}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </AppShell>
  );
}
