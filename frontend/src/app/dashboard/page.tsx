'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
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
  cache?: {
    is_expired: boolean;
    expires_at: string;
  };
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
  const { user, loading: authLoading, logout } = useAuth();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState<number | null>(null);
  const [showApplicationModal, setShowApplicationModal] = useState(false);
  const [currentApplication, setCurrentApplication] = useState<ApplicationPackage | null>(null);
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

  async function handleApply(job: Job) {
    setApplying(job.id);
    
    try {
      // Start application
      const res = await fetch('/api/v1/applications/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: job.id })
      });

      if (!res.ok) {
        const error = await res.json();
        if (error.detail?.includes('No CV found')) {
          toast.error('Please create a CV first');
          router.push('/cv-builder');
          return;
        }
        throw new Error(error.detail || 'Failed to start application');
      }

      const appPackage: ApplicationPackage = await res.json();
      
      // Download CV
      const cvRes = await fetch(appPackage.cv_download_url);
      if (cvRes.ok) {
        const blob = await cvRes.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `CV_${user?.email.split('@')[0]}.pdf`;
        link.click();
        window.URL.revokeObjectURL(url);
      }

      // Open job URL in new tab
      window.open(appPackage.job_url, '_blank');

      // Show application modal
      setCurrentApplication(appPackage);
      setShowApplicationModal(true);
      toast.success('Application started! Good luck! 🍀');

    } catch (err: any) {
      console.error('Application error:', err);
      toast.error(err.message || 'Failed to start application');
    } finally {
      setApplying(null);
    }
  }

  async function markAsSubmitted(applicationId: number) {
    try {
      const res = await fetch(`/api/v1/applications/${applicationId}/submit`, {
        method: 'POST'
      });

      if (res.ok) {
        toast.success("Application submitted! We'll track it for you.");
        setShowApplicationModal(false);
        loadDashboard(); // Refresh stats
      } else {
        throw new Error('Failed to update application');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to update application');
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

  if (!onboardingStatus?.onboarding_complete) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900">Dashboard</h1>
            <div className="flex items-center space-x-2 sm:space-x-4">
              <span className="hidden sm:block text-sm text-slate-600 truncate max-w-[150px]">{user?.email}</span>
              <button
                onClick={() => router.push('/cv-builder')}
                className="hidden sm:block px-4 py-2 text-sm text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
              >
                My CVs
              </button>
              <button
                onClick={logout}
                className="px-3 sm:px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 rounded-lg transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
                aria-label="Logout"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <div className="bg-white rounded-xl shadow-sm p-5 sm:p-6">
            <div className="text-sm text-slate-600 mb-1">Total Jobs</div>
            <div className="text-3xl font-bold text-slate-900">{jobs.length}</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-5 sm:p-6">
            <div className="text-sm text-slate-600 mb-1">Applications</div>
            <div className="text-3xl font-bold text-slate-900">0</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-5 sm:p-6">
            <div className="text-sm text-slate-600 mb-1">Cache Status</div>
            <div className="text-base sm:text-lg font-semibold text-slate-900">
              {onboardingStatus?.cache?.is_expired ? (
                <span className="flex items-center space-x-2">
                  <span>⚠️</span><span>Expired</span>
                </span>
              ) : (
                <span className="flex items-center space-x-2">
                  <span>✅</span><span>Fresh</span>
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Jobs List */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="p-4 sm:p-6 border-b border-slate-200 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-slate-900">Your Jobs</h2>
            <button
              onClick={loadDashboard}
              className="p-2 text-teal-600 hover:bg-teal-50 rounded-lg transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
              aria-label="Refresh"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
          
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}

          {jobs.length === 0 ? (
            <div className="p-8 text-center text-slate-600">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <p className="text-base font-medium mb-4">No jobs found</p>
              <button
                onClick={loadDashboard}
                className="w-full sm:w-auto px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors font-medium min-h-[48px]"
              >
                Refresh Search
              </button>
            </div>
          ) : (
            <div className="divide-y divide-slate-200">
              {jobs.map((job) => (
                <div key={job.id} className="p-4 sm:p-6 hover:bg-slate-50 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start space-y-3 sm:space-y-0">
                    <div className="flex-1">
                      <h3 className="text-base sm:text-lg font-semibold text-slate-900 mb-1">{job.title}</h3>
                      <p className="text-slate-600 text-sm sm:text-base mb-3">{job.company}</p>
                      <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm text-slate-500">
                        <span className="flex items-center space-x-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          <span>{job.location}</span>
                        </span>
                        {job.remote && (
                          <span className="flex items-center space-x-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                            </svg>
                            <span>Remote</span>
                          </span>
                        )}
                        {job.max_salary && (
                          <span className="flex items-center space-x-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span>£{job.max_salary.toLocaleString()}</span>
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => handleApply(job)}
                      disabled={applying === job.id}
                      className="w-full sm:w-auto px-6 py-2.5 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors text-sm font-semibold min-h-[44px] flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {applying === job.id ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Starting...</span>
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          <span>Apply Now</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Application Modal */}
      {showApplicationModal && currentApplication && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-200">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-slate-900">Application Started!</h3>
                <button
                  onClick={() => setShowApplicationModal(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              {/* Job Info */}
              <div className="bg-slate-50 rounded-xl p-4">
                <h4 className="font-semibold text-slate-900 mb-1">{currentApplication.job_title}</h4>
                <p className="text-sm text-slate-600">{currentApplication.company}</p>
              </div>

              {/* What Happened */}
              <div>
                <h4 className="font-semibold text-slate-900 mb-2">✅ What We Did:</h4>
                <ul className="space-y-2 text-sm text-slate-600">
                  <li className="flex items-start space-x-2">
                    <span className="text-green-500 mt-1">✓</span>
                    <span>Downloaded your tailored CV</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-green-500 mt-1">✓</span>
                    <span>Opened the application page in a new tab</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-green-500 mt-1">✓</span>
                    <span>Created application tracker entry</span>
                  </li>
                </ul>
              </div>

              {/* Next Steps */}
              <div>
                <h4 className="font-semibold text-slate-900 mb-2">📋 Next Steps:</h4>
                <ol className="space-y-2 text-sm text-slate-600">
                  <li className="flex items-start space-x-2">
                    <span className="font-semibold">1.</span>
                    <span>Complete the application in the other tab</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="font-semibold">2.</span>
                    <span>Upload your CV when prompted</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="font-semibold">3.</span>
                    <span>Click "I've Submitted" below when done</span>
                  </li>
                </ol>
              </div>

              {/* Application Tips */}
              {currentApplication.application_tips.length > 0 && (
                <div>
                  <h4 className="font-semibold text-slate-900 mb-2">💡 Tips:</h4>
                  <ul className="space-y-1 text-sm text-slate-600">
                    {currentApplication.application_tips.slice(0, 4).map((tip, i) => (
                      <li key={i} className="flex items-start space-x-2">
                        <span className="text-teal-500 mt-1">•</span>
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="p-6 border-t border-slate-200 flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => setShowApplicationModal(false)}
                className="flex-1 px-4 py-3 text-slate-700 font-medium hover:bg-slate-100 rounded-lg transition-colors"
              >
                I'll Submit Later
              </button>
              <button
                onClick={() => markAsSubmitted(currentApplication.application_id)}
                className="flex-1 px-4 py-3 bg-navy-900 text-white font-semibold rounded-lg hover:bg-navy-800 transition-colors"
              >
                I've Submitted!
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
