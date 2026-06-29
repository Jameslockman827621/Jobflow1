'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toast';

const SUGGESTED_ROLES = [
  'Software Engineer', 'Senior Software Engineer', 'Frontend Developer',
  'Backend Developer', 'Full Stack Developer', 'Python Developer',
  'React Developer', 'DevOps Engineer', 'Data Engineer', 'Data Scientist',
  'Machine Learning Engineer', 'AI Engineer', 'Product Manager', 'Product Designer',
  'Site Reliability Engineer', 'Staff Engineer', 'Mobile Developer', 'iOS Developer',
  'Android Developer', 'Engineering Manager',
];

const SUGGESTED_COMPANIES = [
  'Stripe', 'Monzo', 'Notion', 'Linear', 'Vercel', 'Supabase', 'GitLab',
  'Airbnb', 'Figma', 'Anthropic', 'OpenAI', 'Datadog', 'Shopify', 'Coinbase',
  'Mercury', 'Ramp', 'Brex', 'Plaid', 'Wise', 'Klarna',
];

type Step = 'upload' | 'roles' | 'searching' | 'done';

export default function QuickStartPage() {
  const router = useRouter();
  const { user, loading: authLoading, authFetch } = useAuth();
  const toast = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [step, setStep] = useState<Step>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);
  const [seniority, setSeniority] = useState<string>('mid');
  const [remotePreference, setRemotePreference] = useState<string>('any');
  const [submitting, setSubmitting] = useState(false);
  const [searchProgress, setSearchProgress] = useState<string>('');
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login?next=/quick-start');
    }
  }, [user, authLoading, router]);

  function handleFileDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  }

  function validateAndSetFile(f: File) {
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const validExts = ['pdf', 'docx', 'txt'];
    const ext = f.name.split('.').pop()?.toLowerCase() || '';
    if (!validTypes.includes(f.type) && !validExts.includes(ext)) {
      toast.error('Please upload a PDF, DOCX, or TXT file');
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      toast.error('File too large (max 10MB)');
      return;
    }
    setFile(f);
    toast.success('CV uploaded — looks good!');
  }

  function toggleRole(role: string) {
    setSelectedRoles(prev =>
      prev.includes(role) ? prev.filter(r => r !== role) : prev.length < 5 ? [...prev, role] : prev
    );
  }

  function toggleCompany(company: string) {
    setSelectedCompanies(prev =>
      prev.includes(company) ? prev.filter(c => c !== company) : prev.length < 8 ? [...prev, company] : prev
    );
  }

  async function handleQuickStart() {
    if (!file) {
      toast.error('Please upload your CV first');
      return;
    }
    if (selectedRoles.length === 0) {
      toast.error("Pick at least one role you are interested in");
      return;
    }
    setSubmitting(true);
    setStep('searching');
    setSearchProgress('Uploading & parsing your CV...');

    // Animate the progress messages while the request runs
    const progressInterval = setInterval(() => {
      setSearchProgress(prev => {
        if (prev.includes('Uploading')) return 'Extracting your skills and experience...';
        if (prev.includes('Extracting')) return 'Saving your job preferences...';
        if (prev.includes('Saving')) return 'Searching 15 job sources in parallel...';
        if (prev.includes('Searching')) return 'Ranking jobs by match score...';
        return prev;
      });
    }, 1500);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('target_roles', JSON.stringify(selectedRoles));
      formData.append('seniority_levels', JSON.stringify([seniority]));
      formData.append('remote_preference', remotePreference);
      formData.append('employment_types', JSON.stringify(['fulltime']));
      if (selectedCompanies.length > 0) {
        formData.append('target_companies', JSON.stringify(selectedCompanies));
      }

      const res = await authFetch('/api/v1/onboarding/quick-start', {
        method: 'POST',
        body: formData as any,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Quick start failed');
      }

      const data = await res.json();
      setResult(data);
      setStep('done');
      toast.success(`CV parsed! Found ${data.total_jobs} matching jobs.`);
    } catch (err: any) {
      toast.error(err.message || 'Something went wrong');
      setStep('roles');
    } finally {
      clearInterval(progressInterval);
      setSubmitting(false);
    }
  }

  function goToDashboard() {
    router.push('/dashboard');
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-slate-200 border-t-teal-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-teal-50/30 flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-navy-900 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
            </div>
            <span className="font-bold text-navy-900">JobScale</span>
          </div>
          <span className="text-xs text-slate-500 hidden sm:block">60-second setup</span>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-xl">
          {/* Progress dots */}
          <div className="flex items-center justify-center gap-2 mb-8">
            {['upload', 'roles', 'searching', 'done'].map((s, i) => {
              const stepOrder = ['upload', 'roles', 'searching', 'done'];
              const currentIdx = stepOrder.indexOf(step);
              const isActive = i <= currentIdx;
              return (
                <div key={s} className={`h-1.5 rounded-full transition-all ${isActive ? 'bg-teal-500 w-8' : 'bg-slate-200 w-4'}`} />
              );
            })}
          </div>

          {/* Step 1: Upload */}
          {step === 'upload' && (
            <div className="text-center">
              <h1 className="text-3xl sm:text-4xl font-bold text-navy-900 mb-3 tracking-tight">
                Upload your CV.<br />We will handle the rest.
              </h1>
              <p className="text-slate-600 mb-8 max-w-md mx-auto">
                For every job you apply to, we auto-tailor your CV to pass AI screening and highlight your most relevant skills.
              </p>

              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleFileDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-12 cursor-pointer transition-all ${dragOver ? 'border-teal-500 bg-teal-50' : 'border-slate-300 hover:border-teal-400 hover:bg-slate-50'}`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && validateAndSetFile(e.target.files[0])}
                />
                {file ? (
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-14 h-14 rounded-xl bg-teal-500 flex items-center justify-center">
                      <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
                    </div>
                    <div>
                      <p className="font-medium text-navy-900">{file.name}</p>
                      <p className="text-sm text-slate-500 mt-0.5">{(file.size / 1024).toFixed(0)} KB · Click to replace</p>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-14 h-14 rounded-xl bg-slate-100 flex items-center justify-center">
                      <svg className="w-7 h-7 text-slate-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" /></svg>
                    </div>
                    <div>
                      <p className="font-medium text-navy-900">Drop your CV here</p>
                      <p className="text-sm text-slate-500 mt-0.5">or click to browse · PDF, DOCX, or TXT</p>
                    </div>
                  </div>
                )}
              </div>

              {file && (
                <button
                  onClick={() => setStep('roles')}
                  className="mt-6 px-6 py-3 bg-navy-900 text-white rounded-lg font-semibold hover:bg-navy-800 transition-colors"
                >
                  Continue →
                </button>
              )}

              <p className="text-xs text-slate-400 mt-6">We parse your CV locally — your data stays private.</p>
            </div>
          )}

          {/* Step 2: Pick roles */}
          {step === 'roles' && (
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-navy-900 mb-3 tracking-tight text-center">
                What roles are you after?
              </h1>
              <p className="text-slate-600 mb-8 text-center max-w-md mx-auto">
                Pick up to 5 roles. We will search 15 job boards and company career pages in parallel.
              </p>

              <div className="mb-6">
                <label className="block text-xs font-medium text-slate-700 mb-2 uppercase tracking-wide">Roles you want</label>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTED_ROLES.map(role => {
                    const selected = selectedRoles.includes(role);
                    return (
                      <button
                        key={role}
                        onClick={() => toggleRole(role)}
                        className={`px-3.5 py-2 rounded-full text-sm font-medium transition-all ${selected ? 'bg-teal-500 text-white shadow-sm' : 'bg-white text-slate-700 border border-slate-200 hover:border-teal-400'}`}
                      >
                        {selected && <span className="mr-1">✓</span>}
                        {role}
                      </button>
                    );
                  })}
                </div>
                <p className="text-xs text-slate-400 mt-2">{selectedRoles.length}/5 selected</p>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-2 uppercase tracking-wide">Seniority</label>
                  <select
                    value={seniority}
                    onChange={(e) => setSeniority(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="entry">Entry level</option>
                    <option value="mid">Mid level</option>
                    <option value="senior">Senior</option>
                    <option value="lead">Lead / Staff</option>
                    <option value="director">Director+</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-2 uppercase tracking-wide">Remote preference</label>
                  <select
                    value={remotePreference}
                    onChange={(e) => setRemotePreference(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="any">Open to anything</option>
                    <option value="remote_only">Remote only</option>
                    <option value="hybrid_ok">Hybrid OK</option>
                    <option value="onsite_only">Onsite only</option>
                  </select>
                </div>
              </div>

              <div className="mb-6">
                <label className="block text-xs font-medium text-slate-700 mb-2 uppercase tracking-wide">Target companies (optional)</label>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTED_COMPANIES.map(company => {
                    const selected = selectedCompanies.includes(company);
                    return (
                      <button
                        key={company}
                        onClick={() => toggleCompany(company)}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${selected ? 'bg-navy-900 text-white' : 'bg-white text-slate-700 border border-slate-200 hover:border-navy-400'}`}
                      >
                        {selected && <span className="mr-1">✓</span>}
                        {company}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="flex items-center justify-between gap-3">
                <button
                  onClick={() => setStep('upload')}
                  className="px-4 py-2.5 text-slate-600 hover:text-navy-900 text-sm font-medium transition-colors"
                >
                  ← Back
                </button>
                <button
                  onClick={handleQuickStart}
                  disabled={selectedRoles.length === 0 || submitting}
                  className="flex-1 px-6 py-3 bg-teal-500 text-white rounded-lg font-semibold hover:bg-teal-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Find my jobs →
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Searching */}
          {step === 'searching' && (
            <div className="text-center py-12">
              <div className="relative w-20 h-20 mx-auto mb-6">
                <div className="absolute inset-0 rounded-full border-4 border-slate-100" />
                <div className="absolute inset-0 rounded-full border-4 border-teal-500 border-t-transparent animate-spin" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl">🎯</span>
                </div>
              </div>
              <h2 className="text-2xl font-bold text-navy-900 mb-2">Finding your jobs</h2>
              <p className="text-slate-600 mb-6">{searchProgress}</p>
              <div className="space-y-2 text-sm text-slate-500 max-w-xs mx-auto text-left">
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse" />
                  <span>Greenhouse · Lever · Ashby · Workable</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse" />
                  <span>LinkedIn · Indeed · Otta · BuiltIn</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse" />
                  <span>RemoteOK · WeWorkRemotely · Remotive · Himalayas</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse" />
                  <span>Google Jobs · Direct career pages</span>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Done */}
          {step === 'done' && result && (
            <div className="text-center">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center mx-auto mb-6 shadow-lg">
                <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" /></svg>
              </div>
              <h1 className="text-3xl sm:text-4xl font-bold text-navy-900 mb-3 tracking-tight">
                You are all set! 🎉
              </h1>
              <p className="text-slate-600 mb-8 max-w-md mx-auto">
                We parsed your CV, extracted <strong className="text-navy-900">{result.cv?.skills?.length || 0} skills</strong>, and found <strong className="text-teal-600">{result.total_jobs} matching jobs</strong> across {Object.keys(result.sources_used || {}).filter(k => result.sources_used[k] > 0).length} sources.
              </p>

              {result.cv?.skills && result.cv.skills.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 p-4 mb-6 max-w-md mx-auto">
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Skills we found in your CV</p>
                  <div className="flex flex-wrap gap-1.5">
                    {result.cv.skills.slice(0, 12).map((skill: string) => (
                      <span key={skill} className="px-2.5 py-1 bg-teal-50 text-teal-700 rounded-full text-xs font-medium">{skill}</span>
                    ))}
                    {result.cv.skills.length > 12 && (
                      <span className="px-2.5 py-1 bg-slate-100 text-slate-600 rounded-full text-xs">+{result.cv.skills.length - 12} more</span>
                    )}
                  </div>
                </div>
              )}

              <button
                onClick={goToDashboard}
                className="px-8 py-3 bg-navy-900 text-white rounded-lg font-semibold hover:bg-navy-800 transition-colors text-base"
              >
                See my matched jobs →
              </button>

              {/* Next steps guidance */}
              <div className="mt-8 max-w-md mx-auto bg-slate-50 rounded-xl p-4 text-left">
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3 text-center">What happens next</p>
                <div className="space-y-2.5">
                  <div className="flex items-start gap-2.5">
                    <div className="w-5 h-5 rounded-full bg-teal-500 text-white text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">1</div>
                    <p className="text-xs text-slate-600">Check the jobs you like on your dashboard</p>
                  </div>
                  <div className="flex items-start gap-2.5">
                    <div className="w-5 h-5 rounded-full bg-teal-500 text-white text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">2</div>
                    <p className="text-xs text-slate-600">Click &quot;Approve &amp; Tailor CVs&quot; — we create a unique CV for each job</p>
                  </div>
                  <div className="flex items-start gap-2.5">
                    <div className="w-5 h-5 rounded-full bg-teal-500 text-white text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">3</div>
                    <p className="text-xs text-slate-600">Apply from the queue — our Chrome extension auto-fills each form</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}