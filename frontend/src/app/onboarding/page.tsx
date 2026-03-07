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

interface Role {
  name: string;
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

export default function OnboardingPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
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
      return 'Salary must be between £0 and £1,000,000';
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
      const saveRes = await fetch('/api/v1/onboarding/preferences', {
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
      const validationError = validatePreferences();
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
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-4"></div>
          <p className="text-slate-600 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-lg sm:text-xl font-bold text-slate-900">Set Up Your Profile</h1>
            <span className="text-xs sm:text-sm font-medium text-slate-600">Step {step} of 5</span>
          </div>
          {/* Progress Bar */}
          <div className="w-full bg-slate-200 rounded-full h-2">
            <div
              className="bg-teal-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(step / 5) * 100}%` }}
            />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {searching ? (
          /* Searching State */
          <div className="bg-white rounded-2xl shadow-xl p-8 sm:p-12 text-center">
            <div className="w-20 h-20 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-teal-600 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Finding Your Perfect Jobs</h2>
            <p className="text-slate-600 mb-6">Searching across Indeed, LinkedIn, and 50+ companies...</p>
            
            {/* Progress */}
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-600">Progress</span>
                <span className="font-medium text-slate-900">{searchProgress}%</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-3">
                <div
                  className="bg-teal-500 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${searchProgress}%` }}
                />
              </div>
            </div>
            
            <p className="text-xs text-slate-500">This takes 2-3 minutes. You can navigate away and come back!</p>
          </div>
        ) : (
          <>
            {/* Step 1: Roles */}
            {step === 1 && (
              <div className="bg-white rounded-2xl shadow-xl p-5 sm:p-8">
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mb-2">What role are you looking for?</h2>
                <p className="text-slate-600 mb-6 text-sm sm:text-base">Select all that apply</p>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-3 mb-6">
                  {suggestedRoles.map((role) => (
                    <button
                      key={role.name}
                      onClick={() => toggleRole(role.name)}
                      className={`p-3 sm:p-4 rounded-xl border-2 transition-all text-sm sm:text-base font-medium min-h-[48px] ${
                        preferences.target_roles.includes(role.name)
                          ? 'border-teal-500 bg-teal-50 text-teal-700'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      {role.name}
                    </button>
                  ))}
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={() => handleStepChange(2)}
                    disabled={preferences.target_roles.length === 0}
                    className="w-full sm:w-auto px-6 py-3 bg-navy-900 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-navy-800 transition-colors min-h-[48px]"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}

            {/* Step 2: Seniority Level */}
            {step === 2 && (
              <div className="bg-white rounded-2xl shadow-xl p-5 sm:p-8">
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mb-2">What&apos;s your seniority level?</h2>
                <p className="text-slate-600 mb-6 text-sm sm:text-base">Select your current or target level</p>

                <div className="space-y-3 mb-6">
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
                      className="flex items-center space-x-3 sm:space-x-4 p-4 sm:p-5 border-2 rounded-xl cursor-pointer hover:border-slate-300 transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={preferences.seniority_levels.includes(level.value)}
                        onChange={() => toggleSeniority(level.value)}
                        className="w-5 h-5 text-teal-500 rounded flex-shrink-0"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-slate-900 text-sm sm:text-base">{level.label}</div>
                        <div className="text-xs sm:text-sm text-slate-500">{level.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>

                <div className="flex flex-col sm:flex-row justify-between gap-3">
                  <button
                    onClick={() => handleStepChange(1)}
                    className="w-full sm:w-auto px-6 py-3 text-slate-700 font-medium hover:bg-slate-100 rounded-xl transition-colors min-h-[48px]"
                  >
                    Back
                  </button>
                  <button
                    onClick={() => handleStepChange(3)}
                    disabled={preferences.seniority_levels.length === 0}
                    className="w-full sm:w-auto px-6 py-3 bg-navy-900 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-navy-800 transition-colors min-h-[48px]"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}

            {/* Step 3: Location & Remote */}
            {step === 3 && (
              <div className="bg-white rounded-2xl shadow-xl p-5 sm:p-8">
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mb-2">Where do you want to work?</h2>
                <p className="text-slate-600 mb-6 text-sm sm:text-base">Select countries and remote preference</p>

                {/* Countries */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-slate-700 mb-3">Countries</label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-3">
                    {[
                      { code: 'uk', name: '🇬🇧 UK' },
                      { code: 'us', name: '🇺🇸 US' },
                      { code: 'ca', name: '🇨🇦 Canada' },
                      { code: 'au', name: '🇦🇺 Australia' },
                      { code: 'de', name: '🇩🇪 Germany' },
                      { code: 'fr', name: '🇫🇷 France' },
                      { code: 'ie', name: '🇮🇪 Ireland' },
                      { code: 'nl', name: '🇳🇱 Netherlands' },
                    ].map((country) => (
                      <button
                        key={country.code}
                        onClick={() => toggleCountry(country.code)}
                        className={`p-3 rounded-xl border-2 transition-all text-sm font-medium min-h-[48px] ${
                          preferences.countries.includes(country.code)
                            ? 'border-teal-500 bg-teal-50 text-teal-700'
                            : 'border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        {country.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Remote Preference */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-slate-700 mb-3">Remote Preference</label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
                    {[
                      { value: 'any', label: 'Any', icon: '🌍' },
                      { value: 'remote_only', label: 'Remote Only', icon: '🏠' },
                      { value: 'hybrid_ok', label: 'Hybrid OK', icon: '🔄' },
                      { value: 'onsite_only', label: 'Onsite Only', icon: '🏢' },
                    ].map((option) => (
                      <button
                        key={option.value}
                        onClick={() => setPreferences((prev) => ({ ...prev, remote_preference: option.value }))}
                        className={`p-3 rounded-xl border-2 transition-all text-sm font-medium min-h-[48px] flex flex-col items-center justify-center space-y-1 ${
                          preferences.remote_preference === option.value
                            ? 'border-teal-500 bg-teal-50 text-teal-700'
                            : 'border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <span className="text-lg">{option.icon}</span>
                        <span>{option.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row justify-between gap-3">
                  <button
                    onClick={() => handleStepChange(2)}
                    className="w-full sm:w-auto px-6 py-3 text-slate-700 font-medium hover:bg-slate-100 rounded-xl transition-colors min-h-[48px]"
                  >
                    Back
                  </button>
                  <button
                    onClick={() => handleStepChange(4)}
                    disabled={preferences.countries.length === 0}
                    className="w-full sm:w-auto px-6 py-3 bg-navy-900 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-navy-800 transition-colors min-h-[48px]"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}

            {/* Step 4: Job Type & Date Posted */}
            {step === 4 && (
              <div className="bg-white rounded-2xl shadow-xl p-5 sm:p-8">
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mb-2">Job preferences</h2>
                <p className="text-slate-600 mb-6 text-sm sm:text-base">Employment type and when jobs were posted</p>

                {/* Employment Type */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-slate-700 mb-3">Employment Type</label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
                    {[
                      { value: 'fulltime', label: 'Full-time', icon: '⏰' },
                      { value: 'parttime', label: 'Part-time', icon: '🕐' },
                      { value: 'contract', label: 'Contract', icon: '📄' },
                      { value: 'internship', label: 'Internship', icon: '🎓' },
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
                        className={`p-3 rounded-xl border-2 transition-all text-sm font-medium min-h-[48px] flex flex-col items-center justify-center space-y-1 ${
                          preferences.employment_types.includes(option.value)
                            ? 'border-teal-500 bg-teal-50 text-teal-700'
                            : 'border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <span className="text-lg">{option.icon}</span>
                        <span>{option.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Date Posted */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-slate-700 mb-3">Date Posted</label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
                    {[
                      { value: 'day', label: 'Last 24h', icon: '🕐' },
                      { value: 'week', label: 'Past Week', icon: '📅' },
                      { value: 'month', label: 'Past Month', icon: '🗓️' },
                      { value: 'any', label: 'Any Time', icon: '∞' },
                    ].map((option) => (
                      <button
                        key={option.value}
                        onClick={() => setPreferences((prev) => ({ ...prev, date_posted: option.value }))}
                        className={`p-3 rounded-xl border-2 transition-all text-sm font-medium min-h-[48px] flex flex-col items-center justify-center space-y-1 ${
                          preferences.date_posted === option.value
                            ? 'border-teal-500 bg-teal-50 text-teal-700'
                            : 'border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <span className="text-lg">{option.icon}</span>
                        <span>{option.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Min Salary */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-slate-700 mb-3">
                    Minimum Salary (optional)
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 text-lg">£</span>
                    <input
                      type="number"
                      value={preferences.min_salary || ''}
                      onChange={(e) => setPreferences((prev) => ({ ...prev, min_salary: parseInt(e.target.value) || undefined }))}
                      placeholder="60000"
                      className="w-full pl-8 pr-4 py-3 border-2 border-slate-200 rounded-xl focus:border-teal-500 focus:outline-none text-base min-h-[48px]"
                    />
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row justify-between gap-3">
                  <button
                    onClick={() => handleStepChange(3)}
                    className="w-full sm:w-auto px-6 py-3 text-slate-700 font-medium hover:bg-slate-100 rounded-xl transition-colors min-h-[48px]"
                  >
                    Back
                  </button>
                  <button
                    onClick={() => handleStepChange(5)}
                    disabled={preferences.employment_types.length === 0}
                    className="w-full sm:w-auto px-6 py-3 bg-navy-900 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-navy-800 transition-colors min-h-[48px]"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}

            {/* Step 5: Review & Search */}
            {step === 5 && (
              <div className="bg-white rounded-2xl shadow-xl p-5 sm:p-8">
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mb-2">Review your preferences</h2>
                <p className="text-slate-600 mb-6 text-sm sm:text-base">Make sure everything looks good!</p>

                <div className="space-y-4 mb-6">
                  <div className="p-4 bg-slate-50 rounded-xl">
                    <div className="text-xs font-medium text-slate-500 mb-1">Roles</div>
                    <div className="text-sm font-medium text-slate-900">{preferences.target_roles.join(', ') || 'None selected'}</div>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-xl">
                    <div className="text-xs font-medium text-slate-500 mb-1">Seniority</div>
                    <div className="text-sm font-medium text-slate-900">{preferences.seniority_levels.join(', ') || 'None selected'}</div>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-xl">
                    <div className="text-xs font-medium text-slate-500 mb-1">Locations</div>
                    <div className="text-sm font-medium text-slate-900">
                      {preferences.countries.map(c => c.toUpperCase()).join(', ')}
                      {preferences.locations.length > 0 && `, ${preferences.locations.join(', ')}`}
                    </div>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-xl">
                    <div className="text-xs font-medium text-slate-500 mb-1">Remote</div>
                    <div className="text-sm font-medium text-slate-900 capitalize">{preferences.remote_preference.replace('_', ' ')}</div>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-xl">
                    <div className="text-xs font-medium text-slate-500 mb-1">Employment Type</div>
                    <div className="text-sm font-medium text-slate-900 capitalize">{preferences.employment_types.join(', ').replace('_', ' ')}</div>
                  </div>
                  {preferences.min_salary && (
                    <div className="p-4 bg-slate-50 rounded-xl">
                      <div className="text-xs font-medium text-slate-500 mb-1">Min Salary</div>
                      <div className="text-sm font-medium text-slate-900">£{preferences.min_salary.toLocaleString()}</div>
                    </div>
                  )}
                </div>

                {error && (
                  <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
                    {error}
                  </div>
                )}

                <div className="flex flex-col sm:flex-row justify-between gap-3">
                  <button
                    onClick={() => handleStepChange(4)}
                    className="w-full sm:w-auto px-6 py-3 text-slate-700 font-medium hover:bg-slate-100 rounded-xl transition-colors min-h-[48px]"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={loading}
                    className="w-full sm:w-auto px-8 py-3 bg-teal-500 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-teal-600 transition-colors min-h-[48px] flex items-center justify-center space-x-2"
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span>Saving...</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <span>Start Job Search</span>
                      </>
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
