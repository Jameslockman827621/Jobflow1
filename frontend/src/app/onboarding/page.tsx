'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toast';

interface Company {
  name: string;
  industry: string;
  size: string;
}

interface Preferences {
  target_roles: string[];
  seniority_levels: string[];
  locations: string[];
  countries: string[];
  remote_preference: string;
  employment_types: string[];
  date_posted: string;
  min_salary?: number;
  target_companies: string[];
  required_skills: string[];
}

const STEPS = [
  { num: 1, label: 'Roles' },
  { num: 2, label: 'Experience' },
  { num: 3, label: 'Locations' },
  { num: 4, label: 'Preferences' },
  { num: 5, label: 'Review' },
];

export default function OnboardingPage() {
  const router = useRouter();
  const { user, loading: authLoading, authFetch } = useAuth();
  const toast = useToast();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchProgress, setSearchProgress] = useState(0);

  const [preferences, setPreferences] = useState<Preferences>({
    target_roles: [],
    seniority_levels: [],
    locations: [],
    countries: ['uk'],
    remote_preference: 'any',
    employment_types: ['fulltime'],
    date_posted: 'month',
    min_salary: undefined,
    target_companies: [],
    required_skills: [],
  });

  const [suggestedCompanies, setSuggestedCompanies] = useState<Company[]>([]);
  const [suggestedRoles, setSuggestedRoles] = useState<string[]>([]);

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
        authFetch('/api/v1/onboarding/companies/suggested'),
        authFetch('/api/v1/onboarding/roles/suggested'),
      ]);

      const companiesData = await companiesRes.json();
      const rolesData = await rolesRes.json();

      setSuggestedCompanies(companiesData.companies || []);
      setSuggestedRoles(rolesData.roles || []);
    } catch (err) {
      console.error('Failed to fetch suggestions:', err);
    }
  };

  const validatePreferences = (): string | null => {
    if (preferences.target_roles.length === 0) {
      return 'Please select at least one role';
    }
    if (preferences.seniority_levels.length === 0) {
      return 'Please select your seniority level';
    }
    if (preferences.locations.length === 0 && preferences.countries.length === 0) {
      return 'Please select at least one location or country';
    }
    if (preferences.employment_types.length === 0) {
      return 'Please select at least one employment type';
    }
    if (preferences.min_salary && (preferences.min_salary < 0 || preferences.min_salary > 1000000)) {
      return 'Salary must be between \u00A30 and \u00A31,000,000';
    }
    return null;
  };

  const handleSubmit = async () => {
    const validationError = validatePreferences();
    if (validationError) {
      toast.error(validationError);
      setError(validationError);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const saveRes = await authFetch('/api/v1/onboarding/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preferences),
      });

      if (!saveRes.ok) {
        const errorData = await saveRes.json();
        throw new Error(errorData.detail || 'Failed to save preferences');
      }

      toast.success('Preferences saved!');

      setSearching(true);
      setSearchProgress(0);
      toast.loading('Searching for jobs... This takes 2-3 minutes');

      const progressInterval = setInterval(() => {
        setSearchProgress((prev) => Math.min(prev + 5, 90));
      }, 800);

      const searchRes = await authFetch('/api/v1/onboarding/search', {
        method: 'POST',
      });

      clearInterval(progressInterval);
      setSearchProgress(100);

      if (!searchRes.ok) {
        const errorData = await searchRes.json();
        throw new Error(errorData.detail || 'Failed to search jobs');
      }

      const searchData = await searchRes.json();
      toast.success(`Found ${searchData.total} jobs!`);

      setTimeout(() => {
        router.push(`/dashboard?onboarding=complete&jobs=${searchData.total}`);
      }, 1000);
    } catch (err: any) {
      console.error('Onboarding error:', err);
      toast.error(err.message || 'Something went wrong');
      setError(err.message || 'Something went wrong');
      setSearching(false);
    } finally {
      setLoading(false);
    }
  };

  const handleStepChange = (newStep: number) => {
    if (newStep > step) {
      let validationError: string | null = null;

      if (step === 1 && preferences.target_roles.length === 0) {
        validationError = 'Please select at least one role';
      } else if (step === 2 && preferences.seniority_levels.length === 0) {
        validationError = 'Please select your seniority level';
      } else if (step === 3 && preferences.locations.length === 0 && preferences.countries.length === 0) {
        validationError = 'Please select at least one location or country';
      } else if (step === 4 && preferences.employment_types.length === 0) {
        validationError = 'Please select at least one employment type';
      }

      if (validationError) {
        toast.error(validationError);
        setError(validationError);
        return;
      }
    }

    setStep(newStep);
    setError('');
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

  const toggleCountry = (country: string) => {
    setPreferences((prev) => ({
      ...prev,
      countries: prev.countries.includes(country)
        ? prev.countries.filter((c) => c !== country)
        : [...prev.countries, country],
    }));
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="h-1 w-48 bg-slate-200 rounded-full overflow-hidden mx-auto mb-4">
            <div className="h-full w-1/2 bg-teal-500 rounded-full animate-pulse" />
          </div>
          <p className="text-slate-500 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-lg font-semibold text-navy-900">Set up your profile</h1>
            <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md">Step {step} of 5</span>
          </div>
          <div className="flex items-center gap-1">
            {STEPS.map((s) => (
              <div key={s.num} className="flex-1 flex flex-col items-center gap-1">
                <div className={`w-full h-1 rounded-full transition-colors ${s.num <= step ? 'bg-teal-500' : 'bg-slate-200'}`} />
                <span className={`text-[10px] font-medium hidden sm:block ${s.num <= step ? 'text-teal-600' : 'text-slate-400'}`}>{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        {searching ? (
          <div className="bg-white rounded-xl border border-slate-200 p-8 sm:p-12 text-center">
            <h2 className="text-xl font-semibold text-navy-900 mb-2">Searching for jobs</h2>
            <p className="text-sm text-slate-500 mb-8">Scanning across multiple job boards and company pages...</p>

            <div className="max-w-sm mx-auto mb-4">
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="text-slate-500">Progress</span>
                <span className="font-medium text-slate-700">{searchProgress}%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-1.5">
                <div
                  className="bg-teal-500 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${searchProgress}%` }}
                />
              </div>
            </div>

            <p className="text-xs text-slate-400">This takes 2-3 minutes. You can navigate away and come back.</p>
          </div>
        ) : (
          <>
            {step === 1 && (
              <div className="bg-white rounded-xl border border-slate-200 p-5 sm:p-8">
                <h2 className="text-xl font-semibold text-navy-900 mb-1">Select your target roles</h2>
                <p className="text-sm text-slate-500 mb-6">Choose all that apply</p>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-8">
                  {suggestedRoles.map((role) => (
                    <button
                      key={role}
                      onClick={() => toggleRole(role)}
                      className={`px-3 py-3 rounded-lg border text-sm font-medium transition-all min-h-[44px] ${
                        preferences.target_roles.includes(role)
                          ? 'border-teal-500 bg-teal-500 text-white'
                          : 'border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      {role}
                    </button>
                  ))}
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={() => handleStepChange(2)}
                    disabled={preferences.target_roles.length === 0}
                    className="w-full sm:w-auto px-6 py-2.5 bg-navy-900 text-white rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-navy-800 transition-colors min-h-[44px]"
                  >
                    Continue
                  </button>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="bg-white rounded-xl border border-slate-200 p-5 sm:p-8">
                <h2 className="text-xl font-semibold text-navy-900 mb-1">Experience level</h2>
                <p className="text-sm text-slate-500 mb-6">Select your current or target level</p>

                <div className="space-y-2 mb-8">
                  {[
                    { value: 'entry', label: 'Entry Level', desc: '0-2 years experience' },
                    { value: 'mid', label: 'Mid-Level', desc: '2-5 years experience' },
                    { value: 'senior', label: 'Senior', desc: '5-8 years experience' },
                    { value: 'lead', label: 'Lead / Staff', desc: '8+ years, technical leadership' },
                    { value: 'director', label: 'Director', desc: 'People management' },
                    { value: 'executive', label: 'Executive (VP, C-level)', desc: 'Strategic leadership' },
                  ].map((level) => (
                    <label
                      key={level.value}
                      className={`flex items-center gap-3 p-4 border rounded-lg cursor-pointer transition-colors ${
                        preferences.seniority_levels.includes(level.value)
                          ? 'border-teal-500 bg-teal-50/50'
                          : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={preferences.seniority_levels.includes(level.value)}
                        onChange={() => toggleSeniority(level.value)}
                        className="w-4 h-4 text-teal-500 rounded flex-shrink-0 border-slate-300 focus:ring-teal-500"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-slate-900">{level.label}</div>
                        <div className="text-xs text-slate-500">{level.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>

                <div className="flex flex-col sm:flex-row justify-between gap-3">
                  <button
                    onClick={() => handleStepChange(1)}
                    className="w-full sm:w-auto px-6 py-2.5 text-sm text-slate-600 font-medium hover:bg-slate-100 rounded-lg transition-colors min-h-[44px]"
                  >
                    Back
                  </button>
                  <button
                    onClick={() => handleStepChange(3)}
                    disabled={preferences.seniority_levels.length === 0}
                    className="w-full sm:w-auto px-6 py-2.5 bg-navy-900 text-white rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-navy-800 transition-colors min-h-[44px]"
                  >
                    Continue
                  </button>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="bg-white rounded-xl border border-slate-200 p-5 sm:p-8">
                <h2 className="text-xl font-semibold text-navy-900 mb-1">Preferred locations</h2>
                <p className="text-sm text-slate-500 mb-6">Select countries and remote preference</p>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-slate-700 mb-3">Countries</label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {[
                      { code: 'uk', name: 'UK' },
                      { code: 'us', name: 'US' },
                      { code: 'ca', name: 'Canada' },
                      { code: 'au', name: 'Australia' },
                      { code: 'de', name: 'Germany' },
                      { code: 'fr', name: 'France' },
                      { code: 'ie', name: 'Ireland' },
                      { code: 'nl', name: 'Netherlands' },
                    ].map((country) => (
                      <button
                        key={country.code}
                        onClick={() => toggleCountry(country.code)}
                        className={`px-3 py-2.5 rounded-lg border text-sm font-medium transition-all min-h-[44px] ${
                          preferences.countries.includes(country.code)
                            ? 'border-teal-500 bg-teal-500 text-white'
                            : 'border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                      >
                        {country.name}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="mb-8">
                  <label className="block text-sm font-medium text-slate-700 mb-3">Remote preference</label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {[
                      { value: 'any', label: 'Any' },
                      { value: 'remote_only', label: 'Remote only' },
                      { value: 'hybrid_ok', label: 'Hybrid OK' },
                      { value: 'onsite_only', label: 'Onsite only' },
                    ].map((option) => (
                      <button
                        key={option.value}
                        onClick={() => setPreferences((prev) => ({ ...prev, remote_preference: option.value }))}
                        className={`px-3 py-2.5 rounded-lg border text-sm font-medium transition-all min-h-[44px] ${
                          preferences.remote_preference === option.value
                            ? 'border-teal-500 bg-teal-500 text-white'
                            : 'border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row justify-between gap-3">
                  <button
                    onClick={() => handleStepChange(2)}
                    className="w-full sm:w-auto px-6 py-2.5 text-sm text-slate-600 font-medium hover:bg-slate-100 rounded-lg transition-colors min-h-[44px]"
                  >
                    Back
                  </button>
                  <button
                    onClick={() => handleStepChange(4)}
                    disabled={preferences.countries.length === 0}
                    className="w-full sm:w-auto px-6 py-2.5 bg-navy-900 text-white rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-navy-800 transition-colors min-h-[44px]"
                  >
                    Continue
                  </button>
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="bg-white rounded-xl border border-slate-200 p-5 sm:p-8">
                <h2 className="text-xl font-semibold text-navy-900 mb-1">Job preferences</h2>
                <p className="text-sm text-slate-500 mb-6">Employment type and recency</p>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-slate-700 mb-3">Employment type</label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {[
                      { value: 'fulltime', label: 'Full-time' },
                      { value: 'parttime', label: 'Part-time' },
                      { value: 'contract', label: 'Contract' },
                      { value: 'internship', label: 'Internship' },
                    ].map((option) => (
                      <button
                        key={option.value}
                        onClick={() => {
                          setPreferences((prev) => ({
                            ...prev,
                            employment_types: prev.employment_types.includes(option.value)
                              ? prev.employment_types.filter((t) => t !== option.value)
                              : [...prev.employment_types, option.value],
                          }));
                        }}
                        className={`px-3 py-2.5 rounded-lg border text-sm font-medium transition-all min-h-[44px] ${
                          preferences.employment_types.includes(option.value)
                            ? 'border-teal-500 bg-teal-500 text-white'
                            : 'border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-slate-700 mb-3">Date posted</label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {[
                      { value: 'day', label: 'Last 24 hours' },
                      { value: 'week', label: 'Past week' },
                      { value: 'month', label: 'Past month' },
                      { value: 'any', label: 'Any time' },
                    ].map((option) => (
                      <button
                        key={option.value}
                        onClick={() => setPreferences((prev) => ({ ...prev, date_posted: option.value }))}
                        className={`px-3 py-2.5 rounded-lg border text-sm font-medium transition-all min-h-[44px] ${
                          preferences.date_posted === option.value
                            ? 'border-teal-500 bg-teal-500 text-white'
                            : 'border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="mb-8">
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Minimum salary (optional)
                  </label>
                  <div className="relative max-w-xs">
                    <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-sm font-medium">{'\u00A3'}</span>
                    <input
                      type="number"
                      value={preferences.min_salary || ''}
                      onChange={(e) => setPreferences((prev) => ({ ...prev, min_salary: parseInt(e.target.value) || undefined }))}
                      placeholder="60,000"
                      className="w-full pl-7 pr-4 py-2.5 border border-slate-200 rounded-lg focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none text-sm min-h-[44px]"
                    />
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row justify-between gap-3">
                  <button
                    onClick={() => handleStepChange(3)}
                    className="w-full sm:w-auto px-6 py-2.5 text-sm text-slate-600 font-medium hover:bg-slate-100 rounded-lg transition-colors min-h-[44px]"
                  >
                    Back
                  </button>
                  <button
                    onClick={() => handleStepChange(5)}
                    disabled={preferences.employment_types.length === 0}
                    className="w-full sm:w-auto px-6 py-2.5 bg-navy-900 text-white rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-navy-800 transition-colors min-h-[44px]"
                  >
                    Continue
                  </button>
                </div>
              </div>
            )}

            {step === 5 && (
              <div className="bg-white rounded-xl border border-slate-200 p-5 sm:p-8">
                <h2 className="text-xl font-semibold text-navy-900 mb-1">Review and search</h2>
                <p className="text-sm text-slate-500 mb-6">Confirm everything looks correct before searching.</p>

                <div className="space-y-3 mb-8">
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                    <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Roles</div>
                    <div className="text-sm font-medium text-slate-900">{preferences.target_roles.join(', ') || 'None selected'}</div>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                    <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Seniority</div>
                    <div className="text-sm font-medium text-slate-900">{preferences.seniority_levels.join(', ') || 'None selected'}</div>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                    <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Locations</div>
                    <div className="text-sm font-medium text-slate-900">
                      {preferences.countries.map(c => c.toUpperCase()).join(', ')}
                      {preferences.locations.length > 0 && `, ${preferences.locations.join(', ')}`}
                    </div>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                    <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Remote</div>
                    <div className="text-sm font-medium text-slate-900 capitalize">{preferences.remote_preference.replace('_', ' ')}</div>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                    <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Employment type</div>
                    <div className="text-sm font-medium text-slate-900 capitalize">{preferences.employment_types.join(', ').replace('_', ' ')}</div>
                  </div>
                  {preferences.min_salary && (
                    <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                      <div className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1">Min salary</div>
                      <div className="text-sm font-medium text-slate-900">{'\u00A3'}{preferences.min_salary.toLocaleString()}</div>
                    </div>
                  )}
                </div>

                {error && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm flex items-center gap-2">
                    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" /></svg>
                    {error}
                  </div>
                )}

                <div className="flex flex-col sm:flex-row justify-between gap-3">
                  <button
                    onClick={() => handleStepChange(4)}
                    className="w-full sm:w-auto px-6 py-2.5 text-sm text-slate-600 font-medium hover:bg-slate-100 rounded-lg transition-colors min-h-[44px]"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={loading}
                    className="w-full sm:w-auto px-6 py-2.5 bg-teal-500 text-white rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-teal-600 transition-colors min-h-[44px] flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <div className="h-1 w-16 bg-teal-400 rounded-full overflow-hidden">
                          <div className="h-full w-1/2 bg-white rounded-full animate-pulse" />
                        </div>
                        <span>Saving...</span>
                      </>
                    ) : (
                      <span>Start job search</span>
                    )}
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
