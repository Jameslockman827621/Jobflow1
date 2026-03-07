'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';

interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  remote: boolean;
  min_salary?: number;
  max_salary?: number;
  posted_date: string;
  external_url: string;
}

interface OnboardingStatus {
  onboarding_complete: boolean;
  has_preferences: boolean;
  has_cached_jobs: boolean;
  cache?: {
    is_expired: boolean;
    expires_at: string;
  };
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading: authLoading, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [onboardingStatus, setOnboardingStatus] = useState<OnboardingStatus | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      loadDashboard();
    }
  }, [user]);

  async function loadDashboard() {
    try {
      setLoading(true);
      
      // Load onboarding status
      const statusRes = await fetch('/api/v1/onboarding/status');
      if (statusRes.ok) {
        const status = await statusRes.json();
        setOnboardingStatus(status);
        
        // If onboarding not complete, redirect
        if (!status.onboarding_complete) {
          router.push('/onboarding');
          return;
        }
        
        // If has cached jobs, load them
        if (status.has_cached_jobs && !status.cache?.is_expired) {
          const searchRes = await fetch('/api/v1/onboarding/search');
          if (searchRes.ok) {
            const searchData = await searchRes.json();
            setJobs(searchData.jobs || []);
          }
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500"></div>
      </div>
    );
  }

  if (!onboardingStatus?.onboarding_complete) {
    return null; // Will redirect
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-slate-600">{user?.email}</span>
              <button
                onClick={logout}
                className="px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="text-sm text-slate-600 mb-1">Total Jobs</div>
            <div className="text-3xl font-bold text-slate-900">{jobs.length}</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="text-sm text-slate-600 mb-1">Applications</div>
            <div className="text-3xl font-bold text-slate-900">0</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="text-sm text-slate-600 mb-1">Cache Status</div>
            <div className="text-lg font-semibold text-slate-900">
              {onboardingStatus?.cache?.is_expired ? '⚠️ Expired' : '✅ Fresh'}
            </div>
          </div>
        </div>

        {/* Jobs List */}
        <div className="bg-white rounded-xl shadow-sm">
          <div className="p-6 border-b border-slate-200">
            <h2 className="text-lg font-semibold text-slate-900">Your Jobs</h2>
          </div>
          
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 text-red-700">
              {error}
            </div>
          )}

          {jobs.length === 0 ? (
            <div className="p-8 text-center text-slate-600">
              <p>No jobs found. Try refreshing your search.</p>
              <button
                onClick={loadDashboard}
                className="mt-4 px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors"
              >
                Refresh Search
              </button>
            </div>
          ) : (
            <div className="divide-y divide-slate-200">
              {jobs.map((job) => (
                <div key={job.id} className="p-6 hover:bg-slate-50 transition-colors">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900">{job.title}</h3>
                      <p className="text-slate-600">{job.company}</p>
                      <div className="mt-2 flex items-center space-x-4 text-sm text-slate-500">
                        <span>📍 {job.location}</span>
                        {job.remote && <span>🏠 Remote</span>}
                        {job.max_salary && (
                          <span>💰 £{job.max_salary.toLocaleString()}</span>
                        )}
                      </div>
                    </div>
                    <a
                      href={job.external_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2 bg-navy-900 text-white rounded-lg hover:bg-navy-800 transition-colors text-sm"
                    >
                      Apply
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
