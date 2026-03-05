"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface Skill {
  id: number;
  name: string;
  category?: string;
  years?: number;
  proficiency?: string;
}

interface Profile {
  id: number;
  first_name?: string;
  last_name?: string;
  location?: string;
  timezone?: string;
  desired_roles: string[];
  desired_industries: string[];
  min_salary?: number;
  max_salary?: number;
  remote_only: boolean;
  relocate: boolean;
  preferred_countries: string[];
  years_of_experience?: number;
  current_title?: string;
  current_company?: string;
  resume_text?: string;
  skills: Skill[];
}

export default function ProfilePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [newSkill, setNewSkill] = useState("");
  
  const [profile, setProfile] = useState<Profile>({
    id: 0,
    first_name: "",
    last_name: "",
    location: "",
    timezone: "UTC",
    desired_roles: [],
    desired_industries: [],
    min_salary: undefined,
    max_salary: undefined,
    remote_only: false,
    relocate: false,
    preferred_countries: ["UK", "US"],
    years_of_experience: undefined,
    current_title: "",
    current_company: "",
    resume_text: "",
    skills: [],
  });

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      router.push("/login");
      return;
    }
    setToken(storedToken);
    fetchProfile(storedToken);
  }, [router]);

  const fetchProfile = async (authToken: string) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/profile/me`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
      }
    } catch (error) {
      console.error("Error fetching profile:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!token) return;
    setSaving(true);
    
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/profile/me`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          first_name: profile.first_name,
          last_name: profile.last_name,
          location: profile.location,
          years_of_experience: profile.years_of_experience,
          current_title: profile.current_title,
          current_company: profile.current_company,
          min_salary: profile.min_salary,
          max_salary: profile.max_salary,
          remote_only: profile.remote_only,
          relocate: profile.relocate,
          preferred_countries: profile.preferred_countries,
          desired_roles: profile.desired_roles,
        }),
      });
      
      if (res.ok) {
        alert("Profile saved!");
      } else {
        alert("Failed to save profile");
      }
    } catch (error) {
      console.error("Error saving profile:", error);
      alert("Error saving profile");
    } finally {
      setSaving(false);
    }
  };

  const handleAddSkill = async () => {
    if (!token || !newSkill.trim()) return;
    
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/profile/me/skills`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name: newSkill.trim() }),
      });
      
      if (res.ok) {
        setNewSkill("");
        fetchProfile(token);
      }
    } catch (error) {
      console.error("Error adding skill:", error);
    }
  };

  const handleRemoveSkill = async (skillId: number) => {
    if (!token) return;
    
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/profile/me/skills/${skillId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (res.ok) {
        fetchProfile(token);
      }
    } catch (error) {
      console.error("Error removing skill:", error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">JobScale</h1>
          <div className="flex items-center space-x-4">
            <a href="/dashboard" className="text-sm text-gray-600 hover:text-gray-900">Dashboard</a>
            <button onClick={handleLogout} className="text-sm text-gray-600 hover:text-gray-900">Logout</button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        <h2 className="text-3xl font-bold mb-6">Your Profile</h2>

        <div className="grid gap-6">
          {/* Personal Info */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">Personal Information</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                <input
                  type="text"
                  value={profile.first_name || ""}
                  onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                <input
                  type="text"
                  value={profile.last_name || ""}
                  onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <input
                  type="text"
                  value={profile.location || ""}
                  onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                  placeholder="e.g., London, UK"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Years of Experience</label>
                <input
                  type="number"
                  value={profile.years_of_experience || ""}
                  onChange={(e) => setProfile({ ...profile, years_of_experience: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Current Title</label>
                <input
                  type="text"
                  value={profile.current_title || ""}
                  onChange={(e) => setProfile({ ...profile, current_title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Current Company</label>
                <input
                  type="text"
                  value={profile.current_company || ""}
                  onChange={(e) => setProfile({ ...profile, current_company: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>
          </div>

          {/* Job Preferences */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">Job Preferences</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Salary (£/$)</label>
                <input
                  type="number"
                  value={profile.min_salary || ""}
                  onChange={(e) => setProfile({ ...profile, min_salary: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Salary (£/$)</label>
                <input
                  type="number"
                  value={profile.max_salary || ""}
                  onChange={(e) => setProfile({ ...profile, max_salary: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div className="flex items-center mt-2">
                <input
                  type="checkbox"
                  id="remote-only"
                  checked={profile.remote_only}
                  onChange={(e) => setProfile({ ...profile, remote_only: e.target.checked })}
                  className="mr-2"
                />
                <label htmlFor="remote-only" className="text-sm text-gray-700">Remote only</label>
              </div>
              <div className="flex items-center mt-2">
                <input
                  type="checkbox"
                  id="relocate"
                  checked={profile.relocate}
                  onChange={(e) => setProfile({ ...profile, relocate: e.target.checked })}
                  className="mr-2"
                />
                <label htmlFor="relocate" className="text-sm text-gray-700">Willing to relocate</label>
              </div>
            </div>
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Countries (comma-separated)</label>
              <input
                type="text"
                value={profile.preferred_countries.join(", ")}
                onChange={(e) => setProfile({ ...profile, preferred_countries: e.target.value.split(",").map(c => c.trim()) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>

          {/* Skills */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-xl font-semibold mb-4">Skills</h3>
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                placeholder="Add a skill (e.g., Python, React)"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                onKeyPress={(e) => e.key === "Enter" && handleAddSkill()}
              />
              <button
                onClick={handleAddSkill}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {profile.skills.map((skill) => (
                <span
                  key={skill.id}
                  className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                >
                  {skill.name}
                  <button
                    onClick={() => handleRemoveSkill(skill.id)}
                    className="ml-2 text-blue-600 hover:text-blue-800"
                  >
                    ×
                  </button>
                </span>
              ))}
              {profile.skills.length === 0 && (
                <p className="text-gray-500 text-sm">No skills added yet</p>
              )}
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save Profile"}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
