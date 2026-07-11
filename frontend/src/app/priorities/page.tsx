'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toast';
import AppShell from '@/components/AppShell';

interface Dimension {
  field: string;
  label: string;
  input_type: string;
  unit?: string;
  description: string;
  options?: string[];
}

interface MustHave {
  field: string;
  value: any;
}

interface PriorityWeight {
  field: string;
  weight: number;
}

const COMMON_SKILLS = [
  'Python', 'TypeScript', 'JavaScript', 'React', 'Node.js', 'Java',
  'Go', 'Rust', 'AWS', 'Docker', 'Kubernetes', 'PostgreSQL',
  'GraphQL', 'FastAPI', 'Django', 'Flask', 'Machine Learning',
  'TensorFlow', 'PyTorch', 'Redis', 'Kafka', 'Terraform',
];

export default function PrioritiesPage() {
  const router = useRouter();
  const { authFetch, user, loading: authLoading } = useAuth();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dimensions, setDimensions] = useState<Dimension[]>([]);
  const [mustHaves, setMustHaves] = useState<MustHave[]>([]);
  const [weights, setWeights] = useState<PriorityWeight[]>([]);
  const [matchResults, setMatchResults] = useState<any>(null);
  const [matching, setMatching] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [dimRes, priRes] = await Promise.all([
        authFetch('/api/v1/onboarding/priorities/dimensions'),
        authFetch('/api/v1/onboarding/priorities'),
      ]);
      if (dimRes.ok) {
        const dimData = await dimRes.json();
        setDimensions(dimData.dimensions || []);
      }
      if (priRes.ok) {
        const priData = await priRes.json();
        setMustHaves(priData.must_haves || []);
        setWeights(priData.priority_weights || []);
      }
    } catch (err) {
      console.error('Failed to load priorities:', err);
    } finally {
      setLoading(false);
    }
  }, [authFetch]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login?next=/priorities');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) loadData();
  }, [user, loadData]);

  function addMustHave(field: string) {
    if (mustHaves.length >= 5) {
      toast.error('Maximum 5 must-haves. Remove one to add another.');
      return;
    }
    if (mustHaves.some(m => m.field === field)) {
      toast.info('Already added');
      return;
    }
    const dim = dimensions.find(d => d.field === field);
    if (!dim) return;
    // Default value based on input type
    let defaultValue: any = true;
    if (dim.input_type === 'number') defaultValue = 80000;
    if (dim.input_type === 'text') defaultValue = '';
    if (dim.input_type === 'multiselect') defaultValue = dim.options ? [dim.options[0]] : [];
    if (dim.input_type === 'skills') defaultValue = [];
    setMustHaves([...mustHaves, { field, value: defaultValue }]);
    // Auto-add to weights with a default weight
    if (!weights.some(w => w.field === field)) {
      setWeights([...weights, { field, weight: 5 - mustHaves.length }]);
    }
  }

  function removeMustHave(field: string) {
    setMustHaves(mustHaves.filter(m => m.field !== field));
    setWeights(weights.filter(w => w.field !== field));
  }

  function updateMustHaveValue(field: string, value: any) {
    setMustHaves(mustHaves.map(m => m.field === field ? { ...m, value } : m));
  }

  function updateWeight(field: string, weight: number) {
    setWeights(weights.map(w => w.field === field ? { ...w, weight } : w));
  }

  async function save() {
    setSaving(true);
    try {
      const res = await authFetch('/api/v1/onboarding/priorities', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ must_haves: mustHaves, priority_weights: weights }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Save failed');
      }
      toast.success(`Saved ${mustHaves.length} must-haves. Your dashboard will now filter to only jobs that meet all of them.`);
    } catch (err: any) {
      toast.error(err.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  }

  async function runMatch() {
    setMatching(true);
    try {
      const res = await authFetch('/api/v1/jobs/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Match failed');
      }
      const data = await res.json();
      setMatchResults(data);
      toast.success(data.message || `Found ${data.total} matching jobs`);
    } catch (err: any) {
      toast.error(err.message || 'Failed to match');
    } finally {
      setMatching(false);
    }
  }

  function renderValueInput(mustHave: MustHave) {
    const dim = dimensions.find(d => d.field === mustHave.field);
    if (!dim) return null;

    if (dim.input_type === 'number') {
      return (
        <div className="flex items-center gap-2">
          {dim.unit && <span className="text-sm text-slate-500">{dim.unit}</span>}
          <input
            type="number"
            value={mustHave.value}
            onChange={e => updateMustHaveValue(mustHave.field, parseInt(e.target.value) || 0)}
            className="w-32 px-3 py-1.5 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
        </div>
      );
    }

    if (dim.input_type === 'boolean') {
      return (
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={mustHave.value === true}
            onChange={e => updateMustHaveValue(mustHave.field, e.target.checked)}
            className="w-4 h-4 rounded text-teal-500 focus:ring-teal-500"
          />
          <span className="text-sm text-slate-600">Required</span>
        </label>
      );
    }

    if (dim.input_type === 'text') {
      return (
        <input
          type="text"
          value={mustHave.value}
          onChange={e => updateMustHaveValue(mustHave.field, e.target.value)}
          placeholder={dim.field === 'location' ? 'e.g. London, UK' : dim.field === 'company' ? 'e.g. Stripe' : ''}
          className="w-full px-3 py-1.5 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
      );
    }

    if (dim.input_type === 'multiselect') {
      return (
        <div className="flex flex-wrap gap-1.5">
          {dim.options?.map(opt => {
            const selected = (mustHave.value || []).includes(opt);
            return (
              <button
                key={opt}
                onClick={() => {
                  const current = mustHave.value || [];
                  const next = selected ? current.filter((v: string) => v !== opt) : [...current, opt];
                  updateMustHaveValue(mustHave.field, next);
                }}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${selected ? 'bg-teal-500 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:border-teal-400'}`}
              >
                {opt.replace('_', ' ')}
              </button>
            );
          })}
        </div>
      );
    }

    if (dim.input_type === 'skills') {
      const inputSkills = mustHave.value || [];
      return (
        <div>
          <div className="flex flex-wrap gap-1.5 mb-2">
            {inputSkills.map((skill: string) => (
              <span key={skill} className="px-2.5 py-1 rounded-full text-xs font-medium bg-teal-50 text-teal-700 flex items-center gap-1">
                {skill}
                <button onClick={() => updateMustHaveValue(mustHave.field, inputSkills.filter((s: string) => s !== skill))} className="text-teal-400 hover:text-teal-600">×</button>
              </span>
            ))}
          </div>
          <select
            onChange={e => {
              if (e.target.value && !inputSkills.includes(e.target.value)) {
                updateMustHaveValue(mustHave.field, [...inputSkills, e.target.value]);
              }
              e.target.value = '';
            }}
            className="px-3 py-1.5 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">+ Add a skill</option>
            {COMMON_SKILLS.filter(s => !inputSkills.includes(s)).map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      );
    }

    return null;
  }

  if (authLoading || loading) {
    return (
      <AppShell>
        <div className="max-w-3xl mx-auto">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-slate-200 border-t-teal-500 mx-auto mt-20" />
        </div>
      </AppShell>
    );
  }

  const availableDimensions = dimensions.filter(d => !mustHaves.some(m => m.field === d.field));

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">What matters most to you?</h1>
          <p className="text-sm text-slate-500 mt-1">
            Pick up to 5 must-haves. We&apos;ll only show you jobs that meet <strong>all</strong> of them — no fluff, no guessing.
          </p>
        </div>

        {/* Current must-haves */}
        {mustHaves.length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-900">Your must-haves ({mustHaves.length}/5)</h2>
              <span className="text-xs text-slate-500">Drag to reorder importance</span>
            </div>
            <div className="space-y-3">
              {mustHaves.map((mh, i) => {
                const dim = dimensions.find(d => d.field === mh.field);
                const weight = weights.find(w => w.field === mh.field)?.weight || 1;
                return (
                  <div key={mh.field} className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-navy-900 text-white text-xs font-semibold flex items-center justify-center">{i + 1}</span>
                        <div>
                          <p className="text-sm font-medium text-slate-900">{dim?.label}</p>
                          <p className="text-xs text-slate-500">{dim?.description}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => removeMustHave(mh.field)}
                        className="text-slate-400 hover:text-red-600 transition-colors p-1"
                        aria-label="Remove"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                      </button>
                    </div>
                    <div className="ml-8 mb-2">
                      {renderValueInput(mh)}
                    </div>
                    <div className="ml-8 flex items-center gap-2">
                      <span className="text-xs text-slate-500">Importance:</span>
                      <div className="flex gap-1">
                        {[1, 2, 3, 4, 5].map(n => (
                          <button
                            key={n}
                            onClick={() => updateWeight(mh.field, n)}
                            className={`w-6 h-6 rounded text-xs font-medium transition-colors ${n <= weight ? 'bg-teal-500 text-white' : 'bg-slate-100 text-slate-400 hover:bg-slate-200'}`}
                          >
                            {n}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="mt-4 flex gap-3">
              <button
                onClick={save}
                disabled={saving}
                className="flex-1 px-4 py-2.5 bg-teal-500 text-white rounded-lg font-semibold text-sm hover:bg-teal-600 transition-colors disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save must-haves'}
              </button>
              <button
                onClick={runMatch}
                disabled={matching || mustHaves.length === 0}
                className="flex-1 px-4 py-2.5 bg-navy-900 text-white rounded-lg font-semibold text-sm hover:bg-navy-800 transition-colors disabled:opacity-50"
              >
                {matching ? 'Matching...' : 'See matching jobs'}
              </button>
            </div>
          </div>
        )}

        {/* Available dimensions to add */}
        {mustHaves.length < 5 && availableDimensions.length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h2 className="text-sm font-semibold text-slate-900 mb-3">Add a must-have</h2>
            <div className="grid grid-cols-2 gap-2">
              {availableDimensions.map(dim => (
                <button
                  key={dim.field}
                  onClick={() => addMustHave(dim.field)}
                  className="p-3 rounded-lg border border-slate-200 hover:border-teal-400 hover:bg-teal-50/30 transition-all text-left"
                >
                  <p className="text-sm font-medium text-slate-900">{dim.label}</p>
                  <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{dim.description}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Match results */}
        {matchResults && (
          <div className="mt-5 bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-900">1:1 Match Results</h2>
              <span className="text-xs text-slate-500">{matchResults.total} of {matchResults.total_before_filter} jobs</span>
            </div>
            {matchResults.total === 0 ? (
              <div className="text-center py-8">
                <p className="text-sm text-slate-600 mb-2">No jobs meet all your must-haves.</p>
                <p className="text-xs text-slate-500">Try removing a must-have or running a new search with broader preferences.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {matchResults.jobs.slice(0, 5).map((job: any) => (
                  <div key={job.id} className="p-3 rounded-lg border border-slate-200 bg-slate-50/50">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <p className="text-sm font-medium text-slate-900">{job.title}</p>
                        <p className="text-xs text-slate-500">{job.company}</p>
                      </div>
                      <span className="text-xs font-semibold text-teal-600 bg-teal-50 px-2 py-1 rounded">
                        {job.match_score}/100
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {job.match_breakdown.map((b: any, i: number) => (
                        <span
                          key={i}
                          className={`text-xs px-2 py-0.5 rounded flex items-center gap-1 ${b.met ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-600'}`}
                        >
                          {b.met ? '✓' : '✗'} {b.label}: {b.job_value}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
                {matchResults.total > 5 && (
                  <button
                    onClick={() => router.push('/dashboard')}
                    className="w-full py-2 text-sm text-teal-600 hover:text-teal-700 font-medium"
                  >
                    See all {matchResults.total} matching jobs on dashboard →
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {mustHaves.length === 0 && (
          <div className="bg-teal-50/50 rounded-xl border border-teal-100 p-6 text-center">
            <p className="text-sm text-slate-600 mb-1">👆 Pick what matters most to you above.</p>
            <p className="text-xs text-slate-500">Salary, remote, skills, visa sponsorship, seniority, location — choose up to 5 and we&apos;ll only show jobs that match all of them.</p>
          </div>
        )}
      </div>
    </AppShell>
  );
}