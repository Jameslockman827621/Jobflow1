"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import AppShell from "@/components/AppShell";

function DocumentIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  );
}

function PhoneIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z" />
    </svg>
  );
}

function CodeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
    </svg>
  );
}

function TrophyIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M18.75 4.236c.982.143 1.954.317 2.916.52A6.003 6.003 0 0116.27 9.728M18.75 4.236V4.5c0 2.108-.966 3.99-2.48 5.228M15.003 11.078a7.454 7.454 0 00.981-3.172M9.497 14.25c.157-1.14.458-2.206.881-3.172M15.003 11.078c-.423.966-.724 2.032-.881 3.172" />
    </svg>
  );
}

const FUNNEL_ICONS: Record<string, React.FC<{ className?: string }>> = {
  "Applied": DocumentIcon,
  "Phone Screen": PhoneIcon,
  "Technical Interview": CodeIcon,
  "Offer": TrophyIcon,
};

const FUNNEL_COLORS: Record<string, string> = {
  "Applied": "bg-[#0c1a3b]",
  "Phone Screen": "bg-teal-500",
  "Technical Interview": "bg-orange-500",
  "Offer": "bg-emerald-600",
};

export default function AnalyticsPage() {
  const router = useRouter();
  const { user, loading: authLoading, authFetch } = useAuth();
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<any>(null);
  const [marketInsights, setMarketInsights] = useState<any>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
      return;
    }
    if (user) fetchData();
  }, [user, authLoading, router]);

  const fetchData = async () => {
    try {
      const [overviewRes, marketRes] = await Promise.all([
        authFetch("/api/v1/analytics/overview"),
        authFetch("/api/v1/analytics/market-insights"),
      ]);

      if (overviewRes.ok) setOverview(await overviewRes.json());
      if (marketRes.ok) setMarketInsights(await marketRes.json());
    } catch (error) {
      console.error("Error fetching analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  if (authLoading || loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center py-32">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-slate-200 border-t-teal-500 mx-auto mb-3"></div>
            <p className="text-slate-500 text-sm">Loading analytics...</p>
          </div>
        </div>
      </AppShell>
    );
  }

  const stats = {
    totalApplications: overview?.total_applications ?? 15,
    interviewRate: overview?.interview_rate ?? 20,
    offerRate: overview?.offer_rate ?? 6.7,
    responseRate: overview?.response_rate ?? 73,
    profileCompleteness: overview?.profile_completeness ?? 80,
  };

  const funnel = [
    { stage: "Applied", count: 15, percentage: 100 },
    { stage: "Phone Screen", count: 8, percentage: 53 },
    { stage: "Technical Interview", count: 5, percentage: 33 },
    { stage: "Offer", count: 1, percentage: 7 },
  ];

  const companies = [
    { name: "Stripe", jobs: 566, location: "Fintech -- San Francisco" },
    { name: "Airbnb", jobs: 234, location: "Travel -- San Francisco" },
    { name: "GitLab", jobs: 161, location: "DevTools -- Remote" },
    { name: "Figma", jobs: 171, location: "Design -- San Francisco" },
    { name: "Monzo", jobs: 60, location: "Fintech -- London" },
  ];

  const skills = ["Python", "React", "AWS", "Kubernetes", "TypeScript", "Node.js", "PostgreSQL", "Docker"];

  return (
    <AppShell>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-1.5 text-xs font-medium text-slate-500 mb-3">
          <a href="/dashboard" className="hover:text-slate-700 transition-colors">Dashboard</a>
          <span>/</span>
          <span className="text-slate-900">Analytics</span>
        </div>
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 mb-1">Analytics</h1>
            <p className="text-sm text-slate-500">Track your job search performance</p>
          </div>
          <div className="flex items-center gap-3">
            <select className="px-3 py-2 text-sm rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500/40">
              <option>Last 30 days</option>
              <option>Last 90 days</option>
              <option>All time</option>
            </select>
            <button className="px-4 py-2 text-sm font-medium rounded-lg bg-teal-500 text-white hover:bg-teal-600 transition-colors">
              Export Report
            </button>
          </div>
        </div>
      </div>

      {/* Profile Completeness */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Profile Completeness</h2>
            <p className="text-sm text-slate-500">Add skills to reach 100%</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-slate-900">{stats.profileCompleteness}%</div>
          </div>
        </div>
        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div className="h-full bg-teal-500 rounded-full transition-all" style={{ width: `${stats.profileCompleteness}%` }}></div>
        </div>
        <div className="flex justify-between mt-2 text-xs text-slate-500">
          <span>Profile info, resume, preferences</span>
          <span className="text-amber-600">Add 3 more skills</span>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          }
          value={stats.totalApplications}
          label="Total Applications"
          trend="+12%"
        />
        <MetricCard
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
          }
          value={`${stats.interviewRate}%`}
          label="Interview Rate"
          trend="+5%"
        />
        <MetricCard
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
            </svg>
          }
          value={`${stats.offerRate}%`}
          label="Offer Rate"
          trend="+2%"
        />
        <MetricCard
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-4.894-1.29L3 20.25l1.58-4.22A8.162 8.162 0 013 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
            </svg>
          }
          value={`${stats.responseRate}%`}
          label="Response Rate"
          trend="Stable"
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Application Funnel */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-6">
          <h2 className="text-base font-semibold text-slate-900 mb-6">Application Funnel</h2>
          <div className="space-y-5">
            {funnel.map((item) => {
              const FunnelIcon = FUNNEL_ICONS[item.stage] || DocumentIcon;
              const bgColor = FUNNEL_COLORS[item.stage] || "bg-slate-500";
              return (
                <div key={item.stage}>
                  <div className="flex justify-between items-center mb-2">
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-lg ${bgColor} flex items-center justify-center`}>
                        <FunnelIcon className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-slate-900">{item.stage}</div>
                        <div className="text-xs text-slate-500">
                          {item.stage === "Applied" && `${item.count} jobs total`}
                          {item.stage === "Phone Screen" && "Initial interviews"}
                          {item.stage === "Technical Interview" && "Coding & system design"}
                          {item.stage === "Offer" && "Successful outcomes"}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-semibold text-slate-900">{item.percentage}%</div>
                      <div className="text-xs text-slate-500">{item.count}/{funnel[0].count}</div>
                    </div>
                  </div>
                  <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${bgColor}`} style={{ width: `${item.percentage}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Companies */}
        <div className="bg-white border border-slate-200 rounded-xl p-6">
          <h2 className="text-base font-semibold text-slate-900 mb-4">Top Hiring Companies</h2>
          <div className="space-y-3">
            {companies.map((company, i) => (
              <div
                key={company.name}
                className={`flex items-center justify-between p-3 rounded-lg ${i === 0 ? "bg-teal-50" : "bg-white border border-slate-100"}`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center text-white font-semibold text-xs">
                    {company.name[0]}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-slate-900">{company.name}</div>
                    <div className="text-xs text-slate-500">{company.location}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-slate-900">{company.jobs}</div>
                  <div className="text-xs text-slate-500">open</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Market Insights */}
      <div className="mt-6 bg-white border border-slate-200 rounded-xl p-6">
        <h2 className="text-base font-semibold text-slate-900 mb-6">Market Insights</h2>
        <div className="grid md:grid-cols-2 gap-8">
          {/* Trending Skills */}
          <div>
            <h3 className="text-sm font-medium text-slate-900 mb-3 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-teal-500"></span>
              Trending Skills
            </h3>
            <div className="flex flex-wrap gap-2">
              {skills.map((skill) => (
                <span
                  key={skill}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 text-slate-700"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>

          {/* Remote Jobs */}
          <div>
            <h3 className="text-sm font-medium text-slate-900 mb-3 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-orange-500"></span>
              Remote Opportunities
            </h3>
            <div className="flex items-center gap-6">
              <div className="relative w-28 h-28 flex-shrink-0">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="40" stroke="#f1f5f9" strokeWidth="10" fill="none" />
                  <circle cx="50" cy="50" r="40" stroke="#14b8a6" strokeWidth="10" fill="none" strokeDasharray="251.2" strokeDashoffset="163.28" strokeLinecap="round" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-slate-900">35%</div>
                    <div className="text-xs text-slate-500">Remote</div>
                  </div>
                </div>
              </div>
              <div className="flex-1">
                <p className="text-sm text-slate-500 mb-2">Over 1 in 3 jobs now offer remote or hybrid options.</p>
                <span className="inline-block px-2.5 py-1 rounded-full text-xs font-medium text-emerald-700 bg-emerald-50">+8% vs last quarter</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function MetricCard({ icon, value, label, trend }: {
  icon: React.ReactNode;
  value: string | number;
  label: string;
  trend: string;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-sm transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center text-slate-600">
          {icon}
        </div>
        {trend !== "Stable" ? (
          <span className="text-xs font-medium text-emerald-600 flex items-center gap-0.5">
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" />
            </svg>
            {trend}
          </span>
        ) : (
          <span className="text-xs font-medium text-slate-400">{trend}</span>
        )}
      </div>
      <div className="text-2xl font-bold text-slate-900 mb-0.5">{value}</div>
      <div className="text-sm text-slate-500">{label}</div>
    </div>
  );
}
