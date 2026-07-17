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

interface CoverageStats {
  monitored_career_pages: number;
  coverage_pct?: number;
}

interface ApplyQuota {
  remaining_today: number;
  daily_limit: number;
  daily_used: number;
  allowed: boolean;
}

interface ApplyRunSummary {
  id: number;
  status: string;
  ats_type?: string;
  started_at?: string | null;
  finished_at?: string | null;
  error?: string | null;
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
  const [coverage, setCoverage] = useState<CoverageStats | null>(null);
  const [applyQuota, setApplyQuota] = useState<ApplyQuota | null>(null);
  const [lastApplyRun, setLastApplyRun] = useState<ApplyRunSummary | null>(null);
  const [queueHeadless, setQueueHeadless] = useState(false);
  const [genuineSubmit, setGenuineSubmit] = useState(false);
  const [monitorAutoQueue, setMonitorAutoQueue] = useState(false);
  const [boardConnect, setBoardConnect] = useState<{
    linkedin?: { connected: boolean; connect_url?: string };
    indeed?: { connected: boolean; connect_url?: string };
    extension_required?: boolean;
    message?: string;
  } | null>(null);
  const [connectingBoard, setConnectingBoard] = useState<string | null>(null);
  const [applyBatchId, setApplyBatchId] = useState<string | null>(null);
  const [applyBatchStatus, setApplyBatchStatus] = useState<{
    total?: number;
    by_status?: Record<string, number>;
    runs?: Array<{ status?: string; error?: string; meta?: any }>;
  } | null>(null);
  const [reconnectNeeded, setReconnectNeeded] = useState<{
    boards: Array<'linkedin' | 'indeed'>;
    hint?: string;
  } | null>(null);
  const [retrying, setRetrying] = useState(false);

  function resolveBoardKey(raw: unknown): 'linkedin' | 'indeed' | null {
    if (raw === 'linkedin' || raw === 'indeed') return raw;
    if (raw && typeof raw === 'object') {
      const b = (raw as { board?: string; ats?: string }).board
        || (raw as { board?: string; ats?: string }).ats;
      if (b === 'linkedin' || b === 'indeed') return b;
    }
    return null;
  }

  async function retryNeedsUserApplies() {
    setRetrying(true);
    try {
      const res = await authFetch('/api/v1/apply-engine/headless/retry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          statuses: ['needs_user', 'failed', 'stale'],
          auto_submit: genuineSubmit,
          limit: 20,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        toast.error(
          typeof err.detail === 'string'
            ? err.detail
            : err.detail?.reason || 'Retry queue failed'
        );
        return;
      }
      const data = await res.json();
      toast.success(
        data.queued
          ? `Re-queued ${data.queued} apply${data.queued === 1 ? '' : 's'}`
          : data.message || 'Nothing to retry'
      );
      if (data.queued) {
        setReconnectNeeded(null);
        await loadAutomationMetrics();
      }
    } catch {
      toast.error('Retry request failed');
    } finally {
      setRetrying(false);
    }
  }

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

  async function loadConnectStatus() {
    try {
      const res = await authFetch('/api/v1/apply-engine/connect/status');
      if (res.ok) {
        const data = await res.json();
        setBoardConnect({
          linkedin: data.boards?.linkedin,
          indeed: data.boards?.indeed,
          extension_required: data.extension_required,
          message: data.message,
        });
      }
    } catch {
      /* non-blocking */
    }
  }

