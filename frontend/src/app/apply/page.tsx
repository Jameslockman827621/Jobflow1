'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toast';
import AppShell from '@/components/AppShell';

interface QueueItem {
  id: number;
  job_id: number;
  status: 'approved' | 'in_progress' | 'applied' | 'skipped';
  ats_score: number | null;
  approved_at: string | null;
  started_at: string | null;
  applied_at: string | null;
  tailored_cv_url: string;
  tailored_cv_pdf_url: string;
  job: {
    id: number;
    title: string;
    company: string;
    location: string;
    external_url: string;
    description: string;
    source: string;
  } | null;
}

interface QueueResponse {
  queue: QueueItem[];
  total: number;
  counts: { approved: number; in_progress: number; applied: number; skipped: number };
}

export default function ApplyQueuePage() {
  const router = useRouter();
  const { authFetch, user, loading: authLoading } = useAuth();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [counts, setCounts] = useState({ approved: 0, in_progress: 0, applied: 0, skipped: 0 });
  const [current, setCurrent] = useState<QueueItem | null>(null);
  const [busy, setBusy] = useState(false);

  const loadQueue = useCallback(async () => {
    try {
      const res = await authFetch('/api/v1/auto-apply/queue');
      if (res.ok) {
        const data: QueueResponse = await res.json();
        setQueue(data.queue);
        setCounts(data.counts);
        // Auto-pick the next item to focus on — prioritize in_progress (resume mid-application)
        // over approved (haven't started yet)
        const inProgress = data.queue.find(q => q.status === 'in_progress');
        const next = inProgress || data.queue.find(q => q.status === 'approved');
        setCurrent(next || null);
      }
    } catch (err) {
      console.error('Failed to load queue:', err);
    } finally {
      setLoading(false);
    }
  }, [authFetch]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login?next=/apply');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) loadQueue();
  }, [user, loadQueue]);

  async function startNext() {
    if (!current) return;
    setBusy(true);
    try {
      // Mark the current item as in_progress
      const res = await authFetch(`/api/v1/auto-apply/queue/${current.id}/start`, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to start (${res.status})`);
      }
      const data = await res.json();
      setCurrent(data.queue_item);
      // Open the application URL in a new tab — the extension content script will
      // auto-fill the form + attach the tailored PDF CV
      const url = data.queue_item?.job?.external_url;
      if (url) {
        window.open(url, '_blank');
        toast.success('Application page opened — the extension will auto-fill the form. Click Submit when ready.');
      } else {
        toast.error('Job URL missing — try the next job');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to start');
    } finally {
      setBusy(false);
    }
  }

  async function markApplied() {
    if (!current) return;
    setBusy(true);
    try {
      const res = await authFetch(`/api/v1/auto-apply/queue/${current.id}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skip: false }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to mark applied (${res.status})`);
      }
      const data = await res.json();
      toast.success('Marked as applied! 🎉');
      if (data.next) {
        setCurrent(data.next);
      } else {
        setCurrent(null);
        toast.success("🎉 Queue complete! You've applied to all your approved jobs.");
      }
      loadQueue();
    } catch (err: any) {
      toast.error(err.message || 'Failed to mark applied');
    } finally {
      setBusy(false);
    }
  }

  async function skipCurrent() {
    if (!current) return;
    setBusy(true);
    try {
      const res = await authFetch(`/api/v1/auto-apply/queue/${current.id}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skip: true }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to skip (${res.status})`);
      }
      const data = await res.json();
      toast.info('Skipped — moving to next job');
      if (data.next) {
        setCurrent(data.next);
      } else {
        setCurrent(null);
      }
      loadQueue();
    } catch (err: any) {
      toast.error(err.message || 'Failed to skip');
    } finally {
      setBusy(false);
    }
  }

  async function removeFromQueue(id: number) {
    try {
      const res = await authFetch(`/api/v1/auto-apply/queue/${id}`, { method: 'DELETE' });
      if (res.ok) {
        loadQueue();
        toast.info('Removed from queue');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to remove');
    }
  }

  function getApiBase() {
    if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
    if (process.env.NEXT_PUBLIC_BACKEND_URL) return `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1`;
    return '/api/v1';
  }

  // Authenticated file download — fetches with the user's token and opens as a
  // blob URL so the browser can display/download it. Plain <a href> would 401
  // because browsers don't send Authorization headers on navigation.
  async function openAuthenticatedFile(path: string, filename: string, mime: string) {
    try {
      const res = await authFetch(path);
      if (!res.ok) {
        toast.error('Could not load file — please sign in again');
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(new Blob([blob], { type: mime }));
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 30000);
    } catch (err: any) {
      toast.error(err.message || 'Download failed');
    }
  }

  if (authLoading || loading) {
    return (
      <AppShell>
        <div className="max-w-4xl mx-auto">
          <div className="mb-6">
            <div className="h-7 w-36 bg-slate-100 rounded animate-pulse" />
            <div className="h-4 w-52 bg-slate-50 rounded mt-2 animate-pulse" />
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-12 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-slate-200 border-t-teal-500" />
          </div>
        </div>
      </AppShell>
    );
  }

  const totalDone = counts.applied + counts.skipped;
  const progressPct = counts.approved + counts.in_progress + totalDone > 0
    ? Math.round((totalDone / (counts.approved + counts.in_progress + totalDone)) * 100)
    : 0;

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Apply Queue</h1>
              <p className="text-sm text-slate-500 mt-1">Approve jobs once, then walk through them with everything pre-filled</p>
            </div>
            {counts.approved > 0 && (
              <button
                onClick={async () => {
                  try {
                    const res = await authFetch('/api/v1/auto-apply/auto-session/start', { method: 'POST' });
                    if (!res.ok) throw new Error('Failed to start session');
                    const data = await res.json();
                    if (data.jobs && data.jobs.length > 0) {
                      // Send the job list to the extension to process autonomously
                      try {
                        const chromeRef = (window as any).chrome;
                        if (chromeRef?.runtime?.sendMessage) {
                          chromeRef.runtime.sendMessage(
                            { action: 'autoSession', jobs: data.jobs },
                            (response: any) => {
                              if (response?.ok) {
                                toast.success(`Autonomous session started — the extension will apply to ${data.total} jobs automatically. You can walk away.`);
                              } else {
                                toast.error('Extension not responding. Make sure the JobScale extension is installed and enabled.');
                              }
                            }
                          );
                        } else {
                          toast.error('Chrome extension not detected. Install it to use autonomous apply.');
                        }
                      } catch {
                        toast.error('Extension not available — you can still apply manually with the buttons below.');
                      }
                    } else {
                      toast.info(data.message || 'No approved jobs to apply to.');
                    }
                  } catch (err: any) {
                    toast.error(err.message || 'Failed to start session');
                  }
                }}
                className="px-5 py-2.5 bg-gradient-to-r from-teal-500 to-emerald-500 text-white rounded-lg font-semibold text-sm hover:from-teal-600 hover:to-emerald-600 transition-all flex items-center gap-2 shadow-md"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                Start autonomous session
              </button>
            )}
          </div>
        </div>

        {/* Stats + progress */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="text-xs text-slate-500 uppercase tracking-wide">Approved</div>
            <div className="text-2xl font-bold text-teal-600 mt-1">{counts.approved}</div>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="text-xs text-slate-500 uppercase tracking-wide">In Progress</div>
            <div className="text-2xl font-bold text-amber-600 mt-1">{counts.in_progress}</div>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="text-xs text-slate-500 uppercase tracking-wide">Applied</div>
            <div className="text-2xl font-bold text-emerald-600 mt-1">{counts.applied}</div>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="text-xs text-slate-500 uppercase tracking-wide">Skipped</div>
            <div className="text-2xl font-bold text-slate-400 mt-1">{counts.skipped}</div>
          </div>
        </div>

        {/* Current job — the hero card */}
        {current ? (
          <div className="bg-gradient-to-br from-navy-900 to-slate-800 rounded-2xl p-6 text-white mb-6 shadow-xl">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="text-xs text-teal-300 uppercase tracking-wide mb-1">Current job</div>
                <h2 className="text-2xl font-bold">{current.job?.title}</h2>
                <p className="text-slate-300 mt-1">{current.job?.company} · {current.job?.location || 'Remote'}</p>
              </div>
              {current.ats_score != null && current.ats_score > 0 && (
                <div className="text-right">
                  <div className="text-xs text-slate-400 uppercase tracking-wide">ATS Score</div>
                  <div className="text-3xl font-bold text-teal-400">{Math.round(current.ats_score)}</div>
                  <div className="text-xs text-slate-400">out of 100</div>
                </div>
              )}
            </div>

            {current.job?.description && (
              <p className="text-sm text-slate-300 mb-4 line-clamp-3">{current.job.description}</p>
            )}

            {/* Tailored CV preview link */}
            <div className="bg-white/10 rounded-lg p-3 mb-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-teal-500 flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>
                </div>
                <div>
                  <p className="text-sm font-medium">Tailored CV ready</p>
                  <p className="text-xs text-slate-400">Auto-personalized for this job — passes AI screening</p>
                </div>
              </div>
              <div className="flex gap-2">
                <a
                  href={current.tailored_cv_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={async (e) => {
                    e.preventDefault();
                    try {
                      const res = await authFetch(current.tailored_cv_url);
                      if (res.ok) {
                        const blob = await res.blob();
                        const url = URL.createObjectURL(blob);
                        window.open(url, '_blank');
                        setTimeout(() => URL.revokeObjectURL(url), 60000);
                      } else {
                        toast.error('Could not preview CV — please sign in again');
                      }
                    } catch {
                      toast.error('Preview failed');
                    }
                  }}
                  className="text-xs px-3 py-1.5 rounded-md bg-white/10 hover:bg-white/20 transition-colors"
                >
                  Preview
                </a>
                <button
                  onClick={() => openAuthenticatedFile(current.tailored_cv_pdf_url, 'tailored_cv.pdf', 'application/pdf')}
                  className="text-xs px-3 py-1.5 rounded-md bg-teal-500 hover:bg-teal-600 transition-colors font-medium"
                >
                  Download PDF
                </button>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              {current.status === 'approved' && (
                <button
                  onClick={startNext}
                  disabled={busy}
                  className="flex-1 px-6 py-3 bg-teal-500 hover:bg-teal-600 text-white rounded-lg font-semibold transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {busy ? (
                    <><div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white" /> Opening...</>
                  ) : (
                    <>🚀 Open application page (auto-fill enabled)</>
                  )}
                </button>
              )}
              {current.status === 'in_progress' && (
                <>
                  <a
                    href={current.job?.external_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" /></svg>
                    Reopen application
                  </a>
                  <button
                    onClick={skipCurrent}
                    disabled={busy}
                    className="px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-lg font-semibold transition-colors disabled:opacity-50"
                  >
                    Skip
                  </button>
                  <button
                    onClick={markApplied}
                    disabled={busy}
                    className="flex-1 px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-semibold transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {busy ? (
                      <><div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white" /> Saving...</>
                    ) : (
                      <>✓ I've submitted my application</>
                    )}
                  </button>
                </>
              )}
            </div>

            <p className="text-xs text-slate-400 mt-3 text-center">
              💡 The Chrome extension will auto-fill the form and attach your tailored PDF. You just review and click Submit.
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center mb-6">
            {counts.applied + counts.skipped > 0 ? (
              <>
                <div className="text-5xl mb-3">🎉</div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">Queue complete!</h2>
                <p className="text-slate-600 mb-4">You've applied to {counts.applied} job{counts.applied !== 1 ? 's' : ''} and skipped {counts.skipped}.</p>
                <button
                  onClick={() => router.push('/dashboard')}
                  className="px-6 py-2.5 bg-navy-900 text-white rounded-lg font-semibold hover:bg-navy-800 transition-colors"
                >
                  Find more jobs →
                </button>
              </>
            ) : (
              <>
                <div className="text-5xl mb-3">📋</div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">Your apply queue is empty</h2>
                <p className="text-slate-600 mb-4">Go to your dashboard, select the jobs you like, and click "Approve &amp; Tailor CVs" to add them here.</p>
                <button
                  onClick={() => router.push('/dashboard')}
                  className="px-6 py-2.5 bg-teal-500 text-white rounded-lg font-semibold hover:bg-teal-600 transition-colors"
                >
                  Browse jobs →
                </button>
              </>
            )}
          </div>
        )}

        {/* Progress bar */}
        {counts.approved + counts.in_progress + counts.applied + counts.skipped > 0 && (
          <div className="mb-6">
            <div className="flex justify-between text-xs text-slate-500 mb-1.5">
              <span>Progress</span>
              <span>{totalDone} / {counts.approved + counts.in_progress + totalDone} done</span>
            </div>
            <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-teal-400 to-emerald-500 rounded-full transition-all" style={{ width: `${progressPct}%` }} />
            </div>
          </div>
        )}

        {/* Queue list */}
        {queue.length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-3.5 border-b border-slate-200">
              <h3 className="text-sm font-semibold text-slate-900">All jobs in queue ({queue.length})</h3>
            </div>
            <div className="divide-y divide-slate-100">
              {queue.map(item => (
                <div
                  key={item.id}
                  className={`px-5 py-3.5 flex items-center justify-between hover:bg-slate-50 transition-colors ${current?.id === item.id ? 'bg-teal-50/50' : ''}`}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-medium text-slate-900 truncate">{item.job?.title}</h4>
                      <StatusBadge status={item.status} />
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">{item.job?.company} · {item.job?.location || 'Remote'}</p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {item.ats_score != null && item.ats_score > 0 && (
                      <span className="text-xs font-semibold text-teal-600 bg-teal-50 px-2 py-1 rounded">ATS {Math.round(item.ats_score)}</span>
                    )}
                    {item.status === 'approved' && (
                      <button
                        onClick={() => setCurrent(item)}
                        className="text-xs px-3 py-1.5 rounded-md bg-navy-900 text-white hover:bg-navy-800 transition-colors"
                      >
                        Focus
                      </button>
                    )}
                    <button
                      onClick={() => removeFromQueue(item.id)}
                      className="text-xs text-slate-400 hover:text-red-600 transition-colors p-1"
                      aria-label="Remove from queue"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    approved: 'bg-teal-50 text-teal-700',
    in_progress: 'bg-amber-50 text-amber-700',
    applied: 'bg-emerald-50 text-emerald-700',
    skipped: 'bg-slate-100 text-slate-500',
  };
  const labels: Record<string, string> = {
    approved: 'Approved',
    in_progress: 'In Progress',
    applied: 'Applied',
    skipped: 'Skipped',
  };
  return <span className={`text-xs font-medium px-2 py-0.5 rounded ${styles[status] || styles.approved}`}>{labels[status] || status}</span>;
}