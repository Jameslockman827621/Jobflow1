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
  const [autoApprove, setAutoApprove] = useState(false);
  const [autoApproveThreshold, setAutoApproveThreshold] = useState(60);
  const [autoSubmit, setAutoSubmit] = useState(false);

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
      const [ansRes, approveRes, submitRes] = await Promise.all([
        authFetch('/api/v1/auto-apply/answers'),
        authFetch('/api/v1/auto-apply/auto-approve'),
        authFetch('/api/v1/auto-apply/auto-submit'),
      ]);
      if (ansRes.ok) {
        const data = await ansRes.json();
        setAnswers(data.answers || {});
        setProfile(data.profile || {});
      }
      if (approveRes.ok) {
        const data = await approveRes.json();
        setAutoApprove(data.auto_approve_enabled || false);
        setAutoApproveThreshold(data.auto_approve_threshold || 60);
      }
      if (submitRes.ok) {
        const data = await submitRes.json();
        setAutoSubmit(data.auto_submit_enabled || false);
      }
    } catch (err) {
      console.error('Failed to load settings:', err);
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

        {/* Autonomous settings */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 mb-5">
          <h2 className="text-sm font-semibold text-slate-900 mb-1">Autonomous apply settings</h2>
          <p className="text-xs text-slate-500 mb-4">Control how much you want JobScale to do for you.</p>

          {/* Auto-approve */}
          <div className="border-t border-slate-100 pt-4 mt-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-slate-900">Auto-approve matching jobs</p>
                <p className="text-xs text-slate-500 mt-0.5">When the background monitor finds jobs matching your must-haves, automatically add them to your apply queue (with tailored CVs) — no manual selection needed.</p>
              </div>
              <label className="flex items-center gap-2 cursor-pointer flex-shrink-0">
                <input
                  type="checkbox"
                  checked={autoApprove}
                  onChange={async (e) => {
                    setAutoApprove(e.target.checked);
                    try {
                      await authFetch('/api/v1/auto-apply/auto-approve', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ enabled: e.target.checked, threshold: autoApproveThreshold }),
                      });
                      toast.success(e.target.checked ? 'Auto-approve enabled' : 'Auto-approve disabled');
                    } catch {
                      toast.error('Failed to update');
                    }
                  }}
                  className="w-5 h-5 rounded text-teal-500 focus:ring-teal-500"
                />
              </label>
            </div>
            {autoApprove && (
              <div className="mt-3 flex items-center gap-3">
                <span className="text-xs text-slate-500">Min ATS score to auto-approve:</span>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={autoApproveThreshold}
                  onChange={(e) => setAutoApproveThreshold(parseInt(e.target.value))}
                  className="flex-1 max-w-xs"
                />
                <span className="text-sm font-semibold text-teal-600 w-12">{autoApproveThreshold}%</span>
                <button
                  onClick={async () => {
                    await authFetch('/api/v1/auto-apply/auto-approve', {
                      method: 'PUT',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ enabled: true, threshold: autoApproveThreshold }),
                    });
                    toast.success(`Threshold set to ${autoApproveThreshold}%`);
                  }}
                  className="text-xs px-2 py-1 bg-teal-500 text-white rounded font-medium"
                >
                  Save
                </button>
              </div>
            )}
          </div>

          {/* Auto-submit */}
          <div className="border-t border-slate-100 pt-4 mt-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-slate-900">Auto-submit applications</p>
                <p className="text-xs text-slate-500 mt-0.5">When enabled, the Chrome extension will click Submit after filling each form — you do not need to review each one. Use with caution: you are responsible for the applications submitted on your behalf.</p>
              </div>
              <label className="flex items-center gap-2 cursor-pointer flex-shrink-0">
                <input
                  type="checkbox"
                  checked={autoSubmit}
                  onChange={async (e) => {
                    setAutoSubmit(e.target.checked);
                    try {
                      await authFetch('/api/v1/auto-apply/auto-submit', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ enabled: e.target.checked }),
                      });
                      toast.success(e.target.checked ? 'Auto-submit enabled — the extension will click Submit for you' : 'Auto-submit disabled');
                    } catch {
                      toast.error('Failed to update');
                    }
                  }}
                  className="w-5 h-5 rounded text-teal-500 focus:ring-teal-500"
                />
              </label>
            </div>
          </div>
        </div>

        <p className="text-xs text-slate-400 mt-4 text-center">
          With both auto-approve and auto-submit enabled, JobScale is fully autonomous: it finds jobs, tailors your CV, fills the form, and submits — all you do is click &quot;Start autonomous session&quot; once.
        </p>
      </div>
    </AppShell>
  );
}