  async function connectBoard(board: 'linkedin' | 'indeed') {
    setConnectingBoard(board);
    setError('');
    try {
      // Prefer extension bridge (real cookie sync)
      const ext = (window as any).JobScaleExtension;
      const extInstalled = !!(ext && (ext.installed === true || typeof ext.connectBoard === 'function'));
      if (!extInstalled) {
        toast.error(
          boardConnect?.message
            || 'Install the JobScale Chrome extension, then click Connect again. Options → set API URL if needed.'
        );
      }
      if (ext && typeof ext.connectBoard === 'function') {
        const result = await ext.connectBoard(board);
        if (result?.ok) {
          toast.success(`${board === 'linkedin' ? 'LinkedIn' : 'Indeed'} connected for Easy Apply`);
          setReconnectNeeded(null);
          await loadConnectStatus();
          return;
        }
        // Fall through to open board + poll if extension returned error
        if (result?.error && !String(result.error).includes('timeout')) {
          toast.error(result.error);
        }
      } else {
        // Dispatch for content-script bridge if present without JobScaleExtension
        window.dispatchEvent(new CustomEvent('jobscale-connect-board', { detail: { board } }));
      }
      const url =
        boardConnect?.[board]?.connect_url
        || (board === 'linkedin' ? 'https://www.linkedin.com/feed/' : 'https://www.indeed.com/');
      window.open(url, '_blank', 'noopener,noreferrer');
      toast.success(`Log into ${board === 'linkedin' ? 'LinkedIn' : 'Indeed'} in the new tab — JobScale extension will sync your session`);
      // Poll for up to ~40s
      let connected = false;
      for (let i = 0; i < 10; i++) {
        await new Promise((r) => setTimeout(r, 4000));
        await loadConnectStatus();
        connected = !!(await authFetch('/api/v1/apply-engine/connect/status').then((r) => r.json()).catch(() => null))
          ?.boards?.[board]?.connected;
        if (connected) {
          toast.success(`${board === 'linkedin' ? 'LinkedIn' : 'Indeed'} connected`);
          setReconnectNeeded(null);
          break;
        }
      }
      if (!connected) {
        toast.error(
          extInstalled
            ? `${board === 'linkedin' ? 'LinkedIn' : 'Indeed'} did not connect in time — log in on the board tab, then click Connect again.`
            : 'Extension required to sync your board session. Install JobScale extension, then retry Connect.'
        );
      }
      await loadConnectStatus();
    } finally {
      setConnectingBoard(null);
    }
  }

  async function disconnectBoard(board: 'linkedin' | 'indeed') {
    const res = await authFetch(`/api/v1/apply-engine/board-sessions/${board}`, { method: 'DELETE' });
    if (res.ok) {
      toast.success(`${board === 'linkedin' ? 'LinkedIn' : 'Indeed'} disconnected`);
      await loadConnectStatus();
    }
  }

  async function loadAutomationMetrics() {
    try {
      const [covRes, quotaRes, runsRes, settingsRes] = await Promise.all([
        authFetch('/api/v1/companies/coverage'),
        authFetch('/api/v1/apply-engine/quota'),
        authFetch('/api/v1/apply-engine/runs?limit=5'),
        authFetch('/api/v1/apply-engine/settings'),
        loadConnectStatus(),
      ]);
      if (settingsRes.ok) {
        const st = await settingsRes.json();
        setGenuineSubmit(!!st.auto_apply_submit);
        setMonitorAutoQueue(!!st.monitor_auto_queue);
        if (st.auto_apply_submit) setQueueHeadless(true);
      }
      if (covRes.ok) {
        const cov = await covRes.json();
        setCoverage({
          monitored_career_pages: cov.monitored_career_pages ?? 0,
          coverage_pct: cov.coverage_pct,
        });
      }
      if (quotaRes.ok) {
        const q = await quotaRes.json();
        setApplyQuota({
          remaining_today: q.remaining_today ?? 0,
          daily_limit: q.daily_limit ?? 0,
          daily_used: q.daily_used ?? 0,
          allowed: q.allowed !== false,
        });
      }
      if (runsRes.ok) {
        const runsData = await runsRes.json();
        const runs = runsData.runs || [];
        setLastApplyRun(runs[0] || null);
      }
    } catch {
      /* non-blocking */
    }
  }

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
        // Always re-search — do not gate on has_cached_jobs (empty dashboard bug)
        const searchRes = await authFetch('/api/v1/onboarding/search', { method: 'POST' });
        if (searchRes.ok) {
          const searchData = await searchRes.json();
          setJobs(searchData.jobs || []);
        } else {
          setError('Could not load matched jobs — try Refresh');
          toast.error('Failed to load matched jobs');
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
      await loadAutomationMetrics();
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
        if (typeof err.detail === 'string' && err.detail.includes('No CV found')) {
          toast.error('Please create a CV first');
          router.push('/cv-builder');
          return;
        }
        throw new Error(
          typeof err.detail === 'string' ? err.detail : 'Failed to start applications'
        );
      }
      const data = await res.json();
      const applications = data.applications || [];
      setBatchResults(applications);

