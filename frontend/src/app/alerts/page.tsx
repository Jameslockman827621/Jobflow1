'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toast';
import AppShell from '@/components/AppShell';

function CurrencyIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
    </svg>
  );
}

function ChartBarIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
    </svg>
  );
}

function CogIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

function ArrowTrendingUpIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
    </svg>
  );
}

function ArrowUpRightIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
    </svg>
  );
}

function CheckCircleIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function BoltIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
    </svg>
  );
}

function SalaryBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-600">{label}</span>
        <span className="text-sm font-semibold text-slate-900">&pound;{value.toLocaleString()}</span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function AlertsPage() {
  const router = useRouter();
  const { user, loading: authLoading, authFetch } = useAuth();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [prefs, setPrefs] = useState<any>(null);
  const [upgrades, setUpgrades] = useState<any[]>([]);
  const [report, setReport] = useState<any>(null);
  const [salary, setSalary] = useState('');
  const [isEmployed, setIsEmployed] = useState(false);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState<'upgrades' | 'report' | 'settings'>('upgrades');

  useEffect(() => {
    if (!authLoading && !user) router.push('/login');
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) loadData();
  }, [user]);

  async function loadData() {
    setLoading(true);
    try {
      const [prefsRes, upgradesRes, reportRes] = await Promise.all([
        authFetch('/api/v1/alerts/preferences'),
        authFetch('/api/v1/alerts/upgrades?min_increase=5'),
        authFetch('/api/v1/alerts/report'),
      ]);
      if (prefsRes.ok) {
        const p = await prefsRes.json();
        setPrefs(p);
        setSalary(p.current_salary?.toString() || '');
        setIsEmployed(p.is_employed || false);
      }
      if (upgradesRes.ok) {
        const u = await upgradesRes.json();
        setUpgrades(u.upgrades || []);
      }
      if (reportRes.ok) {
        const r = await reportRes.json();
        setReport(r);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function saveEmployment() {
    setSaving(true);
    try {
      const res = await authFetch('/api/v1/alerts/employment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_employed: isEmployed, current_salary: parseInt(salary) || 0 }),
      });
      if (res.ok) {
        toast.success('Employment details updated.');
        loadData();
      }
    } catch (err) {
      toast.error('Failed to update');
    } finally {
      setSaving(false);
    }
  }

  async function updateFrequency(freq: string) {
    const res = await authFetch('/api/v1/alerts/preferences', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alert_frequency: freq, email_alerts_enabled: freq !== 'off' }),
    });
    if (res.ok) {
      toast.success(`Alerts set to ${freq}`);
      setPrefs((p: any) => ({ ...p, alert_frequency: freq, email_alerts_enabled: freq !== 'off' }));
    }
  }

  async function sendTestAlert() {
    const res = await authFetch('/api/v1/alerts/send-test-alert', { method: 'POST' });
    if (res.ok) toast.success('Test alert sent! Check console output.');
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-10 w-10 border-2 border-slate-200 border-t-teal-500"></div>
      </div>
    );
  }

  const TABS = [
    { id: 'upgrades' as const, label: 'Salary Upgrades', icon: CurrencyIcon },
    { id: 'report' as const, label: 'Career Report', icon: ChartBarIcon },
    { id: 'settings' as const, label: 'Settings', icon: CogIcon },
  ];

  const salaryMax = Math.max(report?.current_salary || 0, report?.market_average || 0) * 1.15 || 100000;

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-heading-lg text-slate-900">Career Growth</h1>
          <p className="text-body-sm text-slate-500 mt-1">Track salary opportunities and career progress</p>
        </div>

        {(!prefs?.current_salary || prefs.current_salary === 0) && (
          <div className="bg-gradient-to-r from-navy-900 to-slate-800 rounded-lg p-6 mb-6">
            <div className="flex items-start gap-4">
              <div className="w-9 h-9 bg-teal-500/20 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5">
                <ArrowTrendingUpIcon className="w-5 h-5 text-teal-400" />
              </div>
              <div className="flex-1">
                <h2 className="text-base font-semibold text-white mb-1">Track salary opportunities</h2>
                <p className="text-sm text-slate-300 mb-5">Enter your current salary and we will alert you when higher-paying roles matching your profile become available.</p>
                <div className="flex flex-col sm:flex-row gap-3 items-end">
                  <div className="flex-1 w-full">
                    <label className="block text-xs font-medium text-slate-400 mb-1.5">Current Annual Salary</label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">&pound;</span>
                      <input
                        type="number"
                        value={salary}
                        onChange={(e) => setSalary(e.target.value)}
                        placeholder="65000"
                        className="w-full pl-7 pr-4 py-2 rounded-md text-sm text-white bg-white/10 border border-white/20 placeholder-slate-500 focus:border-teal-400 focus:ring-1 focus:ring-teal-400 focus:outline-none"
                      />
                    </div>
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer bg-white/10 border border-white/10 px-3 py-2 rounded-md">
                    <input type="checkbox" checked={isEmployed} onChange={(e) => setIsEmployed(e.target.checked)} className="w-4 h-4 rounded text-teal-500 bg-transparent border-slate-400" />
                    <span className="text-xs font-medium text-slate-300">Currently employed</span>
                  </label>
                  <button
                    onClick={saveEmployment}
                    disabled={saving}
                    className="px-5 py-2 bg-teal-500 text-white rounded-md text-sm font-medium hover:bg-teal-600 disabled:opacity-50 transition-colors whitespace-nowrap"
                  >
                    {saving ? 'Saving...' : 'Start Tracking'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="flex items-center gap-1 bg-white rounded-lg border border-slate-200 shadow-sm p-1 mb-6">
          {TABS.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex-1 inline-flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
                  tab === t.id
                    ? 'bg-navy-900 text-white'
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {t.label}
              </button>
            );
          })}
        </div>

        {tab === 'upgrades' && (
          <div className="space-y-3">
            {upgrades.length === 0 ? (
              <div className="bg-white rounded-lg border border-slate-200 shadow-sm px-6 py-14 text-center">
                <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <CurrencyIcon className="w-6 h-6 text-slate-400" />
                </div>
                <h3 className="text-sm font-semibold text-slate-900 mb-1">No salary upgrades found yet</h3>
                <p className="text-xs text-slate-500 max-w-xs mx-auto">
                  {prefs?.current_salary ? 'We will alert you when higher-paying opportunities are found.' : 'Set your current salary above to start tracking upgrades.'}
                </p>
              </div>
            ) : (
              upgrades.map((u, i) => (
                <div key={i} className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 hover:border-slate-300 transition-colors">
                  <div className="flex justify-between items-start">
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold text-slate-900 truncate">{u.title}</h3>
                      <p className="text-xs text-slate-500 mt-0.5">{u.company} &bull; {u.location}</p>
                      {u.match_score > 0 && (
                        <span className="inline-block mt-1.5 px-2 py-0.5 bg-teal-50 text-teal-700 rounded text-xs font-medium">
                          {u.match_score}% match
                        </span>
                      )}
                    </div>
                    <div className="text-right flex-shrink-0 ml-4">
                      <div className="text-green-600 font-semibold text-sm">+&pound;{u.salary_increase?.toLocaleString()}</div>
                      <div className="text-xs text-slate-400 mt-0.5">+{u.salary_increase_pct}%</div>
                    </div>
                  </div>
                  {u.external_url && (
                    <a
                      href={u.external_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 mt-3 text-xs text-teal-600 font-medium hover:text-teal-700 transition-colors"
                    >
                      View &amp; Apply
                      <ArrowUpRightIcon className="w-3 h-3" />
                    </a>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {tab === 'report' && report && (
          <div className="space-y-4">
            <div className="grid sm:grid-cols-3 gap-3">
              <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 text-center">
                <div className="text-xl font-bold text-slate-900">&pound;{(report.current_salary || 0).toLocaleString()}</div>
                <div className="text-xs text-slate-500 mt-1">Current Salary</div>
              </div>
              <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 text-center">
                <div className="text-xl font-bold text-teal-600">&pound;{(report.market_average || 0).toLocaleString()}</div>
                <div className="text-xs text-slate-500 mt-1">Market Average</div>
              </div>
              <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 text-center">
                <div className="text-xl font-bold text-navy-900">{report.percentile || 0}th</div>
                <div className="text-xs text-slate-500 mt-1">Percentile</div>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5">
              <h3 className="text-sm font-semibold text-slate-900 mb-4">Salary Comparison</h3>
              <div className="space-y-4">
                <SalaryBar label="Your Salary" value={report.current_salary || 0} max={salaryMax} color="bg-slate-700" />
                <SalaryBar label="Market Average" value={report.market_average || 0} max={salaryMax} color="bg-teal-500" />
              </div>
              {(report.current_salary || 0) > 0 && (report.market_average || 0) > 0 && (
                <p className="text-xs text-slate-500 mt-4 pt-3 border-t border-slate-100">
                  {report.current_salary >= report.market_average
                    ? `You are earning ${Math.round(((report.current_salary - report.market_average) / report.market_average) * 100)}% above the market average.`
                    : `You are earning ${Math.round(((report.market_average - report.current_salary) / report.market_average) * 100)}% below the market average.`}
                </p>
              )}
            </div>

            {report.career_stats && (
              <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5">
                <h3 className="text-sm font-semibold text-slate-900 mb-4">Career Stats</h3>
                <div className="grid sm:grid-cols-4 gap-3">
                  <div className="text-center p-3 bg-slate-50 rounded-md">
                    <div className="text-lg font-bold text-slate-900">{report.career_stats.total_applications}</div>
                    <div className="text-xs text-slate-500">Applications</div>
                  </div>
                  <div className="text-center p-3 bg-slate-50 rounded-md">
                    <div className="text-lg font-bold text-slate-900">{report.career_stats.interviews}</div>
                    <div className="text-xs text-slate-500">Interviews</div>
                  </div>
                  <div className="text-center p-3 bg-slate-50 rounded-md">
                    <div className="text-lg font-bold text-slate-900">{report.career_stats.offers}</div>
                    <div className="text-xs text-slate-500">Offers</div>
                  </div>
                  <div className="text-center p-3 bg-slate-50 rounded-md">
                    <div className="text-lg font-bold text-slate-900">{report.career_stats.interview_rate}%</div>
                    <div className="text-xs text-slate-500">Interview Rate</div>
                  </div>
                </div>
              </div>
            )}

            {report.recommendations && (
              <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5">
                <h3 className="text-sm font-semibold text-slate-900 mb-3">Recommendations</h3>
                <ul className="space-y-2.5">
                  {report.recommendations.map((rec: string, i: number) => (
                    <li key={i} className="flex items-start gap-2.5">
                      <CheckCircleIcon className="w-4 h-4 text-teal-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-slate-600">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {report.subscription && !report.subscription.is_premium && (
              <div className="bg-navy-900 rounded-lg p-6">
                <div className="flex items-start gap-4">
                  <div className="w-9 h-9 bg-teal-500/15 rounded-md flex items-center justify-center flex-shrink-0">
                    <BoltIcon className="w-5 h-5 text-teal-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold text-white mb-1">Unlock Full Career Report</h3>
                    <p className="text-xs text-slate-400 mb-3">Get detailed salary analysis, market trends, and personalized growth plans.</p>
                    {report.subscription.upgrade_benefits && (
                      <ul className="space-y-1.5 mb-4">
                        {report.subscription.upgrade_benefits.map((b: string, i: number) => (
                          <li key={i} className="flex items-center gap-2 text-xs text-slate-300">
                            <CheckCircleIcon className="w-3.5 h-3.5 text-teal-400 flex-shrink-0" />
                            {b}
                          </li>
                        ))}
                      </ul>
                    )}
                    <button
                      onClick={() => router.push('/pricing')}
                      className="px-4 py-2 bg-teal-500 text-white rounded-md text-sm font-medium hover:bg-teal-600 transition-colors"
                    >
                      Upgrade to Pro
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {tab === 'settings' && (
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
            <h3 className="text-base font-semibold text-slate-900 mb-5">Alert Settings</h3>

            <div className="space-y-6">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-2.5">Email Alert Frequency</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { value: 'daily', label: 'Daily', desc: 'Get alerts every morning' },
                    { value: 'weekly', label: 'Weekly', desc: 'Monday morning digest' },
                    { value: 'off', label: 'Off', desc: 'No email alerts' },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => updateFrequency(opt.value)}
                      className={`p-3 rounded-md border transition-all text-left ${
                        prefs?.alert_frequency === opt.value
                          ? 'border-teal-500 bg-teal-50'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className="text-sm font-medium text-slate-900">{opt.label}</div>
                      <div className="text-xs text-slate-500 mt-0.5">{opt.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">Current Salary</label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">&pound;</span>
                    <input
                      type="number"
                      value={salary}
                      onChange={(e) => setSalary(e.target.value)}
                      className="w-full pl-7 pr-4 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none"
                      placeholder="65000"
                    />
                  </div>
                  <button
                    onClick={saveEmployment}
                    disabled={saving}
                    className="px-4 py-2 bg-teal-500 text-white rounded-md text-sm font-medium hover:bg-teal-600 disabled:opacity-50 transition-colors"
                  >
                    {saving ? 'Saving...' : 'Update'}
                  </button>
                </div>
              </div>

              <div>
                <label className="flex items-center gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isEmployed}
                    onChange={(e) => { setIsEmployed(e.target.checked); }}
                    className="w-4 h-4 text-teal-500 rounded border-slate-300"
                  />
                  <div>
                    <span className="text-sm font-medium text-slate-900">Currently employed</span>
                    <p className="text-xs text-slate-500">We will focus on finding you better opportunities</p>
                  </div>
                </label>
              </div>

              <div className="pt-4 border-t border-slate-100">
                <button
                  onClick={sendTestAlert}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-teal-600 hover:bg-teal-50 rounded-md font-medium transition-colors"
                >
                  Send test email
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
