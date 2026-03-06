"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

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
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-lg text-slate-600">Analyzing your career path...</div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="min-h-screen bg-slate-50" style={{
        backgroundImage: 'linear-gradient(to right, rgba(148, 163, 184, 0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(148, 163, 184, 0.08) 1px, transparent 1px)',
        backgroundSize: '32px 32px'
      }}>
        <Navbar token={token} onLogout={handleLogout} />
        <div className="max-w-4xl mx-auto py-16 px-6 text-center">
          <h1 className="text-4xl font-bold text-navy-900 mb-4">Complete Your Profile First</h1>
          <p className="text-lg text-slate-600 mb-8">
            We need more information to provide personalized career guidance.
          </p>
          <button
            onClick={() => router.push("/profile")}
            className="px-6 py-3 bg-teal-500 text-white rounded-lg font-semibold hover:bg-teal-600 transition-colors"
          >
            Complete Profile
          </button>
        </div>
      </div>
    );
  }

  const careerLevels = [
    { level: 1, title: "Junior Engineer", years: "0-2 years", min: 60, max: 90 },
    { level: 2, title: "Mid-Level Engineer", years: "2-5 years", min: 90, max: 140, active: true },
    { level: 3, title: "Senior Engineer", years: "5-8 years", min: 140, max: 200 },
    { level: 4, title: "Staff Engineer", years: "8-12 years", min: 200, max: 300 },
    { level: 5, title: "Principal Engineer", years: "12+ years", min: 300, max: 500 },
  ];

  const skillGaps = [
    { name: "Leadership", priority: "High Priority", priorityColor: "text-red-600", bg: "bg-red-50", progress: 40, gradient: "from-red-500 to-orange-500" },
    { name: "System Design", priority: "Medium Priority", priorityColor: "text-amber-600", bg: "bg-amber-50", progress: 60, gradient: "from-amber-500 to-orange-500" },
    { name: "Mentoring", priority: "On Track", priorityColor: "text-teal-600", bg: "bg-teal-50", progress: 80, gradient: "from-teal-500 to-emerald-500" },
  ];

  return (
    <div className="min-h-screen bg-slate-50" style={{
      backgroundImage: 'linear-gradient(to right, rgba(148, 163, 184, 0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(148, 163, 184, 0.08) 1px, transparent 1px)',
      backgroundSize: '32px 32px'
    }}>
      <Navbar token={token} onLogout={handleLogout} />

      <main className="pt-28 pb-16">
        <div className="max-w-7xl mx-auto px-6">
          {/* Header */}
          <div className="mb-12">
            <div className="flex items-center space-x-2 text-xs font-medium tracking-wide text-slate-600 mb-4">
              <a href="/dashboard" className="text-slate-600 hover:text-navy-900">Dashboard</a>
              <span>/</span>
              <span className="text-navy-900">Career Pathing</span>
            </div>
            <div className="flex justify-between items-end">
              <div>
                <h1 className="text-4xl font-bold text-navy-900 mb-2">Career Pathing</h1>
                <p className="text-lg text-slate-600">Your personalized roadmap to career growth</p>
              </div>
              <div className="flex space-x-3">
                <button className="px-5 py-2.5 text-sm font-semibold rounded-lg border border-slate-200 text-navy-900 hover:bg-slate-50 transition-colors">Export Plan</button>
                <button className="px-5 py-2.5 text-sm font-semibold rounded-lg bg-teal-500 text-white hover:bg-teal-600 transition-colors">Set New Goal</button>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex space-x-1 p-1.5 rounded-xl mb-10 w-fit bg-white border border-slate-200 shadow-md">
            <button 
              onClick={() => setActiveTab("analysis")}
              className={`px-6 py-2.5 text-sm font-semibold rounded-lg transition-colors ${activeTab === "analysis" ? "bg-white text-navy-900 shadow-sm" : "text-slate-600 hover:text-navy-900"}`}
            >
              Analysis
            </button>
            <button 
              onClick={() => setActiveTab("goals")}
              className={`px-6 py-2.5 text-sm font-semibold rounded-lg transition-colors ${activeTab === "goals" ? "bg-white text-navy-900 shadow-sm" : "text-slate-600 hover:text-navy-900"}`}
            >
              Goals
            </button>
            <button 
              onClick={() => setActiveTab("recommendations")}
              className={`px-6 py-2.5 text-sm font-semibold rounded-lg transition-colors ${activeTab === "recommendations" ? "bg-white text-navy-900 shadow-sm" : "text-slate-600 hover:text-navy-900"}`}
            >
              Recommendations
            </button>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-8">
              {/* Current Level */}
              <div className="bg-white border border-slate-200 rounded-2xl shadow-xl p-8">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-2xl font-semibold text-navy-900 mb-2">Current Level: Mid-Level Engineer</h2>
                    <p className="text-base text-slate-600">2-5 years experience • $90k-$140k range</p>
                  </div>
                  <div className="px-4 py-2 rounded-full text-xs font-medium tracking-wide bg-teal-50 text-teal-600">Level 2 of 5</div>
                </div>
                
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-slate-600 font-medium">Progress to Senior</span>
                    <span className="font-semibold text-navy-900">50%</span>
                  </div>
                  <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div className="h-full bg-teal-500 rounded-full" style={{ width: '50%' }}></div>
                  </div>
                </div>
                
                <p className="text-sm text-slate-600">You're halfway to Senior level. Focus on leadership and system design skills.</p>
              </div>

              {/* Career Ladder */}
              <div className="bg-white border border-slate-200 rounded-2xl shadow-xl p-8">
                <h2 className="text-2xl font-semibold text-navy-900 mb-6">Career Ladder</h2>
                <div className="space-y-3">
                  {careerLevels.map((level) => (
                    <div 
                      key={level.level}
                      className={`bg-white border border-slate-200 rounded-xl p-5 transition-all hover:translate-x-1 ${level.active ? 'border-teal-500 bg-teal-50' : ''}`}
                    >
                      <div className="flex justify-between items-center">
                        <div className="flex items-center space-x-4">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${level.active ? 'bg-teal-500 text-white' : 'bg-slate-100 text-slate-600'}`}>
                            {level.level}
                          </div>
                          <div>
                            <h3 className="font-semibold text-navy-900">{level.title}</h3>
                            <p className="text-sm text-slate-600">{level.years}</p>
                            {level.active && <p className="text-xs text-teal-600 font-medium mt-0.5">You are here</p>}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className={`text-lg font-semibold ${level.active ? 'text-teal-600' : 'text-navy-900'}`}>${level.min}k-${level.max}k</div>
                          <div className="text-xs text-slate-600">{level.active ? 'Current range' : level.level < 2 ? 'Base range' : 'Target range'}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Skill Gaps */}
              <div className="bg-white border border-slate-200 rounded-2xl shadow-xl p-8">
                <h2 className="text-2xl font-semibold text-navy-900 mb-6">Skill Gaps to Reach Senior</h2>
                <div className="space-y-6">
                  {skillGaps.map((skill) => (
                    <div key={skill.name}>
                      <div className="flex justify-between items-center mb-3">
                        <div className="flex items-center space-x-3">
                          <div className={`w-2 h-2 rounded-full ${skill.progress >= 80 ? 'bg-teal-500' : skill.progress >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}></div>
                          <span className="font-semibold text-navy-900">{skill.name}</span>
                        </div>
                        <div className="flex items-center space-x-3">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium tracking-wide ${skill.bg} ${skill.priorityColor}`}>{skill.priority}</span>
                          <span className="text-sm font-medium text-navy-900 w-10 text-right">{skill.progress}%</span>
                        </div>
                      </div>
                      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full bg-gradient-to-r ${skill.gradient}`} style={{ width: `${skill.progress}%` }}></div>
                      </div>
                      <p className="text-sm text-slate-600 mt-2 ml-5">
                        {skill.name === "Leadership" && "Lead technical discussions and mentor junior engineers"}
                        {skill.name === "System Design" && "Design scalable, distributed systems"}
                        {skill.name === "Mentoring" && "Guide and support junior team members"}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <div className="space-y-8">
              {/* Next Milestone */}
              <div className="bg-navy-900 rounded-2xl shadow-xl p-8 text-white">
                <h2 className="text-2xl font-semibold mb-4">Next Milestone</h2>
                <h3 className="text-3xl font-bold mb-2">Reach Senior Engineer</h3>
                <p className="text-lg text-slate-300 mb-6">Timeline: 18-36 months</p>
                
                <div className="space-y-3 mb-6">
                  {[
                    "Design complex, cross-team systems",
                    "Become domain go-to person",
                    "Mentor junior engineers regularly",
                    "Lead architecture decisions"
                  ].map((item, i) => (
                    <div key={i} className="flex items-start space-x-3">
                      <div className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center mt-0.5 flex-shrink-0">
                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/>
                        </svg>
                      </div>
                      <span className="text-sm text-slate-300">{item}</span>
                    </div>
                  ))}
                </div>
                
                <button className="w-full py-3 rounded-lg text-sm font-semibold text-white bg-teal-500 hover:bg-teal-600 transition-colors">
                  Create Action Plan
                </button>
              </div>

              {/* Recommended Learning */}
              <div className="bg-white border border-slate-200 rounded-2xl shadow-xl p-8">
                <h2 className="text-2xl font-semibold text-navy-900 mb-6">Recommended Learning</h2>
                <div className="space-y-4">
                  {[
                    { name: "Leadership Fundamentals", hours: "6 hours", level: "Intermediate", color: "bg-navy-900" },
                    { name: "System Design Masterclass", hours: "12 hours", level: "Advanced", color: "bg-teal-500" },
                    { name: "Mentorship Best Practices", hours: "4 hours", level: "Beginner", color: "bg-coral-500" },
                  ].map((course, i) => (
                    <div key={i} className="flex items-start space-x-4 p-4 rounded-xl bg-slate-50">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0 ${course.color}`}>
                        {course.name.split(' ').map(w => w[0]).join('').slice(0, 2)}
                      </div>
                      <div>
                        <h3 className="font-semibold text-sm text-navy-900">{course.name}</h3>
                        <p className="text-sm text-slate-600">{course.hours} • {course.level}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

// Simple Navbar component for this page
function Navbar({ token, onLogout }: { token: string | null; onLogout: () => void }) {
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
          <a href="/analytics" className="text-sm text-slate-600 hover:text-navy-900 transition-colors">Analytics</a>
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