      if (queueHeadless) {
        const applicationIds = applications
          .map((a: { application_id?: number }) => a.application_id)
          .filter((id: number | undefined): id is number => typeof id === 'number');
        if (applicationIds.length > 0) {
          try {
            // Persist opt-in before genuine submit queue
            if (genuineSubmit) {
              await authFetch('/api/v1/apply-engine/settings', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ auto_apply_submit: true }),
              });
            }
            const hlRes = await authFetch('/api/v1/apply-engine/headless/batch', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                application_ids: applicationIds,
                dry_run: false,
                auto_submit: genuineSubmit,
              }),
            });
            if (!hlRes.ok) {
              const hlErr = await hlRes.json().catch(() => ({}));
              const detail =
                typeof hlErr.detail === 'string'
                  ? hlErr.detail
                  : hlErr.detail?.reason || 'Headless queue failed';
              toast.error(`Applications started, but headless queue failed: ${detail}`);
            } else {
              const hlData = await hlRes.json().catch(() => ({}));
              const batchId = hlData.batch_id as string | undefined;
              if (hlData.session_warnings?.length || hlData.needs_reconnect) {
                const boards = (hlData.session_warnings || [])
                  .map((w: { board?: string }) => resolveBoardKey(w.board))
                  .filter(Boolean) as Array<'linkedin' | 'indeed'>;
                setReconnectNeeded({
                  boards: boards.length ? boards : ['linkedin', 'indeed'],
                  hint:
                    hlData.session_warnings?.[0]?.connect_hint ||
                    hlData.message ||
                    'Connect LinkedIn/Indeed before Easy Apply on those boards.',
                });
              }
              if (batchId) {
                setApplyBatchId(batchId);
                setApplyBatchStatus({ total: applicationIds.length, by_status: { queued: applicationIds.length } });
                // Poll real ApplyRun outcomes (not mock)
                let finalStatus: any = null;
                for (let i = 0; i < 24; i++) {
                  await new Promise((r) => setTimeout(r, 2500));
                  const stRes = await authFetch(`/api/v1/apply-engine/headless/batch/${batchId}`);
                  if (!stRes.ok) continue;
                  const st = await stRes.json();
                  finalStatus = st;
                  setApplyBatchStatus(st);
                  const by = st.by_status || {};
                  const runs = st.runs || [];
                  const needsReconnect =
                    (st.needs_reconnect || 0) > 0
                      ? runs.filter(
                          (r: any) =>
                            r?.meta?.blocked_reason === 'login_required' ||
                            r?.meta?.connect_hint ||
                            r?.meta?.session_invalidated ||
                            (r?.status === 'needs_user' &&
                              String(r?.error || '').toLowerCase().includes('login'))
                        )
                      : runs.filter(
                          (r: any) =>
                            r?.meta?.blocked_reason === 'login_required' ||
                            r?.meta?.connect_hint ||
                            r?.meta?.session_invalidated
                        );
                  if (needsReconnect.length > 0 || (st.needs_reconnect || 0) > 0) {
                    const boards = Array.from(
                      new Set(
                        needsReconnect
                          .map(
                            (r: any) =>
                              resolveBoardKey(r?.meta?.board_key) ||
                              resolveBoardKey(r?.meta?.board) ||
                              (r?.ats_type === 'indeed' || r?.ats_type === 'linkedin'
                                ? r.ats_type
                                : null)
                          )
                          .filter(Boolean)
                      )
                    ) as Array<'linkedin' | 'indeed'>;
                    setReconnectNeeded({
                      boards: boards.length ? boards : ['linkedin', 'indeed'],
                      hint:
                        needsReconnect[0]?.meta?.connect_hint ||
                        'Session expired or missing — reconnect LinkedIn/Indeed to continue Easy Apply.',
                    });
                    try {
                      document.getElementById('board-connections')?.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center',
                      });
                    } catch {
                      /* ignore */
                    }
                    await loadConnectStatus();
                  }
                  const done =
                    (by.submitted || 0) +
                    (by.filled || 0) +
                    (by.needs_user || 0) +
                    (by.failed || 0) +
                    (by.stale || 0) +
                    (by.skipped || 0) +
                    (by.deferred || 0);
                  const total = st.total || applicationIds.length;
                  if (done >= total && total > 0) break;
                }
                const by = finalStatus?.by_status || {};
                const needsUser = by.needs_user || 0;
                const submitted = by.submitted || 0;
                const failed = (by.failed || 0) + (by.stale || 0);
                if (needsUser > 0 || failed > 0) {
                  toast.error(
                    `Apply finished: ${submitted} submitted, ${needsUser} need you, ${failed} failed` +
                      (needsUser ? ' — reconnect or retry below' : '')
                  );
                } else {
                  toast.success(
                    genuineSubmit
                      ? `${submitted || data.total} genuine auto-apply completed`
                      : `${data.total} applications started — headless fill queued (${applicationIds.length})`
                  );
                }
              } else {
                toast.success(
                  genuineSubmit
                    ? `${data.total} queued for genuine auto-apply (fill + submit)`
                    : `${data.total} applications started — headless fill queued (${applicationIds.length})`
                );
              }
            }
          } catch {
            toast.error('Applications started, but headless queue request failed');
          }
        } else {
          toast.success(`${data.total} applications started!`);
        }
      } else {
        toast.success(`${data.total} applications started!`);
      }

      setShowModal(true);
      setSelectedJobs(new Set());
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
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
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

        {/* Automation strip */}
        <div className="mb-8 px-4 py-3 border border-slate-200 rounded-lg bg-white flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <p className="text-xs font-semibold text-slate-900 uppercase tracking-wide">Automation</p>
            <p className="text-xs text-slate-500 mt-0.5">
              Connect LinkedIn/Indeed, then queue genuine headless Easy Apply
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-sm text-slate-600">
            <span>
              <span className="text-slate-400 text-xs uppercase tracking-wide mr-1.5">Monitored</span>
              <span className="font-medium text-slate-900 tabular-nums">
                {coverage?.monitored_career_pages ?? '—'}
              </span>
            </span>
            <span>
              <span className="text-slate-400 text-xs uppercase tracking-wide mr-1.5">Quota left</span>
              <span className="font-medium text-slate-900 tabular-nums">
                {applyQuota != null ? applyQuota.remaining_today : '—'}
                {applyQuota != null ? (
                  <span className="text-slate-400 font-normal">/{applyQuota.daily_limit}</span>
                ) : null}
              </span>
            </span>
            <span>
              <span className="text-slate-400 text-xs uppercase tracking-wide mr-1.5">Last run</span>
              <span className="font-medium text-slate-900">
                {lastApplyRun?.status ?? 'none'}
              </span>
            </span>
          </div>
        </div>

        {applyBatchId && applyBatchStatus && (
          <div className="mb-6 px-4 py-3 border border-slate-200 rounded-lg bg-white">
            <p className="text-xs font-semibold text-slate-900 uppercase tracking-wide">Apply progress</p>
            <p className="text-xs text-slate-500 mt-0.5">Batch {applyBatchId.slice(0, 8)}…</p>
            <div className="flex flex-wrap gap-3 mt-2 text-sm text-slate-700">
              {Object.entries(applyBatchStatus.by_status || {}).map(([k, v]) => (
                <span key={k}>
                  <span className="text-slate-400 text-xs uppercase mr-1">{k}</span>
                  <span className="font-medium tabular-nums">{v as number}</span>
                </span>
              ))}
            </div>
            {(applyBatchStatus.runs || []).some(
              (r) => r.status === 'needs_user' || (r.meta && (r.meta.blocked_reason === 'login_required' || r.meta.connect_hint))
            ) && (
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <p className="text-xs text-amber-700">
                  Some applies need you — Connect LinkedIn/Indeed below, or complete CAPTCHA/profile gaps.
                </p>
                <button
                  type="button"
                  disabled={retrying}
                  onClick={() => retryNeedsUserApplies()}
                  className="px-2.5 py-1 text-xs font-semibold rounded-md border border-amber-300 text-amber-900 hover:bg-amber-50 disabled:opacity-50"
                >
                  {retrying ? 'Retrying…' : 'Retry needs-you'}
                </button>
              </div>
            )}
          </div>
        )}

        {reconnectNeeded && (
          <div className="mb-6 px-4 py-3 border border-amber-300 rounded-lg bg-amber-50">
            <p className="text-xs font-semibold text-amber-900 uppercase tracking-wide">Reconnect required</p>
            <p className="text-sm text-amber-900 mt-1">{reconnectNeeded.hint}</p>
            <div className="flex flex-wrap gap-2 mt-3">
              {reconnectNeeded.boards.map((board) => (
                <button
                  key={board}
                  type="button"
                  disabled={connectingBoard === board}
                  onClick={() => connectBoard(board)}
                  className="px-3 py-1.5 text-xs font-semibold rounded-md bg-navy-900 text-white hover:bg-navy-800 disabled:opacity-50"
                >
                  {connectingBoard === board
                    ? 'Connecting…'
                    : `Reconnect ${board === 'linkedin' ? 'LinkedIn' : 'Indeed'}`}
                </button>
              ))}
              <button
                type="button"
                disabled={retrying}
                onClick={() => retryNeedsUserApplies()}
                className="px-3 py-1.5 text-xs font-semibold rounded-md border border-amber-400 text-amber-900 hover:bg-amber-100 disabled:opacity-50"
              >
                {retrying ? 'Retrying…' : 'Retry after reconnect'}
              </button>
              <button
                type="button"
                onClick={() => setReconnectNeeded(null)}
                className="px-3 py-1.5 text-xs text-amber-800 hover:text-amber-950"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Connect LinkedIn / Indeed */}
        <div
          id="board-connections"
          className={`mb-8 px-4 py-4 border rounded-lg bg-white ${
            reconnectNeeded ? 'border-amber-300 ring-2 ring-amber-100' : 'border-slate-200'
          }`}
        >
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-3">
            <div>
              <p className="text-xs font-semibold text-slate-900 uppercase tracking-wide">Board connections</p>
              <p className="text-xs text-slate-500 mt-0.5 max-w-xl">
                Install the JobScale Chrome extension, click Connect, log in — we sync your session so Easy Apply can run for you.
              </p>
            </div>
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            {(['linkedin', 'indeed'] as const).map((board) => {
              const info = boardConnect?.[board];
              const connected = !!info?.connected;
              const label = board === 'linkedin' ? 'LinkedIn' : 'Indeed';
              return (
                <div
                  key={board}
                  className="flex items-center justify-between gap-3 rounded-md border border-slate-100 bg-slate-50/50 px-3 py-3"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-900">{label}</p>
                    <p className={`text-xs mt-0.5 ${connected ? 'text-teal-700' : 'text-slate-500'}`}>
                      {connected ? 'Connected · Easy Apply ready' : 'Not connected'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {connected && (
                      <button
                        type="button"
                        onClick={() => disconnectBoard(board)}
                        className="text-xs text-slate-500 hover:text-slate-800 px-2 py-1"
                      >
                        Disconnect
                      </button>
                    )}
                    <button
                      type="button"
                      disabled={connectingBoard === board}
                      onClick={() => connectBoard(board)}
                      className="px-3 py-1.5 text-xs font-semibold rounded-md bg-navy-900 text-white hover:bg-navy-800 disabled:opacity-50"
                    >
                      {connectingBoard === board ? 'Connecting…' : connected ? 'Reconnect' : 'Connect'}
                    </button>
                  </div>
                </div>
              );
            })}
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
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <p className="text-sm text-slate-600">
              <span className="font-semibold text-navy-900">{selectedJobs.size}</span> job{selectedJobs.size !== 1 ? 's' : ''} selected
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={queueHeadless}
                  onChange={(e) => setQueueHeadless(e.target.checked)}
                  className="w-4 h-4 text-teal-500 border-slate-300 rounded focus:ring-teal-500 cursor-pointer"
                />
                <span>Queue headless apply (server-side)</span>
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={genuineSubmit}
                  onChange={async (e) => {
                    const on = e.target.checked;
                    setGenuineSubmit(on);
                    if (on) setQueueHeadless(true);
                    try {
                      await authFetch('/api/v1/apply-engine/settings', {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ auto_apply_submit: on }),
                      });
                    } catch {
                      /* non-blocking */
                    }
                  }}
                  className="w-4 h-4 text-teal-500 border-slate-300 rounded focus:ring-teal-500 cursor-pointer"
                />
                <span>Genuinely submit for me</span>
                <span className="text-xs text-slate-400 font-normal">(fills + submits when confirmed)</span>
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={monitorAutoQueue}
                  onChange={async (e) => {
                    const on = e.target.checked;
                    setMonitorAutoQueue(on);
                    try {
                      await authFetch('/api/v1/apply-engine/settings', {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ monitor_auto_queue: on }),
                      });
                    } catch {
                      /* non-blocking */
                    }
                  }}
                  className="w-4 h-4 text-teal-500 border-slate-300 rounded focus:ring-teal-500 cursor-pointer"
                />
                <span>Auto-queue high-match monitored jobs</span>
              </label>
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
              <p className="text-sm text-slate-600 mb-4">
                {genuineSubmit
                  ? 'JobScale queues genuine headless apply (fill + submit when opted in). Status updates above as runs finish.'
                  : 'Headless fill is queued without submit unless “Genuine submit” is checked. Manual links below are optional.'}
              </p>
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
