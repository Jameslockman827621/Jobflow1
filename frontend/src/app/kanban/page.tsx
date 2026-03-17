'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import AppShell from '@/components/AppShell';

interface Application {
  id: number;
  job_id: number;
  status: string;
  job: {
    title: string;
    company: string;
    location: string;
  };
}

function ClipboardIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
    </svg>
  );
}

function EnvelopeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
    </svg>
  );
}

function PhoneIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z" />
    </svg>
  );
}

function CodeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
    </svg>
  );
}

function BuildingIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
    </svg>
  );
}

function TrophyIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M18.75 4.236c.982.143 1.954.317 2.916.52A6.003 6.003 0 0116.27 9.728M18.75 4.236V4.5c0 2.108-.966 3.99-2.48 5.228M15.003 11.078a7.454 7.454 0 00.981-3.172M9.497 14.25c.157-1.14.458-2.206.881-3.172M15.003 11.078c-.423.966-.724 2.032-.881 3.172" />
    </svg>
  );
}

function XCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function LocationIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
    </svg>
  );
}

const STAGES: { id: string; name: string; icon: React.FC<{ className?: string }> }[] = [
  { id: 'wishlist', name: 'Wishlist', icon: ClipboardIcon },
  { id: 'applied', name: 'Applied', icon: EnvelopeIcon },
  { id: 'phone_screen', name: 'Phone', icon: PhoneIcon },
  { id: 'technical', name: 'Technical', icon: CodeIcon },
  { id: 'onsite', name: 'Onsite', icon: BuildingIcon },
  { id: 'offer', name: 'Offer', icon: TrophyIcon },
  { id: 'rejected', name: 'Rejected', icon: XCircleIcon },
];

const STAGE_COLORS: Record<string, string> = {
  wishlist: 'bg-slate-100 text-slate-700',
  applied: 'bg-sky-50 text-sky-700',
  phone_screen: 'bg-amber-50 text-amber-700',
  technical: 'bg-orange-50 text-orange-700',
  onsite: 'bg-violet-50 text-violet-700',
  offer: 'bg-emerald-50 text-emerald-700',
  rejected: 'bg-red-50 text-red-700',
};

