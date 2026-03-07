'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';

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

const STAGES = [
  { id: 'wishlist', name: 'Wishlist', color: 'bg-slate-200', icon: '📋' },
  { id: 'applied', name: 'Applied', color: 'bg-blue-200', icon: '✉️' },
  { id: 'phone_screen', name: 'Phone', color: 'bg-yellow-200', icon: '📞' },
  { id: 'technical', name: 'Technical', color: 'bg-orange-200', icon: '💻' },
  { id: 'onsite', name: 'Onsite', color: 'bg-purple-200', icon: '🏢' },
  { id: 'offer', name: 'Offer', color: 'bg-green-200', icon: '🎉' },
  { id: 'rejected', name: 'Rejected', color: 'bg-red-200', icon: '❌' },
];

export default function KanbanPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
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
      const response = await fetch('/api/v1/applications');
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
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-4"></div>
          <p className="text-slate-600 text-sm">Loading applications...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-40">
        <div className="max-w-full mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-slate-900">Application Tracker</h1>
              <p className="text-xs sm:text-sm text-slate-600 mt-1 hidden sm:block">Track your job applications through every stage</p>
            </div>
            <button
              onClick={() => router.push('/dashboard')}
              className="px-3 sm:px-4 py-2 text-sm font-semibold text-teal-600 hover:bg-teal-50 rounded-lg transition-colors min-h-[44px] flex items-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              <span className="hidden sm:inline">Add Application</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content - Horizontal scroll on mobile */}
      <main className="p-4 sm:p-6 md:p-8">
        {/* Mobile: Stage selector tabs */}
        <div className="md:hidden mb-4 overflow-x-auto pb-2">
          <div className="flex space-x-2 min-w-max">
            {STAGES.map((stage) => {
              const stageApps = applications.filter(app => app.status === stage.id);
              return (
                <button
                  key={stage.id}
                  className={`flex-shrink-0 px-3 py-2 rounded-lg text-xs font-medium flex items-center space-x-2 ${stage.color} bg-opacity-50`}
                >
                  <span>{stage.icon}</span>
                  <span>{stage.name}</span>
                  <span className="bg-white px-2 py-0.5 rounded text-xs font-bold">{stageApps.length}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Desktop/Tablet: Full Kanban board */}
        <div className="hidden md:block">
          <div className="flex space-x-4 overflow-x-auto pb-4">
            {STAGES.map((stage) => {
              const stageApps = applications.filter(app => app.status === stage.id);
              
              return (
                <div
                  key={stage.id}
                  className="flex-shrink-0 w-80 bg-slate-100 rounded-xl p-4"
                >
                  <div className={`flex items-center justify-between mb-4 ${stage.color} rounded-lg p-3`}>
                    <h2 className="font-semibold text-slate-900 flex items-center space-x-2">
                      <span>{stage.icon}</span>
                      <span>{stage.name}</span>
                    </h2>
                    <span className="bg-white px-2 py-1 rounded text-sm font-medium">
                      {stageApps.length}
                    </span>
                  </div>
                  
                  <div className="space-y-3">
                    {stageApps.map((app) => (
                      <div
                        key={app.id}
                        className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                      >
                        <h3 className="font-semibold text-slate-900 text-sm">{app.job.title}</h3>
                        <p className="text-sm text-slate-600 mt-1">{app.job.company}</p>
                        <p className="text-xs text-slate-500 mt-2 flex items-center space-x-1">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
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
                              Browse Jobs →
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
            const stageApps = applications.filter(app => app.status === stage.id);
            
            if (stageApps.length === 0) return null;
            
            return (
              <div key={stage.id} className="bg-white rounded-xl shadow-sm overflow-hidden">
                <div className={`${stage.color} px-4 py-3 flex items-center justify-between`}>
                  <h2 className="font-semibold text-slate-900 flex items-center space-x-2">
                    <span>{stage.icon}</span>
                    <span>{stage.name}</span>
                  </h2>
                  <span className="bg-white px-3 py-1 rounded-full text-sm font-bold shadow-sm">
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
                      <p className="text-sm text-slate-600 mt-1">{app.job.company}</p>
                      <div className="mt-2 flex items-center space-x-4 text-xs text-slate-500">
                        <span className="flex items-center space-x-1">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          <span>{app.job.location}</span>
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
          
          {applications.length === 0 && (
            <div className="text-center py-12">
              <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">No applications yet</h3>
              <p className="text-slate-600 mb-6 max-w-sm mx-auto">
                Start tracking your job applications by browsing available positions
              </p>
              <button
                onClick={() => router.push('/dashboard')}
                className="w-full max-w-xs mx-auto px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors font-semibold flex items-center justify-center space-x-2 min-h-[48px]"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <span>Browse Jobs</span>
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
