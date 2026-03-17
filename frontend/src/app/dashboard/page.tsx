'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toast';

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
  source?: string;
}

interface OnboardingStatus {
  onboarding_complete: boolean;
  has_preferences: boolean;
  has_cached_jobs: boolean;
  cache?: { is_expired: boolean; expires_at: string };
}

interface ApplicationPackage {
  application_id: number;
  cv_download_url: string;
  job_url: string;
  job_title: string;
  company: string;
  application_tips: string[];
  status: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading: authLoading, logout, authFetch } = useAuth();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [batchResults, setBatchResults] = useState<any[]>([]);
  const [onboardingStatus, setOnboardingStatus] = useState<OnboardingStatus | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobs, setSelectedJobs] = useState<Set<number>>(new Set());
  const [error, setError] = useState('');
  const [appCount, setAppCount] = useState(0);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) loadDashboard();
  }, [user]);

  useEffect(() => {
    if (searchParams.get('onboarding') === 'complete') {
      toast.success(`Onboarding complete! Found ${searchParams.get('jobs') || 'new'} jobs.`);
    }
  }, [searchParams]);

  async function loadDashboard() {
    try {
      setLoading(true);
      const statusRes = await authFetch('/api/v1/onboarding/status');
      if (statusRes.ok) {
        const status = await statusRes.json();
        setOnboardingStatus(status);
        if (!status.onboarding_complete) {
          router.push('/onboarding');
          return;
        }
        if (status.has_cached_jobs) {
          const searchRes = await authFetch('/api/v1/onboarding/search', { method: 'POST' });
          if (searchRes.ok) {
            const searchData = await searchRes.json();
            setJobs(searchData.jobs || []);
          }
        }
      }
      const statsRes = await authFetch('/api/v1/applications/stats/summary');
      if (statsRes.ok) {
        const stats = await statsRes.json();
        setAppCount(stats.total || 0);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }

  function toggleJobSelection(jobId: number) {
    setSelectedJobs(prev => {
      const next = new Set(prev);
      if (next.has(jobId)) next.delete(jobId); else next.add(jobId);
      return next;
    });
  }

  function selectAll() {
    if (selectedJobs.size === jobs.length) {
      setSelectedJobs(new Set());
    } else {
      setSelectedJobs(new Set(jobs.map(j => j.id)));
    }
  }

  async function handleApplySelected() {
    if (selectedJobs.size === 0) {
      toast.error('Select at least one job to apply to');
      return;
    }
    setApplying(true);
    try {
      const res = await authFetch('/api/v1/applications/batch-start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_ids: Array.from(selectedJobs) })
      });
      if (!res.ok) {
        const err = await res.json();
        if (err.detail?.includes('No CV found')) {
          toast.error('Please create a CV first');
          router.push('/cv-builder');
          return;
        }
        throw new Error(err.detail || 'Failed to start applications');
      }
      const data = await res.json();
      setBatchResults(data.applications || []);
      setShowModal(true);
      setSelectedJobs(new Set());
      toast.success(`${data.total} applications started!`);
      loadDashboard();
    } catch (err: any) {
      toast.error(err.message || 'Failed to apply');
    } finally {
      setApplying(false);
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-4"></div>
          <p className="text-slate-600 text-sm">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!onboardingStatus?.onboarding_complete) return null;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900">Dashboard</h1>
            <div className="flex items-center space-x-2 sm:space-x-4">
              <span className="hidden sm:block text-sm text-slate-600 truncate max-w-[150px]">{user?.email}</span>
              <button onClick={() => router.push('/cv-builder')} className="hidden sm:block px-4 py-2 text-sm text-teal-600 hover:bg-teal-50 rounded-lg">My CVs</button>
              <button onClick={() => router.push('/kanban')} className="hidden sm:block px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg">Tracker</button>
              <button onClick={logout} className="px-3 sm:px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 rounded-lg min-h-[44px] min-w-[44px] flex items-center justify-center" aria-label="Logout">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <div className="bg-white rounded-xl shadow-sm p-5 sm:p-6">
            <div className="text-sm text-slate-600 mb-1">Matched Jobs</div>
            <div className="text-3xl font-bold text-slate-900">{jobs.length}</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-5 sm:p-6">
            <div className="text-sm text-slate-600 mb-1">Applications</div>
            <div className="text-3xl font-bold text-slate-900">{appCount}</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-5 sm:p-6">
            <div className="text-sm text-slate-600 mb-1">Selected to Apply</div>
            <div className="text-3xl font-bold text-teal-600">{selectedJobs.size}</div>
          </div>
        </div>

        {/* Action Bar */}
        {selectedJobs.size > 0 && (
          <div className="bg-teal-50 border border-teal-200 rounded-xl p-4 mb-6 flex flex-col sm:flex-row items-center justify-between gap-3">
            <p className="text-teal-800 font-medium">{selectedJobs.size} job{selectedJobs.size !== 1 ? 's' : ''} selected</p>
            <div className="flex space-x-3">
              <button onClick={() => setSelectedJobs(new Set())} className="px-4 py-2 text-sm text-slate-700 hover:bg-white rounded-lg">Clear</button>
              <button onClick={handleApplySelected} disabled={applying} className="px-6 py-2.5 bg-teal-500 text-white rounded-lg hover:bg-teal-600 font-semibold text-sm disabled:opacity-50 flex items-center space-x-2">
                {applying ? (
                  <><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div><span>Applying...</span></>
                ) : (
                  <><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg><span>Apply to Selected</span></>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Jobs List */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="p-4 sm:p-6 border-b border-slate-200 flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <h2 className="text-lg font-semibold text-slate-900">Your Matched Jobs</h2>
              {jobs.length > 0 && (
                <button onClick={selectAll} className="text-sm text-teal-600 hover:text-teal-700 font-medium">
                  {selectedJobs.size === jobs.length ? 'Deselect All' : 'Select All'}
                </button>
              )}
            </div>
            <button onClick={loadDashboard} className="p-2 text-teal-600 hover:bg-teal-50 rounded-lg min-h-[44px] min-w-[44px] flex items-center justify-center" aria-label="Refresh">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
            </button>
          </div>

          {error && <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>}

          {jobs.length === 0 ? (
            <div className="p-8 text-center text-slate-600">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
              </div>
              <p className="text-base font-medium mb-4">No jobs found yet</p>
              <button onClick={loadDashboard} className="px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 font-medium">Refresh Search</button>
            </div>
          ) : (
            <div className="divide-y divide-slate-200">
              {jobs.map((job) => (
                <div key={job.id} className={`p-4 sm:p-6 hover:bg-slate-50 transition-colors ${selectedJobs.has(job.id) ? 'bg-teal-50/50' : ''}`}>
                  <div className="flex items-start space-x-4">
                    <label className="flex items-center mt-1 cursor-pointer">
                      <input type="checkbox" checked={selectedJobs.has(job.id)} onChange={() => toggleJobSelection(job.id)}
                        className="w-5 h-5 text-teal-500 border-slate-300 rounded focus:ring-teal-500 cursor-pointer" />
                    </label>
                    <div className="flex-1">
                      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start space-y-2 sm:space-y-0">
                        <div>
                          <h3 className="text-base sm:text-lg font-semibold text-slate-900 mb-1">{job.title}</h3>
                          <p className="text-slate-600 text-sm sm:text-base mb-2">{job.company}</p>
                          <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm text-slate-500">
                            <span className="flex items-center space-x-1">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                              <span>{job.location}</span>
                            </span>
                            {job.remote && <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">Remote</span>}
                            {job.max_salary && <span className="text-slate-600 font-medium">{'\u00A3'}{job.max_salary.toLocaleString()}</span>}
                            {job.source && <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full text-xs">{job.source}</span>}
                          </div>
                        </div>
                        {job.external_url && (
                          <a href={job.external_url} target="_blank" rel="noopener noreferrer" className="text-sm text-teal-600 hover:text-teal-700 font-medium whitespace-nowrap">
                            View Job &rarr;
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Batch Apply Results Modal */}
      {showModal && batchResults.length > 0 && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-200">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-slate-900">Applications Ready!</h3>
                <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
            </div>
            <div className="p-6 space-y-3">
              <p className="text-sm text-slate-600 mb-4">Your applications have been prepared. The Chrome extension will auto-apply to these jobs, or you can apply manually by clicking the links below.</p>
              {batchResults.map((result, i) => (
                <div key={i} className={`p-4 rounded-xl border ${result.status === 'already_applied' ? 'border-yellow-200 bg-yellow-50' : 'border-green-200 bg-green-50'}`}>
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-semibold text-slate-900 text-sm">{result.job_title}</h4>
                      <p className="text-xs text-slate-600">{result.company}</p>
                    </div>
                    {result.status === 'already_applied' ? (
                      <span className="text-xs font-medium text-yellow-700 bg-yellow-100 px-2 py-1 rounded">Already Applied</span>
                    ) : (
                      <a href={result.job_url} target="_blank" rel="noopener noreferrer" className="text-xs font-medium text-teal-600 hover:text-teal-700">Apply Now &rarr;</a>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <div className="p-6 border-t border-slate-200">
              <button onClick={() => setShowModal(false)} className="w-full px-4 py-3 bg-navy-900 text-white font-semibold rounded-lg hover:bg-navy-800">
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
