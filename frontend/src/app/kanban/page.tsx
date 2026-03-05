"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Navbar from "../../components/Navbar";

interface Application {
  id: number;
  job_id: number;
  job_title: string;
  company: string;
  status: string;
  stage: string;
  match_score?: number;
  submitted_at?: string;
  created_at: string;
}

type Stage = "wishlist" | "applied" | "phone_screen" | "technical" | "onsite" | "offer" | "rejected";

const STAGES: { id: Stage; label: string; color: string }[] = [
  { id: "wishlist", label: "Wishlist", color: "bg-gray-100 border-gray-300" },
  { id: "applied", label: "Applied", color: "bg-blue-50 border-blue-300" },
  { id: "phone_screen", label: "Phone Screen", color: "bg-yellow-50 border-yellow-300" },
  { id: "technical", label: "Technical", color: "bg-orange-50 border-orange-300" },
  { id: "onsite", label: "Onsite", color: "bg-purple-50 border-purple-300" },
  { id: "offer", label: "Offer", color: "bg-green-50 border-green-300" },
  { id: "rejected", label: "Rejected", color: "bg-red-50 border-red-300" },
];

export default function KanbanBoard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [draggingId, setDraggingId] = useState<number | null>(null);

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      router.push("/login");
      return;
    }
    setToken(storedToken);
    fetchApplications(storedToken);
  }, [router]);

  const fetchApplications = async (authToken: string) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/applications/`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setApplications(data);
      }
    } catch (error) {
      console.error("Error fetching applications:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDragStart = (e: React.DragEvent, id: number) => {
    setDraggingId(id);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };

  const handleDrop = async (e: React.DragEvent, stage: Stage) => {
    e.preventDefault();
    if (!draggingId || !token) return;

    // Map stage to status
    const statusMap: Record<Stage, string> = {
      wishlist: "draft",
      applied: "submitted",
      phone_screen: "interviewing",
      technical: "interviewing",
      onsite: "interviewing",
      offer: "offered",
      rejected: "rejected",
    };

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/applications/${draggingId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          stage: stage,
          status: statusMap[stage],
        }),
      });

      if (res.ok) {
        fetchApplications(token);
      }
    } catch (error) {
      console.error("Error updating application:", error);
    } finally {
      setDraggingId(null);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  const getApplicationsByStage = (stage: Stage) => {
    return applications.filter(app => app.stage === stage);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-xl text-gray-600">Loading kanban board...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar isLoggedIn={true} onLogout={handleLogout} />

      <main className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Application Pipeline</h1>
          <div className="text-sm text-gray-500">
            {applications.length} applications • {applications.filter(a => a.stage === "offer").length} offers
          </div>
        </div>

        <div className="flex gap-4 overflow-x-auto pb-4">
          {STAGES.map((stage) => {
            const stageApps = getApplicationsByStage(stage.id);
            
            return (
              <div
                key={stage.id}
                className={`flex-shrink-0 w-80 rounded-lg border-2 ${stage.color} p-4`}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, stage.id)}
              >
                <div className="flex justify-between items-center mb-4">
                  <h2 className="font-semibold text-gray-900">{stage.label}</h2>
                  <span className="text-sm text-gray-500 bg-white px-2 py-1 rounded-full">
                    {stageApps.length}
                  </span>
                </div>

                <div className="space-y-3">
                  {stageApps.map((app) => (
                    <div
                      key={app.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, app.id)}
                      className={`bg-white p-4 rounded-lg shadow-sm border cursor-move hover:shadow-md transition-shadow ${
                        draggingId === app.id ? "opacity-50" : "opacity-100"
                      }`}
                    >
                      <h3 className="font-medium text-gray-900">{app.job_title}</h3>
                      <p className="text-sm text-gray-600">{app.company}</p>
                      
                      {app.match_score !== undefined && (
                        <div className="mt-2">
                          <span className={`text-xs px-2 py-1 rounded ${
                            app.match_score >= 70 ? "bg-green-100 text-green-800" :
                            app.match_score >= 50 ? "bg-yellow-100 text-yellow-800" :
                            "bg-red-100 text-red-800"
                          }`}>
                            {app.match_score}% match
                          </span>
                        </div>
                      )}
                      
                      {app.submitted_at && (
                        <p className="text-xs text-gray-400 mt-2">
                          Applied {new Date(app.submitted_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  ))}
                  
                  {stageApps.length === 0 && (
                    <div className="text-center py-8 text-gray-400 text-sm">
                      No applications
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
