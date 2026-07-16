"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import AppShell from "@/components/AppShell";
import { toast } from "sonner";

export default function ReviewsPage() {
  const router = useRouter();
  const { authFetch, user, loading: authLoading } = useAuth();
  const [loading, setLoading] = useState(true);
  const [companies, setCompanies] = useState<any[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState("");
  const [formData, setFormData] = useState({
    company_name: "",
    overall_rating: 5,
    work_life_balance: 5,
    culture: 5,
    compensation: 5,
    career_opportunities: 5,
    title: "",
    pros: "",
    cons: "",
  });

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push("/login");
      return;
    }
    fetchCompanies();
  }, [authLoading, user, router]);

  const fetchCompanies = async () => {
    try {
      const res = await authFetch("/api/v1/reviews/companies");
      if (res.ok) {
        const data = await res.json();
        const list = data.companies || [];
        setCompanies(list);
        if (list.length && !selectedCompany) {
          selectCompany(list[0].name);
        }
      }
    } catch {
      toast.error("Failed to load companies");
    } finally {
      setLoading(false);
    }
  };

  const selectCompany = async (companyName: string) => {
    setSelectedCompany(companyName);
    setDetailLoading(true);
    try {
      const res = await authFetch(`/api/v1/reviews/company/${encodeURIComponent(companyName)}`);
      if (res.ok) setDetail(await res.json());
      else {
        setDetail(null);
        toast.error("Could not load reviews");
      }
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await authFetch("/api/v1/reviews/company", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(typeof err.detail === "string" ? err.detail : "Submit failed");
      }
      toast.success("Review submitted");
      setShowForm(false);
      await fetchCompanies();
      if (formData.company_name) await selectCompany(formData.company_name);
    } catch (err: any) {
      toast.error(err.message || "Failed to submit review");
    }
  };

  if (authLoading || loading) {
    return (
      <AppShell>
        <div className="flex justify-center py-24 text-slate-500 text-sm">Loading reviews…</div>
      </AppShell>
    );
  }

  const filtered = companies.filter((c) =>
    String(c.name || "").toLowerCase().includes(search.toLowerCase())
  );
  const avg = detail?.average_ratings || {};

  return (
    <AppShell>
      <div className="mb-8 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Company reviews</h1>
          <p className="text-sm text-slate-500 mt-1">Employee-submitted reviews only — no fabricated listings</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setFormData((f) => ({ ...f, company_name: selectedCompany || "" }));
            setShowForm(true);
          }}
          className="px-4 py-2 text-sm font-semibold rounded-lg bg-teal-500 text-white hover:bg-teal-600"
        >
          Write a review
        </button>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search companies"
            className="w-full mb-3 rounded-lg border border-slate-200 px-3 py-2 text-sm"
          />
          {filtered.length === 0 ? (
            <p className="text-sm text-slate-500 p-3">
              No reviews yet. Be the first — write a review for a company you know.
            </p>
          ) : (
            <ul className="space-y-1 max-h-[70vh] overflow-y-auto">
              {filtered.map((c) => (
                <li key={c.name}>
                  <button
                    type="button"
                    onClick={() => selectCompany(c.name)}
                    className={`w-full text-left rounded-lg px-3 py-2.5 ${
                      selectedCompany === c.name ? "bg-teal-50 border border-teal-200" : "hover:bg-slate-50"
                    }`}
                  >
                    <p className="text-sm font-medium text-slate-900">{c.name}</p>
                    <p className="text-xs text-slate-500">
                      {(c.avg_rating ?? 0).toFixed?.(1) ?? c.avg_rating} · {c.review_count || 0} reviews
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="lg:col-span-2 space-y-4">
          {!selectedCompany && (
            <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-sm text-slate-500">
              Select a company to see real reviews.
            </div>
          )}
          {detailLoading && (
            <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-sm text-slate-500">
              Loading…
            </div>
          )}
          {!detailLoading && detail && (
            <>
              <div className="bg-white border border-slate-200 rounded-xl p-6">
                <h2 className="text-xl font-semibold text-slate-900">{detail.company_name}</h2>
                <p className="text-sm text-slate-500 mt-1">
                  {detail.total_reviews || 0} reviews · overall{" "}
                  <span className="font-semibold text-slate-800">
                    {(avg.overall ?? 0).toFixed?.(1) ?? avg.overall ?? "—"}
                  </span>
                </p>
                <div className="grid sm:grid-cols-2 gap-3 mt-5">
                  {[
                    ["Work-life balance", avg.work_life_balance],
                    ["Culture", avg.culture],
                    ["Compensation", avg.compensation],
                    ["Career opportunities", avg.career_opportunities],
                    ["Management", avg.management],
                  ].map(([label, value]) => (
                    <div key={String(label)}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-600">{label}</span>
                        <span className="font-medium">{value != null ? Number(value).toFixed(1) : "—"}</span>
                      </div>
                      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-teal-500 rounded-full"
                          style={{ width: `${Math.min(100, ((Number(value) || 0) / 5) * 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white border border-slate-200 rounded-xl p-6">
                <h3 className="text-sm font-semibold text-slate-900 mb-4">Reviews</h3>
                {(detail.reviews || []).length === 0 ? (
                  <p className="text-sm text-slate-500">No reviews for this company yet.</p>
                ) : (
                  <div className="space-y-4">
                    {(detail.reviews || []).map((r: any) => (
                      <div key={r.id} className="border border-slate-100 rounded-lg p-4">
                        <div className="flex justify-between gap-3">
                          <h4 className="text-sm font-semibold text-slate-900">{r.title || "Review"}</h4>
                          <span className="text-xs text-amber-600">{r.overall_rating}★</span>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">
                          {r.job_title || "Employee"}
                          {r.created_at ? ` · ${new Date(r.created_at).toLocaleDateString()}` : ""}
                        </p>
                        {r.pros && (
                          <p className="text-sm text-slate-700 mt-2">
                            <span className="text-emerald-600 font-medium">Pros:</span> {r.pros}
                          </p>
                        )}
                        {r.cons && (
                          <p className="text-sm text-slate-700 mt-1">
                            <span className="text-red-600 font-medium">Cons:</span> {r.cons}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <form
            onSubmit={handleSubmitReview}
            className="bg-white rounded-xl border border-slate-200 p-6 w-full max-w-md space-y-3 max-h-[90vh] overflow-y-auto"
          >
            <h3 className="text-lg font-semibold text-slate-900">Write a review</h3>
            <input
              required
              placeholder="Company name"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              value={formData.company_name}
              onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
            />
            <input
              required
              placeholder="Title"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            />
            <label className="block text-xs text-slate-600">
              Overall (1–5)
              <input
                type="number"
                min={1}
                max={5}
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                value={formData.overall_rating}
                onChange={(e) => setFormData({ ...formData, overall_rating: Number(e.target.value) })}
              />
            </label>
            <textarea
              required
              placeholder="Pros"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm min-h-[72px]"
              value={formData.pros}
              onChange={(e) => setFormData({ ...formData, pros: e.target.value })}
            />
            <textarea
              required
              placeholder="Cons"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm min-h-[72px]"
              value={formData.cons}
              onChange={(e) => setFormData({ ...formData, cons: e.target.value })}
            />
            <div className="flex gap-2 justify-end pt-2">
              <button type="button" onClick={() => setShowForm(false)} className="px-3 py-2 text-sm text-slate-600">
                Cancel
              </button>
              <button type="submit" className="px-4 py-2 text-sm font-semibold rounded-lg bg-teal-500 text-white">
                Submit
              </button>
            </div>
          </form>
        </div>
      )}
    </AppShell>
  );
}
