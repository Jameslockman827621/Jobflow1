"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Navbar from "../../components/Navbar";
import JobCard from "../../components/JobCard";

interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  remote: boolean;
  hybrid?: boolean;
  min_salary?: number;
  max_salary?: number;
  seniority?: string;
  match_score?: number;
  external_url: string;
  posted_date?: string;
}

interface Application {
  id: number;
  job_id: number;
  job_title: string;
  company: string;
  status: string;
  stage: string;
  match_score?: number;
  created_at: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"jobs" | "applications" | "profile">("jobs");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);

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
    setLoading(true);
    const headers = { Authorization: `Bearer ${authToken}` };
    
    try {
      const [jobsRes, appsRes] = await Promise.all([
        fetch(`${process.env.API_URL || "http://localhost:8000/api/v1"}/jobs?limit=20`, { headers }),
        fetch(`${process.env.API_URL || "http://localhost:8000/api/v1"}/applications/`, { headers }),
      ]);
      
      if (jobsRes.ok) setJobs(await jobsRes.json());
      if (appsRes.ok) setApplications(await appsRes.json());
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async (jobId: number) => {
    if (!token) return;
    
    try {
      const res = await fetch(`${process.env.API_URL || "http://localhost:8000/api/v1"}/applications/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ job_id: jobId, auto_prepare: true }),
      });
      
      const data = await res.json();
      alert(data.message);
      fetchData(token);
    } catch (error) {
      console.error("Error applying:", error);
      alert("Failed to apply");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-xl text-gray-600">Loading your dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar isLoggedIn={true} onLogout={handleLogout} />

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 mt-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {["jobs", "applications", "profile"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className={`
                  pb-4 px-1 border-b-2 font-medium text-sm capitalize
                  ${activeTab === tab
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }
                `}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === "jobs" && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Recommended Jobs</h2>
              <span className="text-sm text-gray-500">{jobs.length} jobs found</span>
            </div>
            {jobs.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-4xl mb-4">🔍</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs yet</h3>
                <p className="text-gray-500 mb-4">We're still scraping jobs. Check back soon!</p>
                <p className="text-sm text-gray-400">Admin: Run job scraper to populate jobs</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {jobs.map((job) => (
                  <JobCard
                    key={job.id}
                    {...job}
                    onApply={handleApply}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "applications" && (
          <div>
            <h2 className="text-xl font-semibold mb-4">Your Applications</h2>
            {applications.length === 0 ? (
              <p className="text-gray-500">No applications yet. Start applying to jobs!</p>
            ) : (
              <div className="grid gap-4">
                {applications.map((app) => (
                  <div key={app.id} className="bg-white p-4 rounded-lg shadow">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold text-lg">{app.job_title}</h3>
                        <p className="text-gray-600">{app.company}</p>
                        <div className="mt-2 flex space-x-3 text-sm">
                          <span className={`px-2 py-1 rounded ${
                            app.status === "submitted" ? "bg-green-100 text-green-800" :
                            app.status === "draft" ? "bg-gray-100 text-gray-800" :
                            "bg-blue-100 text-blue-800"
                          }`}>
                            {app.status}
                          </span>
                          <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">
                            {app.stage}
                          </span>
                          {app.match_score && (
                            <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded">
                              {app.match_score}% match
                            </span>
                          )}
                        </div>
                        <p className="mt-2 text-xs text-gray-400">
                          Applied: {new Date(app.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "profile" && (
          <div>
            <h2 className="text-xl font-semibold mb-4">Your Profile</h2>
            <div className="bg-white p-6 rounded-lg shadow">
              <p className="text-gray-600 mb-4">
                Profile management coming soon. You'll be able to:
              </p>
              <ul className="list-disc list-inside space-y-2 text-gray-600">
                <li>Edit your skills and experience</li>
                <li>Upload your resume</li>
                <li>Set job preferences (salary, location, remote)</li>
                <li>View match score breakdowns</li>
              </ul>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
