"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Navbar from "../../components/Navbar";

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
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-xl text-gray-600">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar isLoggedIn={true} onLogout={handleLogout} />

      <main className="max-w-7xl mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Analytics Dashboard</h1>

        {/* Profile Completeness */}
        {overview?.profile_completeness !== undefined && (
          <div className="bg-white p-6 rounded-lg shadow mb-8">
            <h2 className="text-lg font-semibold mb-4">Profile Completeness</h2>
            <div className="flex items-center gap-4">
              <div className="flex-1 bg-gray-200 rounded-full h-4">
                <div
                  className={`h-4 rounded-full ${
                    overview.profile_completeness >= 80 ? "bg-green-500" :
                    overview.profile_completeness >= 50 ? "bg-yellow-500" :
                    "bg-red-500"
                  }`}
                  style={{ width: `${overview.profile_completeness}%` }}
                />
              </div>
              <span className="text-lg font-semibold">{overview.profile_completeness}%</span>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Applications */}
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-sm text-gray-500 mb-2">Total Applications</div>
            <div className="text-3xl font-bold text-blue-600">
              {overview?.applications?.total_applications || 0}
            </div>
            <div className="text-sm text-gray-500 mt-2">
              This month: {overview?.applications?.this_month || 0}
            </div>
          </div>

          {/* Interview Rate */}
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-sm text-gray-500 mb-2">Interview Rate</div>
            <div className={`text-3xl font-bold ${
              (overview?.interviews?.interview_rate || 0) >= 20 ? "text-green-600" :
              (overview?.interviews?.interview_rate || 0) >= 10 ? "text-yellow-600" :
              "text-red-600"
            }`}>
              {overview?.interviews?.interview_rate || 0}%
            </div>
            <div className="text-sm text-gray-500 mt-2">
              {overview?.interviews?.total_interviews || 0} interviews total
            </div>
          </div>

          {/* Offer Rate */}
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-sm text-gray-500 mb-2">Offer Rate</div>
            <div className="text-3xl font-bold text-purple-600">
              {overview?.success?.offer_rate || 0}%
            </div>
            <div className="text-sm text-gray-500 mt-2">
              {overview?.success?.offers_received || 0} offers received
            </div>
          </div>

          {/* Response Rate */}
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-sm text-gray-500 mb-2">Response Rate</div>
            <div className="text-3xl font-bold text-orange-600">
              {overview?.applications?.by_status?.viewed ? 
                Math.round((overview.applications.by_status.viewed / overview.applications.total_applications) * 100) : 0}%
            </div>
            <div className="text-sm text-gray-500 mt-2">
              Avg response: {overview?.response_times?.avg_response_days || 5} days
            </div>
          </div>
        </div>

        {/* Application Funnel */}
        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <h2 className="text-xl font-semibold mb-6">Application Funnel</h2>
          <div className="space-y-4">
            {overview?.applications?.by_stage && Object.entries(overview.applications.by_stage).map(([stage, count]: [string, any], i: number) => {
              const total = overview.applications.total_applications;
              const percentage = Math.round((count / total) * 100);
              return (
                <div key={stage} className="flex items-center gap-4">
                  <div className="w-32 text-sm font-medium capitalize">{stage.replace("_", " ")}</div>
                  <div className="flex-1 bg-gray-200 rounded-full h-8">
                    <div
                      className="h-8 rounded-full bg-blue-500 flex items-center justify-end px-3 text-white text-sm font-medium"
                      style={{ width: `${percentage}%` }}
                    >
                      {count}
                    </div>
                  </div>
                  <div className="w-16 text-right text-sm text-gray-500">{percentage}%</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Market Insights */}
        {marketInsights && (
          <div className="grid md:grid-cols-2 gap-8">
            {/* Top Hiring Companies */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Top Hiring Companies</h2>
              <div className="space-y-3">
                {marketInsights.top_hiring_companies?.slice(0, 10).map((company: string, i: number) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
                    <div className="flex items-center gap-3">
                      <span className="text-gray-400 font-medium">{i + 1}</span>
                      <span className="font-medium">{company}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Trending Skills */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Trending Skills</h2>
              <div className="flex flex-wrap gap-2">
                {marketInsights.trending_skills?.slice(0, 15).map((skill: string, i: number) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* Salary by Level */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Avg Salary by Level</h2>
              <div className="space-y-3">
                {marketInsights.avg_salary_by_role && Object.entries(marketInsights.avg_salary_by_role).map(([level, salary]: [string, any], i: number) => (
                  <div key={i} className="flex justify-between items-center py-2 border-b last:border-0">
                    <span className="capitalize font-medium">{level}</span>
                    <span className="text-green-600 font-semibold">
                      ${(salary / 1000).toFixed(0)}k
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Remote Stats */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Remote Work Trends</h2>
              <div className="flex items-center gap-4">
                <div className="text-5xl font-bold text-blue-600">
                  {marketInsights.remote_percentage || 0}%
                </div>
                <div className="text-gray-600">
                  of jobs are fully remote
                </div>
              </div>
              <div className="mt-4">
                <div className="flex-1 bg-gray-200 rounded-full h-4">
                  <div
                    className="h-4 rounded-full bg-blue-500"
                    style={{ width: `${marketInsights.remote_percentage || 0}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Growth Trend */}
        <div className="bg-white p-6 rounded-lg shadow mt-8">
          <h2 className="text-xl font-semibold mb-4">Monthly Activity</h2>
          <div className="flex items-end gap-2 h-48">
            {overview?.applications?.this_month && (
              <>
                <div className="flex-1 flex flex-col items-center">
                  <div
                    className="w-full bg-gray-300 rounded-t"
                    style={{ height: '60%' }}
                  />
                  <div className="text-xs text-gray-600 mt-2">Last Month</div>
                  <div className="text-sm font-semibold">{overview.applications.last_month}</div>
                </div>
                <div className="flex-1 flex flex-col items-center">
                  <div
                    className="w-full bg-blue-500 rounded-t"
                    style={{ height: '100%' }}
                  />
                  <div className="text-xs text-gray-600 mt-2">This Month</div>
                  <div className="text-sm font-semibold">{overview.applications.this_month}</div>
                </div>
              </>
            )}
          </div>
          {overview?.applications?.growth_rate !== undefined && (
            <div className={`mt-4 text-center font-semibold ${
              overview.applications.growth_rate >= 0 ? "text-green-600" : "text-red-600"
            }`}>
              {overview.applications.growth_rate >= 0 ? "↑" : "↓"} {Math.abs(overview.applications.growth_rate)}% vs last month
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
