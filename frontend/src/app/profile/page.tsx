"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import AppShell from "@/components/AppShell";
import { useToast } from "@/components/ui/Toast";

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

interface SubscriptionSummary {
  plan?: string;
  status?: string;
  applications_used?: number;
  applications_limit?: number;
}

export default function ProfilePage() {
  const router = useRouter();
  const { user, loading: authLoading, authFetch, logout } = useAuth();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [portalLoading, setPortalLoading] = useState(false);
  const [newSkill, setNewSkill] = useState("");
  const [subscription, setSubscription] = useState<SubscriptionSummary | null>(null);

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
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  const fetchProfile = async () => {
    try {
      const res = await authFetch("/api/v1/profile/me");
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

  const fetchSubscription = async () => {
    try {
      const res = await authFetch("/api/v1/billing/subscription");
      if (res.ok) {
        setSubscription(await res.json());
      } else {
        setSubscription({ plan: "free", status: "active", applications_used: 0, applications_limit: 5 });
      }
    } catch {
      setSubscription({ plan: "free", status: "active" });
    }
  };

  useEffect(() => {
    if (user) {
      fetchProfile();
      fetchSubscription();
    }
  }, [user]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await authFetch("/api/v1/profile/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
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
        toast.success("Profile saved");
      } else {
        toast.error("Failed to save profile");
      }
    } catch (error) {
      console.error("Error saving profile:", error);
      toast.error("Error saving profile");
    } finally {
      setSaving(false);
    }
  };

  const handleAddSkill = async () => {
    if (!newSkill.trim()) return;
    try {
      const res = await authFetch("/api/v1/profile/me/skills", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newSkill.trim() }),
      });

      if (res.ok) {
        setNewSkill("");
        fetchProfile();
      }
    } catch (error) {
      console.error("Error adding skill:", error);
    }
  };

  const handleRemoveSkill = async (skillId: number) => {
    try {
      const res = await authFetch(`/api/v1/profile/me/skills/${skillId}`, {
        method: "DELETE",
      });

      if (res.ok) {
        fetchProfile();
      }
    } catch (error) {
      console.error("Error removing skill:", error);
    }
  };

  const openBillingPortal = async () => {
    setPortalLoading(true);
    try {
      const origin = typeof window !== "undefined" ? window.location.origin : "";
      const q = new URLSearchParams({
        return_url: `${origin}/profile`,
      });
      const res = await authFetch(`/api/v1/billing/portal?${q.toString()}`, {
        method: "POST",
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || "Could not open billing portal");
      }
      if (data.url) {
        window.location.href = data.url;
        return;
      }
      throw new Error("No portal URL returned");
    } catch (e: any) {
      toast.error(e.message || "Portal unavailable");
    } finally {
      setPortalLoading(false);
    }
  };

  if (authLoading || loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center min-h-[40vh] text-slate-500 text-sm">Loading profile…</div>
      </AppShell>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto pb-12">
        <div className="mb-8">
          <h1 className="text-xl font-semibold text-navy-900 tracking-tight">Settings</h1>
          <p className="text-sm text-slate-500 mt-1">{user.email}</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-5 mb-6">
          <h2 className="text-sm font-semibold text-slate-900 mb-2">Plan</h2>
          <p className="text-sm text-slate-600 capitalize mb-1">
            {subscription?.plan || "free"} · {subscription?.status || "active"}
          </p>
          <p className="text-xs text-slate-500 mb-4">
            Applications this month: {subscription?.applications_used ?? 0}
            {subscription?.applications_limit != null ? ` / ${subscription.applications_limit}` : ""}
          </p>
          <button
            type="button"
            onClick={openBillingPortal}
            disabled={portalLoading}
            className="text-sm font-medium text-teal-600 hover:text-teal-700 disabled:opacity-50"
          >
            {portalLoading ? "Opening…" : "Manage billing & subscription"}
          </button>
          <p className="text-xs text-slate-400 mt-2">
            Opens Stripe Customer Portal after you complete a paid checkout.
          </p>
        </div>

        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-lg p-5">
            <h2 className="text-sm font-semibold text-slate-900 mb-4">Personal information</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">First name</label>
                <input
                  type="text"
                  value={profile.first_name || ""}
                  onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Last name</label>
                <input
                  type="text"
                  value={profile.last_name || ""}
                  onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Location</label>
                <input
                  type="text"
                  value={profile.location || ""}
                  onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                  placeholder="e.g., London, UK"
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Years of experience</label>
                <input
                  type="number"
                  value={profile.years_of_experience ?? ""}
                  onChange={(e) =>
                    setProfile({
                      ...profile,
                      years_of_experience: e.target.value ? parseFloat(e.target.value) : undefined,
                    })
                  }
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Current title</label>
                <input
                  type="text"
                  value={profile.current_title || ""}
                  onChange={(e) => setProfile({ ...profile, current_title: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Current company</label>
                <input
                  type="text"
                  value={profile.current_company || ""}
                  onChange={(e) => setProfile({ ...profile, current_company: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-5">
            <h2 className="text-sm font-semibold text-slate-900 mb-4">Job preferences</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Min salary</label>
                <input
                  type="number"
                  value={profile.min_salary ?? ""}
                  onChange={(e) =>
                    setProfile({
                      ...profile,
                      min_salary: e.target.value ? parseInt(e.target.value, 10) : undefined,
                    })
                  }
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Max salary</label>
                <input
                  type="number"
                  value={profile.max_salary ?? ""}
                  onChange={(e) =>
                    setProfile({
                      ...profile,
                      max_salary: e.target.value ? parseInt(e.target.value, 10) : undefined,
                    })
                  }
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="remote-only"
                  checked={profile.remote_only}
                  onChange={(e) => setProfile({ ...profile, remote_only: e.target.checked })}
                  className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <label htmlFor="remote-only" className="text-sm text-slate-700">
                  Remote only
                </label>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="relocate"
                  checked={profile.relocate}
                  onChange={(e) => setProfile({ ...profile, relocate: e.target.checked })}
                  className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <label htmlFor="relocate" className="text-sm text-slate-700">
                  Willing to relocate
                </label>
              </div>
            </div>
            <div className="mt-4">
              <label className="block text-xs font-medium text-slate-600 mb-1">Preferred countries (comma-separated)</label>
              <input
                type="text"
                value={profile.preferred_countries.join(", ")}
                onChange={(e) =>
                  setProfile({
                    ...profile,
                    preferred_countries: e.target.value.split(",").map((c) => c.trim()).filter(Boolean),
                  })
                }
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
              />
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-5">
            <h2 className="text-sm font-semibold text-slate-900 mb-4">Skills</h2>
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                placeholder="Add a skill"
                className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddSkill())}
              />
              <button
                type="button"
                onClick={handleAddSkill}
                className="px-4 py-2 text-sm font-medium rounded-lg bg-navy-900 text-white hover:bg-navy-800"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {profile.skills.map((skill) => (
                <span
                  key={skill.id}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-slate-100 text-slate-800 rounded-full text-sm"
                >
                  {skill.name}
                  <button type="button" onClick={() => handleRemoveSkill(skill.id)} className="text-slate-500 hover:text-slate-800 ml-1">
                    ×
                  </button>
                </span>
              ))}
              {profile.skills.length === 0 && <p className="text-sm text-slate-500">No skills yet</p>}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="px-5 py-2.5 text-sm font-medium rounded-lg bg-teal-500 text-white hover:bg-teal-600 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save changes"}
            </button>
            <button
              type="button"
              onClick={() => logout()}
              className="px-5 py-2.5 text-sm font-medium rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
