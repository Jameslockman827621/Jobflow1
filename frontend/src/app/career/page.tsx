"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import AppShell from "@/components/AppShell";
import { toast } from "sonner";

type Tab = "analysis" | "goals" | "recommendations";

export default function CareerPathingPage() {
  const router = useRouter();
  const { authFetch, user, loading: authLoading } = useAuth();
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState<any>(null);
  const [goals, setGoals] = useState<any>(null);
  const [jobRecs, setJobRecs] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>("analysis");
  const [goalForm, setGoalForm] = useState({ target_roles: "", target_salary: "" });
  const [savingGoal, setSavingGoal] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push("/login");
      return;
    }
    loadAll();
  }, [authLoading, user, router]);

  async function loadAll() {
    setLoading(true);
    try {
      const [aRes, gRes, jRes] = await Promise.all([
        authFetch("/api/v1/career/analysis"),
        authFetch("/api/v1/career/goals"),
        authFetch("/api/v1/career/recommendations"),
      ]);
      if (aRes.ok) setAnalysis(await aRes.json());
      else setAnalysis(null);
      if (gRes.ok) {
        const g = await gRes.json();
        setGoals(g.goals || g);
        const roles = (g.goals?.target_roles || g.target_roles || []).join(", ");
        setGoalForm({
          target_roles: roles,
          target_salary: String(g.goals?.target_salary || g.target_salary || ""),
        });
      }
      if (jRes.ok) {
        const j = await jRes.json();
        setJobRecs(j.jobs || []);
      }
    } catch {
      toast.error("Failed to load career data");
    } finally {
      setLoading(false);
    }
  }

  async function saveGoals(e: React.FormEvent) {
    e.preventDefault();
    setSavingGoal(true);
    try {
      const res = await authFetch("/api/v1/career/goals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_roles: goalForm.target_roles
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
          target_salary: goalForm.target_salary ? Number(goalForm.target_salary) : null,
        }),
      });
      if (!res.ok) throw new Error("Save failed");
      toast.success("Goals saved");
      await loadAll();
    } catch {
      toast.error("Could not save goals");
    } finally {
      setSavingGoal(false);
    }
  }

  if (authLoading || loading) {
    return (
      <AppShell>
        <div className="flex justify-center py-24 text-slate-500 text-sm">Analyzing your career path…</div>
      </AppShell>
    );
  }

  if (!analysis) {
    return (
      <AppShell>
        <div className="max-w-lg mx-auto py-16 text-center">
          <h1 className="text-2xl font-semibold text-slate-900 mb-2">Complete your profile</h1>
          <p className="text-sm text-slate-500 mb-6">
            Add your title, experience, and skills so we can build a real career path from your data.
          </p>
          <button
            onClick={() => router.push("/profile")}
            className="px-5 py-2.5 text-sm font-semibold rounded-lg bg-teal-500 text-white hover:bg-teal-600"
          >
            Go to profile
          </button>
        </div>
      </AppShell>
    );
  }

  const progression = analysis.career_path?.progression || [];
  const level = analysis.current_level || "—";
  const gaps = analysis.skill_gaps || [];
  const recs = analysis.recommendations || [];
  const milestone = analysis.next_milestone || {};
  const trajectory = analysis.salary_trajectory || [];
  const activeIdx = progression.findIndex((p: any) =>
    String(p.title || "").toLowerCase().includes(String(level).toLowerCase())
  );

  return (
    <AppShell>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Career path</h1>
        <p className="text-sm text-slate-500 mt-1">Built from your profile — not demo content</p>
      </div>

      <div className="flex gap-1 p-1 rounded-lg mb-8 w-fit bg-white border border-slate-200">
        {(["analysis", "goals", "recommendations"] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setActiveTab(t)}
            className={`px-4 py-2 text-sm font-semibold rounded-md capitalize ${
              activeTab === t ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {activeTab === "analysis" && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Current level</p>
            <h2 className="text-xl font-semibold text-slate-900">{level}</h2>
            {milestone?.title && (
              <p className="text-sm text-slate-500 mt-2">
                Next: <span className="text-slate-800 font-medium">{milestone.title}</span>
                {milestone.timeline ? ` · ${milestone.timeline}` : ""}
              </p>
            )}
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-slate-900 mb-4">Progression ladder</h3>
            <div className="space-y-3">
              {progression.map((step: any, i: number) => (
                <div
                  key={step.title || i}
                  className={`flex items-center justify-between rounded-lg px-4 py-3 border ${
                    i === activeIdx ? "border-teal-500 bg-teal-50/50" : "border-slate-100"
                  }`}
                >
                  <div>
                    <p className="text-sm font-medium text-slate-900">{step.title}</p>
                    <p className="text-xs text-slate-500">{step.years} years</p>
                  </div>
                  <p className="text-sm text-slate-700 tabular-nums">{step.salary_range}</p>
                </div>
              ))}
              {progression.length === 0 && (
                <p className="text-sm text-slate-500">No ladder for this role yet — update your title on profile.</p>
              )}
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white border border-slate-200 rounded-xl p-6">
              <h3 className="text-sm font-semibold text-slate-900 mb-4">Skill gaps</h3>
              <div className="space-y-3">
                {gaps.length === 0 && (
                  <p className="text-sm text-slate-500">No gaps detected for your current level.</p>
                )}
                {gaps.map((g: any) => (
                  <div key={g.skill} className="border border-slate-100 rounded-lg p-3">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium text-slate-900">{g.skill}</span>
                      <span className="text-xs uppercase text-slate-500">{g.importance}</span>
                    </div>
                    {(g.resources || []).slice(0, 2).map((r: any) => (
                      <p key={r.title} className="text-xs text-slate-500 mt-1">
                        {r.type}: {r.title}
                        {r.author ? ` — ${r.author}` : ""}
                      </p>
                    ))}
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-6">
              <h3 className="text-sm font-semibold text-slate-900 mb-4">Recommendations</h3>
              <div className="space-y-3">
                {recs.map((r: any, i: number) => (
                  <div key={i} className="border border-slate-100 rounded-lg p-3">
                    <p className="text-sm font-medium text-slate-900">{r.title}</p>
                    <p className="text-xs text-slate-500 mt-1">{r.description}</p>
                    {r.timeline && <p className="text-xs text-teal-700 mt-1">{r.timeline}</p>}
                  </div>
                ))}
                {recs.length === 0 && <p className="text-sm text-slate-500">No recommendations yet.</p>}
              </div>
            </div>
          </div>

          {trajectory.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-6">
              <h3 className="text-sm font-semibold text-slate-900 mb-3">Salary trajectory</h3>
              <div className="flex flex-wrap gap-3">
                {trajectory.map((t: any, i: number) => (
                  <div key={i} className="text-sm px-3 py-2 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="font-medium text-slate-900">{t.level || t.title || `Y${i}`}</span>
                    <span className="text-slate-500 ml-2">{t.salary || t.salary_range}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "goals" && (
        <div className="max-w-lg bg-white border border-slate-200 rounded-xl p-6">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Your goals</h3>
          {goals && (
            <p className="text-xs text-slate-500 mb-4">
              Current title: {goals.current_title || "—"} · Company: {goals.current_company || "—"}
            </p>
          )}
          <form onSubmit={saveGoals} className="space-y-4">
            <label className="block text-sm">
              <span className="text-slate-600">Target roles (comma-separated)</span>
              <input
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
                value={goalForm.target_roles}
                onChange={(e) => setGoalForm((f) => ({ ...f, target_roles: e.target.value }))}
              />
            </label>
            <label className="block text-sm">
              <span className="text-slate-600">Target salary</span>
              <input
                type="number"
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
                value={goalForm.target_salary}
                onChange={(e) => setGoalForm((f) => ({ ...f, target_salary: e.target.value }))}
              />
            </label>
            <button
              type="submit"
              disabled={savingGoal}
              className="px-4 py-2 text-sm font-semibold rounded-lg bg-teal-500 text-white disabled:opacity-50"
            >
              {savingGoal ? "Saving…" : "Save goals"}
            </button>
          </form>
        </div>
      )}

      {activeTab === "recommendations" && (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-200">
            <h3 className="text-sm font-semibold text-slate-900">Matched open roles</h3>
          </div>
          {jobRecs.length === 0 ? (
            <p className="p-6 text-sm text-slate-500">No matched jobs yet — refresh search from the dashboard.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {jobRecs.slice(0, 20).map((item: any, i: number) => {
                const job = item.job || item;
                return (
                  <li key={job.id || i} className="px-5 py-4 flex justify-between gap-4">
                    <div>
                      <p className="text-sm font-medium text-slate-900">{job.title}</p>
                      <p className="text-xs text-slate-500">
                        {job.company}
                        {job.location ? ` · ${job.location}` : ""}
                      </p>
                      {item.career_fit && (
                        <p className="text-xs text-teal-700 mt-1">{item.career_fit}</p>
                      )}
                    </div>
                    <div className="text-right">
                      {item.match_score != null && (
                        <p className="text-sm font-semibold tabular-nums text-slate-900">
                          {Math.round(Number(item.match_score))}%
                        </p>
                      )}
                      {job.external_url && (
                        <a
                          href={job.external_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-teal-600 hover:underline"
                        >
                          View
                        </a>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </AppShell>
  );
}
