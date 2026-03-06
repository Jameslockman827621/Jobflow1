'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';

interface Company {
  name: string;
  industry: string;
  size: string;
}

interface Role {
  name: string;
}

interface Preferences {
  target_roles: string[];
  locations: string[];
  remote_only: boolean;
  hybrid_ok: boolean;
  min_salary?: number;
  target_companies: string[];
  seniority_levels: string[];
  required_skills: string[];
  employment_types: string[];
}

export default function OnboardingPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchProgress, setSearchProgress] = useState(0);

  const [preferences, setPreferences] = useState<Preferences>({
    target_roles: [],
    locations: [],
    remote_only: false,
    hybrid_ok: true,
    min_salary: undefined,
    target_companies: [],
    seniority_levels: [],
    required_skills: [],
    employment_types: ['FULL_TIME'],
  });

  const [suggestedCompanies, setSuggestedCompanies] = useState<Company[]>([]);
  const [suggestedRoles, setSuggestedRoles] = useState<Role[]>([]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    fetchSuggestions();
  }, []);

  const fetchSuggestions = async () => {
    try {
      const [companiesRes, rolesRes] = await Promise.all([
        fetch('/api/v1/onboarding/companies/suggested'),
        fetch('/api/v1/onboarding/roles/suggested'),
      ]);

      const companiesData = await companiesRes.json();
      const rolesData = await rolesRes.json();

      setSuggestedCompanies(companiesData.companies || []);
      setSuggestedRoles(rolesData.roles || []);
    } catch (err) {
      console.error('Failed to fetch suggestions:', err);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');

    try {
      // Step 1: Save preferences
      const saveRes = await fetch('/api/v1/onboarding/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preferences),
      });

      if (!saveRes.ok) {
        const errorData = await saveRes.json();
        throw new Error(errorData.detail || 'Failed to save preferences');
      }

      // Step 2: Run job search
      setSearching(true);
      setSearchProgress(0);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setSearchProgress((prev) => Math.min(prev + 10, 90));
      }, 500);

      const searchRes = await fetch('/api/v1/onboarding/search', {
        method: 'POST',
      });

      clearInterval(progressInterval);
      setSearchProgress(100);

      if (!searchRes.ok) {
        const errorData = await searchRes.json();
        throw new Error(errorData.detail || 'Failed to search jobs');
      }

      const searchData = await searchRes.json();

      setTimeout(() => {
        router.push(`/dashboard?onboarding=complete&jobs=${searchData.total}`);
      }, 1000);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
      setSearching(false);
    } finally {
      setLoading(false);
    }
  };

  const toggleRole = (role: string) => {
    setPreferences((prev) => ({
      ...prev,
      target_roles: prev.target_roles.includes(role)
        ? prev.target_roles.filter((r) => r !== role)
        : [...prev.target_roles, role],
    }));
  };

  const toggleCompany = (company: string) => {
    setPreferences((prev) => ({
      ...prev,
      target_companies: prev.target_companies.includes(company)
        ? prev.target_companies.filter((c) => c !== company)
        : [...prev.target_companies, company],
    }));
  };

  const toggleLocation = (location: string) => {
    setPreferences((prev) => ({
      ...prev,
      locations: prev.locations.includes(location)
        ? prev.locations.filter((l) => l !== location)
        : [...prev.locations, location],
    }));
  };

  const toggleSeniority = (level: string) => {
    setPreferences((prev) => ({
      ...prev,
      seniority_levels: prev.seniority_levels.includes(level)
        ? prev.seniority_levels.filter((l) => l !== level)
        : [...prev.seniority_levels, level],
    }));
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        {/* Progress */}
        <div className="mb-8">
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium text-slate-700">Step {step} of 4</span>
            <span className="text-sm font-medium text-slate-700">{Math.round((step / 4) * 100)}%</span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-2">
            <div
              className="bg-teal-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(step / 4) * 100}%` }}
            />
          </div>
        </div>

        {/* Step 1: Roles */}
        {step === 1 && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">What role are you looking for?</</h2>
            <p className="text-slate-600 mb-6">Select all that apply</p>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
              {suggestedRoles.map((role) => (
                <button
                  key={role.name}
                  onClick={() => toggleRole(role.name)}
                  className={`p-4 rounded-xl border-2 transition-all ${
                    preferences.target_roles.includes(role.name)
                      ? 'border-teal-500 bg-teal-50 text-teal-700'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <span className="font-medium">{role.name}</span>
                </button>
              ))}
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setStep(2)}
                disabled={preferences.target_roles.length === 0}
                className="px-6 py-3 bg-navy-900 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-navy-800 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Location */}
        {step === 2 && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Where do you want to work?</h2>
            <p className="text-slate-600 mb-6">Select locations or remote</p>

            <div className="space-y-4 mb-6">
              <div>
                <label className="flex items-center space-x-3 p-4 border-2 rounded-xl cursor-pointer hover:border-slate-300">
                  <input
                    type="checkbox"
                    checked={preferences.locations.includes('London, UK')}
                    onChange={() => toggleLocation('London, UK')}
                    className="w-5 h-5 text-teal-500 rounded"
                  />
                  <span className="font-medium">London, UK</span>
                </label>
              </div>
              <div>
                <label className="flex items-center space-x-3 p-4 border-2 rounded-xl cursor-pointer hover:border-slate-300">
                  <input
                    type="checkbox"
                    checked={preferences.locations.includes('United Kingdom')}
                    onChange={() => toggleLocation('United Kingdom')}
                    className="w-5 h-5 text-teal-500 rounded"
                  />
                  <span className="font-medium">United Kingdom (anywhere)</span>
                </label>
              </div>
              <div>
                <label className="flex items-center space-x-3 p-4 border-2 rounded-xl cursor-pointer hover:border-slate-300">
                  <input
                    type="checkbox"
                    checked={preferences.remote_only}
                    onChange={(e) => setPreferences({ ...preferences, remote_only: e.target.checked })}
                    className="w-5 h-5 text-teal-500 rounded"
                  />
                  <span className="font-medium">Remote only</span>
                </label>
              </div>
              <div>
                <label className="flex items-center space-x-3 p-4 border-2 rounded-xl cursor-pointer hover:border-slate-300">
                  <input
                    type="checkbox"
                    checked={preferences.hybrid_ok}
                    onChange={(e) => setPreferences({ ...preferences, hybrid_ok: e.target.checked })}
                    className="w-5 h-5 text-teal-500 rounded"
                  />
                  <span className="font-medium">Open to hybrid</span>
                </label>
              </div>
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setStep(1)}
                className="px-6 py-3 text-slate-700 font-medium hover:bg-slate-100 rounded-xl transition-colors"
              >
                Back
              </button>
              <button
                onClick={() => setStep(3)}
                disabled={preferences.locations.length === 0 && !preferences.remote_only}
                className="px-6 py-3 bg-navy-900 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-navy-800 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Companies & Salary */}
        {step === 3 && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Target companies & salary</h2>
            <p className="text-slate-600 mb-6">Optional: Select companies you&apos;d love to work for</p>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
              {suggestedCompanies.map((company) => (
                <button
                  key={company.name}
                  onClick={() => toggleCompany(company.name)}
                  className={`p-4 rounded-xl border-2 transition-all ${
                    preferences.target_companies.includes(company.name)
                      ? 'border-teal-500 bg-teal-50 text-teal-700'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="font-medium">{company.name}</div>
                  <div className="text-xs text-slate-500">{company.industry}</div>
                </button>
              ))}
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Minimum salary expectation (£)
              </label>
              <input
                type="number"
                value={preferences.min_salary || ''}
                onChange={(e) => setPreferences({ ...preferences, min_salary: parseInt(e.target.value) || undefined })}
                placeholder="e.g., 60000"
                className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl focus:border-teal-500 focus:outline-none"
              />
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setStep(2)}
                className="px-6 py-3 text-slate-700 font-medium hover:bg-slate-100 rounded-xl transition-colors"
              >
                Back
              </button>
              <button
                onClick={() => setStep(4)}
                className="px-6 py-3 bg-navy-900 text-white rounded-xl font-medium hover:bg-navy-800 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Review & Search */}
        {step === 4 && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Ready to find your perfect job!</h2>
            <p className="text-slate-600 mb-6">
              We&apos;ll search LinkedIn, Greenhouse, and Lever for jobs matching your preferences.
            </p>

            {searching ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-teal-500 mx-auto mb-4"></div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">Searching for jobs...</h3>
                <p className="text-slate-600 mb-4">This takes about 30-60 seconds</p>
                <div className="w-full bg-slate-200 rounded-full h-3 max-w-md mx-auto">
                  <div
                    className="bg-teal-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${searchProgress}%` }}
                  />
                </div>
              </div>
            ) : (
              <>
                <div className="bg-slate-50 rounded-xl p-6 mb-6">
                  <h3 className="font-semibold text-slate-900 mb-4">Your preferences:</h3>
                  <div className="space-y-3 text-sm">
                    <div>
                      <span className="text-slate-600">Roles:</span>{' '}
                      <span className="font-medium">{preferences.target_roles.join(', ')}</span>
                    </div>
                    <div>
                      <span className="text-slate-600">Locations:</span>{' '}
                      <span className="font-medium">
                        {preferences.locations.join(', ')}
                        {preferences.remote_only && ', Remote'}
                      </span>
                    </div>
                    {preferences.target_companies.length > 0 && (
                      <div>
                        <span className="text-slate-600">Companies:</span>{' '}
                        <span className="font-medium">{preferences.target_companies.join(', ')}</span>
                      </div>
                    )}
                    {preferences.min_salary && (
                      <div>
                        <span className="text-slate-600">Min salary:</span>{' '}
                        <span className="font-medium">£{preferences.min_salary.toLocaleString()}</span>
                      </div>
                    )}
                  </div>
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-6">
                    {error}
                  </div>
                )}

                <div className="flex justify-between">
                  <button
                    onClick={() => setStep(3)}
                    className="px-6 py-3 text-slate-700 font-medium hover:bg-slate-100 rounded-xl transition-colors"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={loading}
                    className="px-8 py-3 bg-teal-500 text-white rounded-xl font-medium hover:bg-teal-600 transition-colors disabled:opacity-50"
                  >
                    {loading ? 'Searching...' : 'Find My Jobs'}
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
