"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AnalyticsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [overview, setOverview] = useState<any>(null);
  const [marketInsights, setMarketInsights] = useState<any>(null);

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      router.push("/login");
      return;
    }
    setToken(storedToken);
    fetchData(storedToken);
  }, [router]);

  const fetchData = async (authToken: string) => {
    try {
      const [overviewRes, marketRes] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/analytics/overview`, {
          headers: { Authorization: `Bearer ${authToken}` },
        }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/analytics/market-insights`, {
          headers: { Authorization: `Bearer ${authToken}` },
        }),
      ]);

      if (overviewRes.ok) setOverview(await overviewRes.json());
      if (marketRes.ok) setMarketInsights(await marketRes.json());
    } catch (error) {
      console.error("Error fetching analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-lg text-slate-600">Loading analytics...</div>
      </div>
    );
  }

  // Mock data for demo
  const stats = {
    totalApplications: 15,
    interviewRate: 20,
    offerRate: 6.7,
    responseRate: 73,
    profileCompleteness: 80,
  };

  const funnel = [
    { stage: "Applied", count: 15, percentage: 100, color: "bg-navy-900", icon: "📝" },
    { stage: "Phone Screen", count: 8, percentage: 53, color: "bg-teal-500", icon: "📞" },
    { stage: "Technical Interview", count: 5, percentage: 33, color: "bg-coral-500", icon: "💻" },
    { stage: "Offer", count: 1, percentage: 7, color: "bg-emerald-600", icon: "🎉" },
  ];

  const companies = [
    { name: "Stripe", jobs: 566, color: "bg-navy-900", location: "Fintech • San Francisco" },
    { name: "Airbnb", jobs: 234, color: "bg-red-500", location: "Travel • San Francisco" },
    { name: "GitLab", jobs: 161, color: "bg-orange-500", location: "DevTools • Remote" },
    { name: "Figma", jobs: 171, color: "bg-blue-500", location: "Design • San Francisco" },
    { name: "Monzo", jobs: 60, color: "bg-slate-800", location: "Fintech • London" },
  ];

  const skills = ["Python", "React", "AWS", "Kubernetes", "TypeScript", "Node.js", "PostgreSQL", "Docker"];

  return (
    <div className="min-h-screen bg-slate-50" style={{
      backgroundImage: 'linear-gradient(to right, rgba(148, 163, 184, 0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(148, 163, 184, 0.08) 1px, transparent 1px)',
      backgroundSize: '32px 32px'
    }}>
      <Navbar onLogout={handleLogout} />

      <main className="pt-28 pb-16">
        <div className="max-w-7xl mx-auto px-6">
          {/* Header */}
          <div className="mb-12">
            <div className="flex items-center space-x-2 text-xs font-medium tracking-wide text-slate-600 mb-4">
              <a href="/dashboard" className="text-slate-600 hover:text-navy-900">Dashboard</a>
              <span>/</span>
              <span className="text-navy-900">Analytics</span>
            </div>
            <div className="flex justify-between items-end">
              <div>
                <h1 className="text-4xl font-bold text-navy-900 mb-2">Analytics Dashboard</h1>
                <p className="text-lg text-slate-600">Track your job search performance</p>
              </div>
              <div className="flex items-center space-x-3">
                <select className="px-4 py-2.5 text-sm font-semibold rounded-lg border border-slate-200 bg-white text-navy-900 focus:outline-none focus:ring-2 focus:ring-teal-500">
                  <option>Last 30 days</option>
                  <option>Last 90 days</option>
                  <option>All time</option>
                </select>
                <button className="px-5 py-2.5 text-sm font-semibold rounded-lg bg-teal-500 text-white hover:bg-teal-600 transition-colors">
                  Export Report
                </button>
              </div>
            </div>
          </div>

          {/* Profile Completeness */}
          <div className="bg-white border border-slate-200 rounded-2xl shadow-xl p-8 mb-8">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-semibold text-navy-900 mb-1">Profile Completeness</h2>
                <p className="text-sm text-slate-600">Add skills to reach 100%</p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-navy-900">{stats.profileCompleteness}%</div>
                <div className="text-xs font-medium tracking-wide text-slate-600">Complete</div>
              </div>
            </div>
            <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
              <div className="h-full bg-teal-500 rounded-full" style={{ width: `${stats.profileCompleteness}%` }}></div>
            </div>
            <div className="flex justify-between mt-3 text-sm">
              <span className="text-emerald-600 font-medium">✓ Profile info, resume, preferences</span>
              <span className="text-coral-500 font-medium">⚠ Add 3 more skills</span>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid md:grid-cols-4 gap-6 mb-8">
            <MetricCard
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              }
              value={stats.totalApplications}
              label="Total Applications"
              trend="+12%"
              color="bg-navy-900"
            />
            <MetricCard
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              }
              value={`${stats.interviewRate}%`}
              label="Interview Rate"
              trend="+5%"
              color="bg-teal-500"
            />
            <MetricCard
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              }
              value={`${stats.offerRate}%`}
              label="Offer Rate"
              trend="+2%"
              color="bg-coral-500"
            />
            <MetricCard
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              }
              value={`${stats.responseRate}%`}
              label="Response Rate"
              trend="Stable"
              color="bg-indigo-500"
            />
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Application Funnel */}
            <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl shadow-xl p-8">
              <h2 className="text-2xl font-semibold text-navy-900 mb-8">Application Funnel</h2>
              <div className="space-y-6">
                {funnel.map((item) => (
                  <div key={item.stage}>
                    <div className="flex justify-between items-center mb-3">
                      <div className="flex items-center space-x-3">
                        <div className={`w-10 h-10 rounded-xl ${item.color} flex items-center justify-center`}>
                          <span className="text-lg">{item.icon}</span>
                        </div>
                        <div>
                          <div className="font-semibold text-navy-900">{item.stage}</div>
                          <div className="text-sm text-slate-600">
                            {item.stage === "Applied" && "15 jobs total"}
                            {item.stage === "Phone Screen" && "Initial interviews"}
                            {item.stage === "Technical Interview" && "Coding & system design"}
                            {item.stage === "Offer" && "Successful outcomes"}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-semibold text-navy-900">{item.percentage}%</div>
                        <div className="text-sm text-slate-600">{item.count}/15</div>
                      </div>
                    </div>
                    <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${item.color}`} style={{ width: `${item.percentage}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Companies */}
            <div className="bg-white border border-slate-200 rounded-2xl shadow-xl p-8">
              <h2 className="text-2xl font-semibold text-navy-900 mb-6">Top Hiring Companies</h2>
              <div className="space-y-4">
                {companies.map((company, i) => (
                  <div 
                    key={company.name}
                    className={`flex items-center justify-between p-4 rounded-xl ${i === 0 ? 'bg-teal-50' : 'bg-white border border-slate-200'}`}
                  >
                    <div className="flex items-center space-x-4">
                      <div className={`w-10 h-10 rounded-xl ${company.color} flex items-center justify-center text-white font-bold text-sm`}>
                        {company.name[0]}
                      </div>
                      <div>
                        <div className="font-semibold text-sm text-navy-900">{company.name}</div>
                        <div className="text-sm text-slate-600">{company.location}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-semibold text-navy-900">{company.jobs}</div>
                      <div className="text-xs font-medium tracking-wide text-slate-600">open jobs</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Market Insights */}
          <div className="mt-8 bg-white border border-slate-200 rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-semibold text-navy-900 mb-8">Market Insights</h2>
            <div className="grid md:grid-cols-2 gap-8">
              {/* Trending Skills */}
              <div>
                <h3 className="font-semibold text-navy-900 mb-4 flex items-center">
                  <div className="w-2 h-2 rounded-full bg-teal-500 mr-3"></div>
                  Trending Skills
                </h3>
                <div className="flex flex-wrap gap-3">
                  {skills.map((skill, i) => (
                    <span 
                      key={skill}
                      className={`px-4 py-2 rounded-lg text-xs font-medium tracking-wide text-white ${
                        i === 0 ? 'bg-navy-900' : 
                        i === 1 ? 'bg-teal-500' : 
                        i === 2 ? 'bg-coral-500' : 
                        i === 3 ? 'bg-navy-800' :
                        i === 4 ? 'bg-navy-700' :
                        i === 5 ? 'bg-emerald-600' :
                        i === 6 ? 'bg-navy-800' : 'bg-teal-400'
                      }`}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Remote Jobs */}
              <div>
                <h3 className="font-semibold text-navy-900 mb-4 flex items-center">
                  <div className="w-2 h-2 rounded-full bg-coral-500 mr-3"></div>
                  Remote Opportunities
                </h3>
                <div className="flex items-center space-x-6">
                  <div className="relative w-32 h-32">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="40" stroke="#e2e8f0" strokeWidth="12" fill="none"/>
                      <circle cx="50" cy="50" r="40" stroke="#14b8a6" strokeWidth="12" fill="none" strokeDasharray="251.2" strokeDashoffset="163.28" strokeLinecap="round"/>
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <div className="text-3xl font-bold text-navy-900">35%</div>
                        <div className="text-xs font-medium tracking-wide text-slate-600">Remote</div>
                      </div>
                    </div>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-slate-600 mb-3">Over 1 in 3 jobs now offer remote or hybrid options.</p>
                    <span className="px-3 py-1 rounded-full text-xs font-medium tracking-wide text-emerald-600 bg-emerald-50">+8% vs last quarter</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function MetricCard({ icon, value, label, trend, color }: { 
  icon: React.ReactNode; 
  value: string | number; 
  label: string; 
  trend: string;
  color: string;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-md p-6 hover:shadow-lg hover:-translate-y-0.5 transition-all">
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center text-white`}>
          {icon}
        </div>
        {trend !== "Stable" ? (
          <span className="text-xs font-semibold tracking-wide text-emerald-600 flex items-center">
            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"/>
            </svg>
            {trend}
          </span>
        ) : (
          <span className="text-xs font-semibold tracking-wide text-slate-500">{trend}</span>
        )}
      </div>
      <div className="text-3xl font-bold text-navy-900 mb-1">{value}</div>
      <div className="text-sm text-slate-600">{label}</div>
    </div>
  );
}

function Navbar({ onLogout }: { onLogout: () => void }) {
  const router = useRouter();
  
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-navy-900 flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <span className="text-xl font-bold text-navy-900">JobScale</span>
        </div>
        <div className="flex items-center space-x-8">
          <a href="/dashboard" className="text-sm text-slate-600 hover:text-navy-900 transition-colors">Dashboard</a>
          <a href="/career" className="text-sm text-slate-600 hover:text-navy-900 transition-colors">Career</a>
          <a href="/reviews" className="text-sm text-slate-600 hover:text-navy-900 transition-colors">Reviews</a>
          <div className="w-px h-6 bg-slate-200"></div>
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-full bg-teal-500 flex items-center justify-center text-white font-semibold text-sm">JD</div>
            <span className="text-sm font-medium text-navy-900">John Doe</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
