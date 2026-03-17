'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toast';

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
        toast.success('Updated! We\'ll find you higher-paying opportunities.');
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white shadow-sm sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-slate-900">Career Growth</h1>
            <button onClick={() => router.push('/dashboard')} className="text-sm text-slate-600 hover:text-navy-900">Back to Dashboard</button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Employment Setup */}
        {(!prefs?.current_salary || prefs.current_salary === 0) && (
          <div className="bg-gradient-to-r from-emerald-500 to-teal-600 rounded-2xl p-8 text-white mb-8">
            <h2 className="text-2xl font-bold mb-2">Never miss a raise</h2>
            <p className="opacity-90 mb-6">Tell us your current salary and we&apos;ll alert you when we find better-paying opportunities.</p>
            <div className="flex flex-col sm:flex-row gap-4 items-end">
              <div className="flex-1">
                <label className="block text-sm font-medium mb-1 opacity-90">Current Annual Salary</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600 text-lg">&pound;</span>
                  <input type="number" value={salary} onChange={(e) => setSalary(e.target.value)} placeholder="65000" className="w-full pl-8 pr-4 py-3 rounded-lg text-slate-900 border-0 focus:ring-2 focus:ring-emerald-300" />
                </div>
              </div>
              <label className="flex items-center space-x-2 cursor-pointer bg-white/20 px-4 py-3 rounded-lg">
                <input type="checkbox" checked={isEmployed} onChange={(e) => setIsEmployed(e.target.checked)} className="w-5 h-5 rounded" />
                <span className="text-sm font-medium">Currently employed</span>
              </label>
              <button onClick={saveEmployment} disabled={saving} className="px-6 py-3 bg-white text-emerald-700 rounded-lg font-semibold hover:bg-emerald-50 disabled:opacity-50">
                {saving ? 'Saving...' : 'Start Tracking'}
              </button>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex space-x-1 bg-white rounded-xl shadow-sm p-1 mb-6">
          {[
            { id: 'upgrades' as const, label: 'Salary Upgrades', icon: '💰' },
            { id: 'report' as const, label: 'Career Report', icon: '📊' },
            { id: 'settings' as const, label: 'Alert Settings', icon: '⚙️' },
          ].map((t) => (
            <button key={t.id} onClick={() => setTab(t.id)} className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-colors ${tab === t.id ? 'bg-teal-500 text-white' : 'text-slate-600 hover:bg-slate-50'}`}>
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {/* Upgrades Tab */}
        {tab === 'upgrades' && (
          <div className="space-y-4">
            {upgrades.length === 0 ? (
              <div className="bg-white rounded-2xl shadow-sm p-8 text-center">
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-3xl">💰</span>
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">No salary upgrades found yet</h3>
                <p className="text-slate-600 mb-4">{prefs?.current_salary ? 'We\'ll alert you when we find higher-paying opportunities.' : 'Set your current salary above to start tracking upgrades.'}</p>
              </div>
            ) : (
              upgrades.map((u, i) => (
                <div key={i} className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900">{u.title}</h3>
                      <p className="text-slate-600 text-sm">{u.company} &bull; {u.location}</p>
                      {u.match_score > 0 && <p className="text-xs text-teal-600 mt-1">{u.match_score}% match</p>}
                    </div>
                    <div className="text-right">
                      <div className="text-emerald-600 font-bold text-lg">+&pound;{u.salary_increase?.toLocaleString()}</div>
                      <div className="text-sm text-slate-500">+{u.salary_increase_pct}%</div>
                    </div>
                  </div>
                  {u.external_url && (
                    <a href={u.external_url} target="_blank" rel="noopener noreferrer" className="inline-block mt-3 text-sm text-teal-600 font-medium hover:text-teal-700">View &amp; Apply &rarr;</a>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* Report Tab */}
        {tab === 'report' && report && (
          <div className="space-y-6">
            <div className="grid sm:grid-cols-3 gap-4">
              <div className="bg-white rounded-xl shadow-sm p-6 text-center">
                <div className="text-3xl font-bold text-slate-900">&pound;{(report.current_salary || 0).toLocaleString()}</div>
                <div className="text-sm text-slate-600 mt-1">Current Salary</div>
              </div>
              <div className="bg-white rounded-xl shadow-sm p-6 text-center">
                <div className="text-3xl font-bold text-emerald-600">&pound;{(report.market_average || 0).toLocaleString()}</div>
                <div className="text-sm text-slate-600 mt-1">Market Average</div>
              </div>
              <div className="bg-white rounded-xl shadow-sm p-6 text-center">
                <div className="text-3xl font-bold text-blue-600">{report.percentile || 0}th</div>
                <div className="text-sm text-slate-600 mt-1">Percentile</div>
              </div>
            </div>

            {report.career_stats && (
              <div className="bg-white rounded-2xl shadow-sm p-6">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Career Stats</h3>
                <div className="grid sm:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-slate-50 rounded-xl">
                    <div className="text-2xl font-bold text-slate-900">{report.career_stats.total_applications}</div>
                    <div className="text-xs text-slate-600">Applications</div>
                  </div>
                  <div className="text-center p-4 bg-slate-50 rounded-xl">
                    <div className="text-2xl font-bold text-slate-900">{report.career_stats.interviews}</div>
                    <div className="text-xs text-slate-600">Interviews</div>
                  </div>
                  <div className="text-center p-4 bg-slate-50 rounded-xl">
                    <div className="text-2xl font-bold text-slate-900">{report.career_stats.offers}</div>
                    <div className="text-xs text-slate-600">Offers</div>
                  </div>
                  <div className="text-center p-4 bg-slate-50 rounded-xl">
                    <div className="text-2xl font-bold text-slate-900">{report.career_stats.interview_rate}%</div>
                    <div className="text-xs text-slate-600">Interview Rate</div>
                  </div>
                </div>
              </div>
            )}

            {report.recommendations && (
              <div className="bg-white rounded-2xl shadow-sm p-6">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Recommendations</h3>
                <ul className="space-y-3">
                  {report.recommendations.map((rec: string, i: number) => (
                    <li key={i} className="flex items-start space-x-3">
                      <span className="text-teal-500 mt-0.5">&#x2713;</span>
                      <span className="text-slate-700 text-sm">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {report.subscription && !report.subscription.is_premium && (
              <div className="bg-gradient-to-r from-violet-500 to-purple-600 rounded-2xl p-8 text-white text-center">
                <h3 className="text-xl font-bold mb-2">Unlock Full Career Report</h3>
                <p className="opacity-90 mb-4">Get detailed salary analysis, market trends, and personalized growth plans.</p>
                <ul className="text-sm space-y-1 mb-6 opacity-90">
                  {report.subscription.upgrade_benefits?.map((b: string, i: number) => (
                    <li key={i}>&#x2713; {b}</li>
                  ))}
                </ul>
                <button onClick={() => router.push('/pricing')} className="px-8 py-3 bg-white text-purple-700 rounded-lg font-semibold hover:bg-purple-50">
                  Upgrade to Pro
                </button>
              </div>
            )}
          </div>
        )}

        {/* Settings Tab */}
        {tab === 'settings' && (
          <div className="bg-white rounded-2xl shadow-sm p-8">
            <h3 className="text-xl font-semibold text-slate-900 mb-6">Alert Settings</h3>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-3">Email Alert Frequency</label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { value: 'daily', label: 'Daily', desc: 'Get alerts every morning' },
                    { value: 'weekly', label: 'Weekly', desc: 'Monday morning digest' },
                    { value: 'off', label: 'Off', desc: 'No email alerts' },
                  ].map((opt) => (
                    <button key={opt.value} onClick={() => updateFrequency(opt.value)}
                      className={`p-4 rounded-xl border-2 transition-all text-left ${prefs?.alert_frequency === opt.value ? 'border-teal-500 bg-teal-50' : 'border-slate-200 hover:border-slate-300'}`}>
                      <div className="font-medium text-slate-900 text-sm">{opt.label}</div>
                      <div className="text-xs text-slate-500 mt-1">{opt.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Current Salary</label>
                <div className="flex gap-3">
                  <div className="relative flex-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">&pound;</span>
                    <input type="number" value={salary} onChange={(e) => setSalary(e.target.value)} className="w-full pl-8 pr-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="65000" />
                  </div>
                  <button onClick={saveEmployment} disabled={saving} className="px-6 py-3 bg-teal-500 text-white rounded-lg font-medium hover:bg-teal-600 disabled:opacity-50">
                    {saving ? 'Saving...' : 'Update'}
                  </button>
                </div>
              </div>

              <div>
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input type="checkbox" checked={isEmployed} onChange={(e) => { setIsEmployed(e.target.checked); }} className="w-5 h-5 text-teal-500 rounded" />
                  <div>
                    <span className="text-sm font-medium text-slate-900">Currently employed</span>
                    <p className="text-xs text-slate-500">We&apos;ll focus on finding you better opportunities</p>
                  </div>
                </label>
              </div>

              <div className="pt-4 border-t border-slate-200">
                <button onClick={sendTestAlert} className="px-4 py-2 text-sm text-teal-600 hover:bg-teal-50 rounded-lg font-medium">
                  Send Test Alert Email
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
