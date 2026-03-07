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
  { id: 'wishlist', name: 'Wishlist', color: 'bg-slate-200' },
  { id: 'applied', name: 'Applied', color: 'bg-blue-200' },
  { id: 'phone_screen', name: 'Phone Screen', color: 'bg-yellow-200' },
  { id: 'technical', name: 'Technical', color: 'bg-orange-200' },
  { id: 'onsite', name: 'Onsite', color: 'bg-purple-200' },
  { id: 'offer', name: 'Offer', color: 'bg-green-200' },
  { id: 'rejected', name: 'Rejected', color: 'bg-red-200' },
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
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-full mx-auto">
        <h1 className="text-3xl font-bold text-slate-900 mb-8">Application Tracker</h1>
        
        <div className="flex space-x-4 overflow-x-auto pb-4">
          {STAGES.map((stage) => {
            const stageApps = applications.filter(app => app.status === stage.id);
            
            return (
              <div
                key={stage.id}
                className="flex-shrink-0 w-80 bg-slate-100 rounded-xl p-4"
              >
                <div className={`flex items-center justify-between mb-4 ${stage.color} rounded-lg p-3`}>
                  <h2 className="font-semibold text-slate-900">{stage.name}</h2>
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
                      <h3 className="font-semibold text-slate-900">{app.job.title}</h3>
                      <p className="text-sm text-slate-600">{app.job.company}</p>
                      <p className="text-xs text-slate-500 mt-2">📍 {app.job.location}</p>
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
    </div>
  );
}
