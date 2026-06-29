'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toast';
import AppShell from '@/components/AppShell';

const COMMON_QUESTIONS = [
  { key: 'work_authorization', label: 'Are you authorized to work in the country?', placeholder: 'e.g. Yes, I am authorized to work in the UK' },
  { key: 'requires_sponsorship', label: 'Do you require visa sponsorship?', placeholder: 'e.g. No, I do not require sponsorship' },
  { key: 'willing_to_relocate', label: 'Are you willing to relocate?', placeholder: 'e.g. Yes, I am open to relocating' },
  { key: 'years_of_experience', label: 'Years of relevant experience', placeholder: 'e.g. 6' },
  { key: 'earliest_start', label: 'Earliest start date', placeholder: 'e.g. 2 weeks notice' },
  { key: 'salary_expectation', label: 'Salary expectation', placeholder: 'e.g. £80,000 - £100,000' },
  { key: 'why_this_company', label: 'Default "Why this company?" answer', placeholder: 'A short generic answer you can customize per application' },
];

export default function ApplySettingsPage() {
  const router = useRouter();
  const { authFetch, user, loading: authLoading } = useAuth();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [profile, setProfile] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login?next=/apply-settings');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) loadAnswers();
  }, [user]);

  async function loadAnswers() {
    try {
      const res = await authFetch('/api/v1/auto-apply/answers');
      if (res.ok) {
        const data = await res.json();
        setAnswers(data.answers || {});
        setProfile(data.profile || {});
      }
    } catch (err) {
      console.error('Failed to load answers:', err);
    } finally {
      setLoading(false);
    }
  }

  async function save() {
    setSaving(true);
    try {
      const res = await authFetch('/api/v1/auto-apply/answers', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers, profile }),
      });
      if (res.ok) {
        toast.success('Saved! The extension will auto-fill these on application forms.');
      } else {
        throw new Error('Save failed');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  }

  if (authLoading || loading) {
    return (
      <AppShell>
        <div className="max-w-2xl mx-auto">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-slate-200 border-t-teal-500 mx-auto mt-20" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">Auto-Fill Settings</h1>
          <p className="text-sm text-slate-500 mt-1">Save these once — the extension reuses them on every application form.</p>
        </div>

        {/* Profile section */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5">
          <h2 className="text-sm font-semibold text-slate-900 mb-4">Your links (auto-filled on every form)</h2>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">LinkedIn URL</label>
              <input
                type="url"
                value={profile.linkedin_url || ''}
                onChange={e => setProfile({ ...profile, linkedin_url: e.target.value })}
                placeholder="https://linkedin.com/in/yourname"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">GitHub URL</label>
              <input
                type="url"
                value={profile.github_url || ''}
                onChange={e => setProfile({ ...profile, github_url: e.target.value })}
                placeholder="https://github.com/yourname"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Personal website / portfolio</label>
              <input
                type="url"
                value={profile.website || ''}
                onChange={e => setProfile({ ...profile, website: e.target.value })}
                placeholder="https://yourname.dev"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
          </div>
        </div>

        {/* Common questions */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5">
          <h2 className="text-sm font-semibold text-slate-900 mb-1">Common application questions</h2>
          <p className="text-xs text-slate-500 mb-4">These get auto-filled on Greenhouse/Lever/Ashby forms. You can edit them per-application if needed.</p>
          <div className="space-y-4">
            {COMMON_QUESTIONS.map(q => (
              <div key={q.key}>
                <label className="block text-xs font-medium text-slate-700 mb-1">{q.label}</label>
                <textarea
                  value={answers[q.key] || ''}
                  onChange={e => setAnswers({ ...answers, [q.key]: e.target.value })}
                  placeholder={q.placeholder}
                  rows={q.key === 'why_this_company' ? 3 : 1}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none"
                />
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={save}
          disabled={saving}
          className="w-full px-6 py-3 bg-teal-500 hover:bg-teal-600 text-white rounded-lg font-semibold transition-colors disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save auto-fill answers'}
        </button>

        <p className="text-xs text-slate-400 mt-4 text-center">
          We never submit applications for you — these just save you typing the same answers on every form.
        </p>
      </div>
    </AppShell>
  );
}