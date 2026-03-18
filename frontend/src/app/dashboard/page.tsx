'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toast';
import AppShell from '@/components/AppShell';

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

function SkeletonCard() {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5 animate-pulse">
      <div className="flex items-center justify-between mb-3">
        <div className="h-3 w-20 bg-slate-100 rounded" />
        <div className="w-9 h-9 bg-slate-100 rounded-lg" />
      </div>
      <div className="h-8 w-16 bg-slate-100 rounded mt-1" />
    </div>
  );
}

function SkeletonRow() {
  return (
    <div className="px-5 py-4 animate-pulse">
      <div className="flex items-start gap-3">
        <div className="w-4 h-4 bg-slate-100 rounded mt-0.5" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-48 bg-slate-100 rounded" />
          <div className="h-3 w-32 bg-slate-100 rounded" />
          <div className="flex gap-2 mt-1">
            <div className="h-5 w-16 bg-slate-50 rounded" />
            <div className="h-5 w-20 bg-slate-50 rounded" />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPageWrapper() {
  return (
    <Suspense fallback={
      <AppShell>
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <div className="h-7 w-36 bg-slate-100 rounded animate-pulse" />
            <div className="h-4 w-52 bg-slate-50 rounded mt-2 animate-pulse" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
          <div className="bg-white rounded-lg border border-slate-200">
            <div className="px-5 py-4 border-b border-slate-200">
              <div className="h-5 w-28 bg-slate-100 rounded animate-pulse" />
            </div>
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
          </div>
        </div>
      </AppShell>
    }>
      <DashboardPage />
    </Suspense>
  );
}

function BriefcaseIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0" />
    </svg>
  );
}

function DocumentStackIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  );
}

function CheckCircleIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function DashboardPage() {
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
        const autoApplyRes = await authFetch('/api/v1/auto-apply/jobs');
        if (autoApplyRes.ok) {
          const autoApplyData = await autoApplyRes.json();
          setSelectedJobs(new Set((autoApplyData.jobs || []).map((j: { id: number }) => j.id)));
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

  async function toggleJobSelection(jobId: number) {
    const nextSelected = !selectedJobs.has(jobId);
    setSelectedJobs(prev => {
      const next = new Set(prev);
      if (next.has(jobId)) next.delete(jobId); else next.add(jobId);
      return next;
    });
    try {
      const res = nextSelected
        ? await authFetch(`/api/v1/auto-apply/jobs/${jobId}`, { method: 'POST' })
        : await authFetch(`/api/v1/auto-apply/jobs/${jobId}`, { method: 'DELETE' });
      if (!res.ok) {
        setSelectedJobs(prev => {
          const revert = new Set(prev);
          if (nextSelected) revert.delete(jobId); else revert.add(jobId);
          return revert;
        });
      }
    } catch {
      setSelectedJobs(prev => {
        const revert = new Set(prev);
        if (nextSelected) revert.delete(jobId); else revert.add(jobId);
        return revert;
      });
    }
  }

  async function selectAll() {
    const selectAll = selectedJobs.size !== jobs.length;
    if (selectAll) {
      setSelectedJobs(new Set(jobs.map(j => j.id)));
      for (const job of jobs) {
        try {
          await authFetch(`/api/v1/auto-apply/jobs/${job.id}`, { method: 'POST' });
        } catch { /* ignore */ }
      }
    } else {
      setSelectedJobs(new Set());
      for (const job of jobs) {
        try {
          await authFetch(`/api/v1/auto-apply/jobs/${job.id}`, { method: 'DELETE' });
        } catch { /* ignore */ }
      }
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
      <AppShell>
        <div className="max-w-6xl mx-auto">
          <div className="mb-6">
            <div className="h-7 w-36 bg-slate-100 rounded animate-pulse" />
            <div className="h-4 w-52 bg-slate-50 rounded mt-2 animate-pulse" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
          <div className="bg-white rounded-lg border border-slate-200">
            <div className="px-5 py-4 border-b border-slate-200">
              <div className="h-5 w-28 bg-slate-100 rounded animate-pulse" />
            </div>
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
          </div>
        </div>
      </AppShell>
    );
  }

  if (!onboardingStatus?.onboarding_complete) return null;

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto pb-20">
        {/* Page header */}
        <div className="mb-6">
          <h1 className="text-xl font-semibold text-navy-900 tracking-tight">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">Your job search at a glance</p>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-lg border border-slate-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Matched Jobs</span>
              <div className="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center">
                <BriefcaseIcon className="w-4 h-4 text-teal-600" />
              </div>
            </div>
            <div className="text-2xl font-semibold text-slate-900 tabular-nums">{jobs.length}</div>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Applications</span>
              <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center">
                <DocumentStackIcon className="w-4 h-4 text-slate-500" />
              </div>
            </div>
            <div className="text-2xl font-semibold text-slate-900 tabular-nums">{appCount}</div>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Selected</span>
              <div className="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center">
                <CheckCircleIcon className="w-4 h-4 text-teal-600" />
              </div>
            </div>
            <div className="text-2xl font-semibold text-teal-600 tabular-nums">{selectedJobs.size}</div>
          </div>
        </div>

        {/* Jobs list */}
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <div className="px-5 py-3.5 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h2 className="text-sm font-semibold text-slate-900">Matched Jobs</h2>
              {jobs.length > 0 && (
                <button onClick={selectAll} className="text-xs text-teal-600 hover:text-teal-700 font-medium">
                  {selectedJobs.size === jobs.length ? 'Deselect all' : 'Select all'}
                </button>
              )}
            </div>
            <button onClick={loadDashboard} className="p-1.5 text-slate-400 hover:text-teal-600 hover:bg-slate-50 rounded-md transition-colors" aria-label="Refresh">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" /></svg>
            </button>
          </div>

          {error && (
            <div className="px-5 py-3 bg-red-50 border-b border-red-100 text-red-700 text-sm flex items-center gap-2">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" /></svg>
              {error}
            </div>
          )}

          {jobs.length === 0 ? (
            <div className="px-5 py-16 text-center">
              <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg>
              </div>
              <p className="text-sm font-medium text-slate-900 mb-1">No jobs found yet</p>
              <p className="text-sm text-slate-500 mb-5">Try refreshing or adjust your search preferences.</p>
              <button onClick={loadDashboard} className="px-4 py-2 bg-teal-500 text-white rounded-md hover:bg-teal-600 text-sm font-medium transition-colors">
                Refresh Search
              </button>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {jobs.map((job) => {
                const isSelected = selectedJobs.has(job.id);
                return (
                  <div
                    key={job.id}
                    onClick={() => toggleJobSelection(job.id)}
                    className={`px-5 py-4 cursor-pointer transition-colors border-l-2 ${
                      isSelected
                        ? 'border-l-teal-500 bg-teal-50/40'
                        : 'border-l-transparent hover:bg-slate-50/60'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <label className="flex items-center pt-0.5 cursor-pointer" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleJobSelection(job.id)}
                          className="w-4 h-4 text-teal-500 border-slate-300 rounded focus:ring-teal-500 cursor-pointer"
                        />
                      </label>
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                          <div className="min-w-0">
                            <h3 className="text-sm font-medium text-slate-900 leading-snug">{job.title}</h3>
                            <p className="text-sm text-slate-500 mt-0.5">{job.company}</p>
                            <div className="flex flex-wrap items-center gap-2 mt-2">
                              <span className="inline-flex items-center gap-1 text-xs text-slate-500">
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" /></svg>
                                {job.location}
                              </span>
                              {job.remote && (
                                <span className="inline-flex items-center px-1.5 py-0.5 bg-teal-50 text-teal-700 rounded text-[11px] font-medium">Remote</span>
                              )}
                              {job.max_salary && (
                                <span className="inline-flex items-center px-1.5 py-0.5 bg-slate-50 text-slate-600 rounded text-[11px] font-medium">{'\u00A3'}{job.max_salary.toLocaleString()}</span>
                              )}
                              {job.source && (
                                <span className="inline-flex items-center px-1.5 py-0.5 bg-slate-50 text-slate-400 rounded text-[11px]">{job.source}</span>
                              )}
                            </div>
                          </div>
                          {job.external_url && (
                            <a
                              href={job.external_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="flex-shrink-0 text-xs font-medium text-teal-600 hover:text-teal-700 flex items-center gap-1"
                            >
                              View
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" /></svg>
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Fixed bottom action bar */}
      {selectedJobs.size > 0 && (
        <div className="fixed bottom-0 left-0 lg:left-56 right-0 z-30 bg-white border-t border-slate-200 shadow-[0_-4px_16px_rgba(0,0,0,0.06)]">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
            <p className="text-sm text-slate-600">
              <span className="font-semibold text-navy-900">{selectedJobs.size}</span> job{selectedJobs.size !== 1 ? 's' : ''} selected
            </p>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSelectedJobs(new Set())}
                className="px-3 py-1.5 text-sm text-slate-500 hover:text-slate-700 hover:bg-slate-50 rounded-md transition-colors font-medium"
              >
                Clear
              </button>
              <button
                onClick={handleApplySelected}
                disabled={applying}
                className="px-6 py-2.5 bg-navy-900 text-white rounded-lg text-sm font-semibold disabled:opacity-50 flex items-center gap-2 transition-colors hover:bg-navy-800 shadow-sm"
              >
                {applying ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white" />
                    <span>Applying...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" /></svg>
                    <span>Apply to Selected</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Batch Apply Results Modal */}
      {showModal && batchResults.length > 0 && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-5 border-b border-slate-200">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-semibold text-navy-900">Applications Ready</h3>
                  <p className="text-sm text-slate-500 mt-0.5">{batchResults.length} application{batchResults.length !== 1 ? 's' : ''} prepared</p>
                </div>
                <button onClick={() => setShowModal(false)} className="p-1.5 text-slate-400 hover:text-slate-600 rounded-md hover:bg-slate-100 transition-colors">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
            </div>
            <div className="px-6 py-4">
              <p className="text-sm text-slate-600 mb-4">Your applications have been prepared. The Chrome extension will auto-apply to these jobs, or you can apply manually using the links below.</p>
              <div className="space-y-2">
                {batchResults.map((result, i) => (
                  <div key={i} className={`p-3.5 rounded-lg border ${result.status === 'already_applied' ? 'border-amber-200 bg-amber-50/50' : 'border-slate-200 bg-slate-50/50'}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <h4 className="text-sm font-medium text-slate-900">{result.job_title}</h4>
                        <p className="text-xs text-slate-500 mt-0.5">{result.company}</p>
                      </div>
                      {result.status === 'already_applied' ? (
                        <span className="flex-shrink-0 text-xs font-medium text-amber-700 bg-amber-100 px-2 py-1 rounded">Already Applied</span>
                      ) : (
                        <a href={result.job_url} target="_blank" rel="noopener noreferrer" className="flex-shrink-0 text-xs font-medium text-teal-600 hover:text-teal-700 flex items-center gap-1">
                          Apply
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" /></svg>
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="px-6 py-4 border-t border-slate-200">
              <button onClick={() => setShowModal(false)} className="w-full px-4 py-2.5 bg-navy-900 text-white text-sm font-medium rounded-lg hover:bg-navy-800 transition-colors">
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
