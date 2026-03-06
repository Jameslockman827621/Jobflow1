"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Navbar from "../../components/Navbar";

export default function CareerPathingPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"analysis" | "goals" | "recommendations">("analysis");

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      router.push("/login");
      return;
    }
    setToken(storedToken);
    fetchAnalysis(storedToken);
  }, [router]);

  const fetchAnalysis = async (authToken: string) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/career/analysis`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setAnalysis(data);
      }
    } catch (error) {
      console.error("Error fetching career analysis:", error);
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
        <div className="text-xl text-gray-600">Analyzing your career path...</div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar isLoggedIn={true} onLogout={handleLogout} />
        <div className="max-w-4xl mx-auto py-16 px-4 text-center">
          <h1 className="text-3xl font-bold mb-4">Complete Your Profile First</h1>
          <p className="text-gray-600 mb-8">
            We need more information to provide personalized career guidance.
          </p>
          <button
            onClick={() => router.push("/profile")}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Complete Profile
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar isLoggedIn={true} onLogout={handleLogout} />

      <main className="max-w-6xl mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Career Pathing</h1>

        {/* Tabs */}
        <div className="flex gap-4 mb-8 border-b">
          {["analysis", "goals", "recommendations"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`pb-4 px-4 font-medium capitalize ${
                activeTab === tab
                  ? "border-b-2 border-blue-600 text-blue-600"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {activeTab === "analysis" && (
          <div className="space-y-8">
            {/* Current Level */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Your Current Level</h2>
              <div className="flex items-center gap-4">
                <div className="text-5xl font-bold text-blue-600">{analysis.current_level}</div>
                <div className="text-gray-600">
                  Based on your experience and skills
                </div>
              </div>
            </div>

            {/* Career Progression */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Career Progression</h2>
              <div className="space-y-4">
                {analysis.career_path.progression?.map((stage: any, i: number) => (
                  <div
                    key={i}
                    className={`flex items-center gap-4 p-4 rounded-lg ${
                      stage.title.toLowerCase().includes(analysis.current_level.toLowerCase())
                        ? "bg-blue-50 border-2 border-blue-500"
                        : "bg-gray-50"
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      stage.title.toLowerCase().includes(analysis.current_level.toLowerCase())
                        ? "bg-blue-600 text-white"
                        : "bg-gray-300"
                    }`}>
                      {i + 1}
                    </div>
                    <div className="flex-1">
                      <div className="font-semibold">{stage.title}</div>
                      <div className="text-sm text-gray-500">{stage.years} experience</div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-green-600">{stage.salary_range}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Skill Gaps */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Skill Gaps to Address</h2>
              {analysis.skill_gaps && analysis.skill_gaps.length > 0 ? (
                <div className="space-y-3">
                  {analysis.skill_gaps.map((gap: any, i: number) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg">
                      <span className="text-yellow-600">⚠️</span>
                      <div>
                        <div className="font-medium">{gap.skill}</div>
                        <div className="text-sm text-gray-600">
                          Importance: <span className="capitalize">{gap.importance}</span>
                        </div>
                        {gap.resources && gap.resources.length > 0 && (
                          <div className="mt-2 text-sm text-blue-600">
                            📚 {gap.resources[0]?.title} by {gap.resources[0]?.author}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">No significant skill gaps identified!</p>
              )}
            </div>

            {/* Next Milestone */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Next Milestone</h2>
              <div className="bg-green-50 p-6 rounded-lg">
                <h3 className="text-lg font-semibold text-green-800 mb-3">
                  {analysis.next_milestone.title}
                </h3>
                <ul className="space-y-2 mb-4">
                  {analysis.next_milestone.requirements?.map((req: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-green-600 mt-1">✓</span>
                      <span>{req}</span>
                    </li>
                  ))}
                </ul>
                <div className="text-sm text-green-700">
                  Timeline: {analysis.next_milestone.timeline}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "goals" && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Set Career Goals</h2>
            <p className="text-gray-600 mb-6">
              Define your target role and we'll help you get there.
            </p>
            <form className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Target Role
                </label>
                <input
                  type="text"
                  placeholder="e.g., Senior Software Engineer"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Target Company (optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g., Google, Stripe"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Target Salary
                </label>
                <input
                  type="number"
                  placeholder="e.g., 150000"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Timeline (months)
                </label>
                <input
                  type="number"
                  placeholder="e.g., 12"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <button
                type="submit"
                className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Set Goal
              </button>
            </form>
          </div>
        )}

        {activeTab === "recommendations" && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Personalized Recommendations</h2>
              {analysis.recommendations && analysis.recommendations.map((rec: any, i: number) => (
                <div key={i} className="border-b last:border-0 py-4">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      rec.priority === "high" ? "bg-red-100 text-red-800" :
                      rec.priority === "medium" ? "bg-yellow-100 text-yellow-800" :
                      "bg-blue-100 text-blue-800"
                    }`}>
                      {rec.priority}
                    </span>
                    <span className="font-semibold">{rec.title}</span>
                  </div>
                  <p className="text-gray-600 mb-2">{rec.description}</p>
                  <p className="text-sm text-gray-500">Timeline: {rec.timeline}</p>
                </div>
              ))}
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">Salary Trajectory</h2>
              <div className="h-64 flex items-end gap-4">
                {analysis.salary_trajectory && analysis.salary_trajectory.map((stage: any, i: number) => (
                  <div key={i} className="flex-1 flex flex-col items-center">
                    <div
                      className="w-full bg-blue-500 rounded-t"
                      style={{ height: `${(i + 1) * 20}%` }}
                    />
                    <div className="text-xs text-gray-600 mt-2 text-center">
                      {stage.years}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
