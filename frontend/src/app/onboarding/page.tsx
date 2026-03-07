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
    // Validate before submitting
    const validationError = validatePreferences();
    if (validationError) {
      setError(validationError);
      return;
    }

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
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Progress */}
        <div className="mb-8">
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium text-slate-700">Step {step} of 5</span>
            <span className="text-sm font-medium text-slate-700">{Math.round((step / 5) * 100)}%</span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-2">
            <div
              className="bg-teal-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(step / 5) * 100}%` }}
            />
          </div>
        </div>

        {/* Step 1: Roles */}
        {step === 1 && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">What role are you looking for?</h2>
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

        {/* Step 2: Seniority Level */}
        {step === 2 && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">What&apos;s your seniority level?</h2>
            <p className="text-slate-600 mb-6">Select your current or target level</p>

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
                  className="flex items-center space-x-4 p-5 border-2 rounded-xl cursor-pointer hover:border-slate-300 transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={preferences.seniority_levels.includes(level.value)}
                    onChange={() => toggleSeniority(level.value)}
                    className="w-5 h-5 text-teal-500 rounded"
                  />
                  <div>
                    <div className="font-medium text-slate-900">{level.label}</div>
                    <div className="text-sm text-slate-500">{level.desc}</div>
                  </div>
                </label>
              ))}
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
                disabled={preferences.seniority_levels.length === 0}
                className="px-6 py-3 bg-navy-900 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-navy-800 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Location & Remote */}
        {step === 3 && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Where do you want to work?</h2>
            <p className="text-slate-600 mb-6">Select countries, cities, and remote preference</p>

            {/* Countries */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-700 mb-3">Countries</label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {[
                  { code: 'uk', name: '🇬🇧 United Kingdom' },
                  { code: 'us', name: '🇺🇸 United States' },
                  { code: 'ca', name: '🇨🇦 Canada' },
                  { code: 'au', name: '🇦🇺 Australia' },
                  { code: 'de', name: '🇩🇪 Germany' },
                  { code: 'fr', name: '🇫🇷 France' },
                  { code: 'ie', name: '🇮🇪 Ireland' },
                  { code: 'nl', name: '🇳🇱 Netherlands' },
                ].map((country) => (
                  <label
                    key={country.code}
                    className="flex items-center space-x-3 p-4 border-2 rounded-xl cursor-pointer hover:border-slate-300"
                  >
                    <input
                      type="checkbox"
                      checked={preferences.countries.includes(country.code)}
                      onChange={() => toggleCountry(country.code)}
                      className="w-5 h-5 text-teal-500 rounded"
                    />
                    <span className="font-medium">{country.name}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Cities */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-700 mb-3">Cities / Regions</label>
              <div className="space-y-3">
                {[
                  'London, UK',
                  'Manchester, UK',
                  'Birmingham, UK',
                  'New York, US',
                  'San Francisco, US',
                  'Toronto, CA',
                  'Berlin, DE',
                  'Paris, FR',
                  'Remote',
                ].map((location) => (
                  <label
                    key={location}
                    className="flex items-center space-x-3 p-4 border-2 rounded-xl cursor-pointer hover:border-slate-300"
                  >
                    <input
                      type="checkbox"
                      checked={preferences.locations.includes(location)}
                      onChange={() => toggleLocation(location)}
                      className="w-5 h-5 text-teal-500 rounded"
                    />
                    <span className="font-medium">{location}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Remote Preference */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-700 mb-3">Remote Preference</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { value: 'any', label: 'Any', icon: '🌍' },
                  { value: 'remote_only', label: 'Remote Only', icon: '🏠' },
                  { value: 'hybrid_ok', label: 'Hybrid OK', icon: '🔄' },
                  { value: 'onsite_only', label: 'On-site Only', icon: '🏢' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setPreferences({ ...preferences, remote_preference: option.value })}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      preferences.remote_preference === option.value
                        ? 'border-teal-500 bg-teal-50 text-teal-700'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="text-2xl mb-2">{option.icon}</div>
                    <div className="font-medium">{option.label}</div>
                  </button>
                ))}
              </div>
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
                disabled={preferences.locations.length === 0 && preferences.countries.length === 0}
                className="px-6 py-3 bg-navy-900 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-navy-800 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Job Type & Timing */}
        {step === 4 && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Job type & timing</h2>
            <p className="text-slate-600 mb-6">Specify employment type and how recent jobs should be</p>

            {/* Employment Type */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-700 mb-3">Employment Type</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { value: 'fulltime', label: 'Full-time', icon: '⏰' },
                  { value: 'parttime', label: 'Part-time', icon: '🕐' },
                  { value: 'contract', label: 'Contract', icon: '📋' },
                  { value: 'internship', label: 'Internship', icon: '🎓' },
                ].map((type) => (
                  <label
                    key={type.value}
                    className="flex items-center justify-center space-x-2 p-4 border-2 rounded-xl cursor-pointer hover:border-slate-300"
                  >
                    <input
                      type="checkbox"
                      checked={preferences.employment_types.includes(type.value)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setPreferences({ ...preferences, employment_types: [...preferences.employment_types, type.value] });
                        } else {
                          setPreferences({
                            ...preferences,
                            employment_types: preferences.employment_types.filter((t) => t !== type.value),
                          });
                        }
                      }}
                      className="w-5 h-5 text-teal-500 rounded"
                    />
                    <div>
                      <div className="text-xl mb-1">{type.icon}</div>
                      <div className="font-medium text-sm">{type.label}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Date Posted */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-slate-700 mb-3">Jobs Posted</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { value: 'day', label: 'Last 24 Hours', desc: ' freshest' },
                  { value: 'week', label: 'Last Week', desc: 'Recent' },
                  { value: 'month', label: 'Last Month', desc: 'Good variety' },
                  { value: 'any', label: 'Any Time', desc: 'All jobs' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setPreferences({ ...preferences, date_posted: option.value })}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      preferences.date_posted === option.value
                        ? 'border-teal-500 bg-teal-50 text-teal-700'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="font-medium">{option.label}</div>
                    <div className="text-xs text-slate-500">{option.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Salary */}
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
              <p className="text-xs text-slate-500 mt-2">Optional - used for filtering, not search</p>
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setStep(3)}
                className="px-6 py-3 text-slate-700 font-medium hover:bg-slate-100 rounded-xl transition-colors"
              >
                Back
              </button>
              <button
                onClick={() => setStep(5)}
                className="px-6 py-3 bg-navy-900 text-white rounded-xl font-medium hover:bg-navy-800 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Step 5: Companies & Review */}
        {step === 5 && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Target companies (optional)</h2>
            <p className="text-slate-600 mb-6">Select companies you&apos;d love to work for</p>

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

            <div className="bg-slate-50 rounded-xl p-6 mb-6">
              <h3 className="font-semibold text-slate-900 mb-4">Your preferences:</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-slate-600">Roles:</span>{' '}
                  <span className="font-medium">{preferences.target_roles.join(', ')}</span>
                </div>
                <div>
                  <span className="text-slate-600">Seniority:</span>{' '}
                  <span className="font-medium">{preferences.seniority_levels.join(', ')}</span>
                </div>
                <div>
                  <span className="text-slate-600">Locations:</span>{' '}
                  <span className="font-medium">
                    {preferences.countries.join(', ').toUpperCase()} • {preferences.locations.join(', ')}
                  </span>
                </div>
                <div>
                  <span className="text-slate-600">Remote:</span>{' '}
                  <span className="font-medium">{preferences.remote_preference.replace('_', ' ')}</span>
                </div>
                <div>
                  <span className="text-slate-600">Type:</span>{' '}
                  <span className="font-medium">{preferences.employment_types.join(', ')}</span>
                </div>
                <div>
                  <span className="text-slate-600">Posted:</span>{' '}
                  <span className="font-medium">Last {preferences.date_posted}</span>
                </div>
                {preferences.min_salary && (
                  <div>
                    <span className="text-slate-600">Min salary:</span>{' '}
                    <span className="font-medium">£{preferences.min_salary.toLocaleString()}</span>
                  </div>
                )}
                {preferences.target_companies.length > 0 && (
                  <div>
                    <span className="text-slate-600">Companies:</span>{' '}
                    <span className="font-medium">{preferences.target_companies.join(', ')}</span>
                  </div>
                )}
              </div>
            </div>

            {searching ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-teal-500 mx-auto mb-4"></div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">Searching for jobs...</h3>
                <p className="text-slate-600 mb-4">This takes about 2-3 minutes</p>
                <p className="text-xs text-slate-500 mb-4">
                  Searching LinkedIn, Indeed, Greenhouse, and Lever simultaneously
                </p>
                <div className="w-full bg-slate-200 rounded-full h-3 max-w-md mx-auto">
                  <div
                    className="bg-teal-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${searchProgress}%` }}
                  />
                </div>
              </div>
            ) : (
              <>
                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-6">
                    {error}
                  </div>
                )}

                <div className="flex justify-between">
                  <button
                    onClick={() => setStep(4)}
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