export default function KanbanPage() {
  const router = useRouter();
  const { user, loading: authLoading, authFetch } = useAuth();
  const [loading, setLoading] = useState(true);
  const [applications, setApplications] = useState<Application[]>([]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      loadApplications();
    }
  }, [user]);

  async function loadApplications() {
    try {
      setLoading(true);
      const response = await authFetch('/api/v1/applications');
      if (response.ok) {
        const data = await response.json();
        setApplications(data);
      }
    } catch (err) {
      console.error('Failed to load applications:', err);
    } finally {
      setLoading(false);
    }
  }

  if (authLoading || loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center py-32">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-slate-200 border-t-teal-500 mx-auto mb-3"></div>
            <p className="text-slate-500 text-sm">Loading applications...</p>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Application Tracker</h1>
            <p className="text-sm text-slate-500 mt-1">Track your job applications through every stage</p>
          </div>
          <button
            onClick={() => router.push('/dashboard')}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-teal-500 text-white hover:bg-teal-600 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            <span className="hidden sm:inline">Add Application</span>
          </button>
        </div>
      </div>

      {/* Mobile: Stage tabs */}
      <div className="md:hidden mb-4 overflow-x-auto pb-2">
        <div className="flex gap-2 min-w-max">
          {STAGES.map((stage) => {
            const StageIcon = stage.icon;
            const stageApps = applications.filter(app => app.status === stage.id);
            return (
              <div
                key={stage.id}
                className={`flex-shrink-0 px-3 py-2 rounded-lg text-xs font-medium flex items-center gap-1.5 ${STAGE_COLORS[stage.id] || 'bg-slate-100 text-slate-700'}`}
              >
                <StageIcon className="w-3.5 h-3.5" />
                <span>{stage.name}</span>
                <span className="bg-white/80 px-1.5 py-0.5 rounded text-xs font-bold">{stageApps.length}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Desktop: Kanban board */}
      <div className="hidden md:block">
        <div className="flex gap-4 overflow-x-auto pb-4">
          {STAGES.map((stage) => {
            const StageIcon = stage.icon;
            const stageApps = applications.filter(app => app.status === stage.id);

            return (
              <div key={stage.id} className="flex-shrink-0 w-72 bg-slate-100 rounded-xl p-3">
                <div className={`flex items-center justify-between mb-3 rounded-lg px-3 py-2.5 ${STAGE_COLORS[stage.id] || 'bg-slate-100 text-slate-700'}`}>
                  <h2 className="font-medium text-sm flex items-center gap-2">
                    <StageIcon className="w-4 h-4" />
                    <span>{stage.name}</span>
                  </h2>
                  <span className="bg-white/80 text-xs font-semibold px-2 py-0.5 rounded">
                    {stageApps.length}
                  </span>
                </div>

                <div className="space-y-2">
                  {stageApps.map((app) => (
                    <div
                      key={app.id}
                      className="bg-white rounded-lg p-3.5 shadow-sm hover:shadow-md transition-shadow cursor-pointer border border-slate-100"
                    >
                      <h3 className="font-semibold text-slate-900 text-sm leading-snug">{app.job.title}</h3>
                      <p className="text-sm text-slate-500 mt-1">{app.job.company}</p>
                      <p className="text-xs text-slate-400 mt-2 flex items-center gap-1">
                        <LocationIcon className="w-3 h-3" />
                        <span>{app.job.location}</span>
                      </p>
                    </div>
                  ))}

                  {stageApps.length === 0 && (
                    <div className="text-center text-slate-400 text-sm py-8">
                      {stage.id === 'wishlist' ? (
                        <div>
                          <p className="mb-2">No applications yet</p>
                          <button
                            onClick={() => router.push('/dashboard')}
                            className="text-teal-600 hover:text-teal-700 font-medium text-xs"
                          >
                            Browse Jobs
                          </button>
                        </div>
                      ) : (
                        <p>No applications</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Mobile: Stacked card view */}
      <div className="md:hidden space-y-4">
        {STAGES.map((stage) => {
          const StageIcon = stage.icon;
          const stageApps = applications.filter(app => app.status === stage.id);

          if (stageApps.length === 0) return null;

          return (
            <div key={stage.id} className="bg-white rounded-xl shadow-sm overflow-hidden border border-slate-100">
              <div className={`px-4 py-3 flex items-center justify-between ${STAGE_COLORS[stage.id] || 'bg-slate-100 text-slate-700'}`}>
                <h2 className="font-medium text-sm flex items-center gap-2">
                  <StageIcon className="w-4 h-4" />
                  <span>{stage.name}</span>
                </h2>
                <span className="bg-white/80 text-xs font-bold px-2.5 py-0.5 rounded-full shadow-sm">
                  {stageApps.length}
                </span>
              </div>

              <div className="divide-y divide-slate-100">
                {stageApps.map((app) => (
                  <div
                    key={app.id}
                    className="p-4 hover:bg-slate-50 transition-colors cursor-pointer"
                  >
                    <h3 className="font-semibold text-slate-900 text-base">{app.job.title}</h3>
                    <p className="text-sm text-slate-500 mt-1">{app.job.company}</p>
                    <div className="mt-2 flex items-center text-xs text-slate-400 gap-1">
                      <LocationIcon className="w-3 h-3" />
                      <span>{app.job.location}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}

        {applications.length === 0 && (
          <div className="text-center py-16">
            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <ClipboardIcon className="w-8 h-8 text-slate-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">No applications yet</h3>
            <p className="text-slate-500 mb-6 max-w-sm mx-auto text-sm">
              Start tracking your job applications by browsing available positions
            </p>
            <button
              onClick={() => router.push('/dashboard')}
              className="inline-flex items-center gap-2 px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors font-medium text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
              <span>Browse Jobs</span>
            </button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
