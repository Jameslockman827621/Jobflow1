'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toast';
import AppShell from '@/components/AppShell';

interface CV {
  id: number;
  full_name: string;
  email: string;
  phone?: string;
  location?: string;
  linkedin_url?: string;
  summary?: string;
  experience: any[];
  education: any[];
  skills: string[];
  template_id: string;
  is_ai_generated: boolean;
  created_at: string;
}

interface Template {
  id: string;
  name: string;
  description: string;
  is_premium: boolean;
}

type WizardStep = 'list' | 'choice' | 'upload' | 'create' | 'templates' | 'preview';

function DocumentIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  );
}

function CloudUploadIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
    </svg>
  );
}

function PencilSquareIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
    </svg>
  );
}

function PlusIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  );
}

function TrashIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
    </svg>
  );
}

function ArrowLeftIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
    </svg>
  );
}

function XMarkIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

function CheckIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
    </svg>
  );
}

const BREADCRUMB_STEPS = [
  { label: 'Personal', key: 0 },
  { label: 'Experience', key: 1 },
  { label: 'Education', key: 2 },
  { label: 'Skills', key: 3 },
];

export default function CVBuilderPage() {
  const router = useRouter();
  const { user, loading: authLoading, authFetch } = useAuth();
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<WizardStep>('list');
  const [cvs, setCvs] = useState<CV[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState('modern');
  const [previewHtml, setPreviewHtml] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const [cvData, setCvData] = useState({
    full_name: '',
    email: '',
    phone: '',
    location: '',
    linkedin_url: '',
    portfolio_url: '',
    summary: '',
    experience: [{ company: '', role: '', start_date: '', end_date: '', description: '' }],
    education: [{ institution: '', degree: '', field: '', graduation_year: '' }],
    skills: [] as string[],
    template_id: 'modern'
  });

  const [skillInput, setSkillInput] = useState('');
  const [generatingSummary, setGeneratingSummary] = useState(false);
  const [createSection, setCreateSection] = useState(0);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      loadCVs();
      loadTemplates();
      setCvData(prev => ({ ...prev, email: user.email || '' }));
    }
  }, [user]);

  async function loadCVs() {
    try {
      const res = await authFetch('/api/v1/cvs');
      if (res.ok) {
        const data = await res.json();
        setCvs(data.cvs || []);
      }
    } catch (err) {
      console.error('Failed to load CVs:', err);
    }
  }

  async function loadTemplates() {
    try {
      const res = await authFetch('/api/v1/cvs/templates');
      if (res.ok) {
        const data = await res.json();
        setTemplates(data.templates || []);
      }
    } catch (err) {
      console.error('Failed to load templates:', err);
    }
  }

  const handleAddExperience = () => {
    setCvData(prev => ({
      ...prev,
      experience: [...prev.experience, { company: '', role: '', start_date: '', end_date: '', description: '' }]
    }));
  };

  const handleUpdateExperience = (index: number, field: string, value: string) => {
    const updated = cvData.experience.map((exp, i) =>
      i === index ? { ...exp, [field]: value } : exp
    );
    setCvData(prev => ({ ...prev, experience: updated }));
  };

  const handleRemoveExperience = (index: number) => {
    setCvData(prev => ({ ...prev, experience: prev.experience.filter((_, i) => i !== index) }));
  };

  const handleAddEducation = () => {
    setCvData(prev => ({
      ...prev,
      education: [...prev.education, { institution: '', degree: '', field: '', graduation_year: '' }]
    }));
  };

  const handleUpdateEducation = (index: number, field: string, value: string) => {
    const updated = cvData.education.map((edu, i) =>
      i === index ? { ...edu, [field]: value } : edu
    );
    setCvData(prev => ({ ...prev, education: updated }));
  };

  const handleRemoveEducation = (index: number) => {
    setCvData(prev => ({ ...prev, education: prev.education.filter((_, i) => i !== index) }));
  };

  const handleAddSkill = () => {
    if (skillInput.trim() && !cvData.skills.includes(skillInput.trim())) {
      setCvData(prev => ({ ...prev, skills: [...prev.skills, skillInput.trim()] }));
      setSkillInput('');
    }
  };

  const handleRemoveSkill = (skill: string) => {
    setCvData(prev => ({ ...prev, skills: prev.skills.filter(s => s !== skill) }));
  };

  const handleGenerateSummary = async () => {
    if (cvData.skills.length === 0) {
      toast.error('Please add at least one skill first');
      return;
    }
    setGeneratingSummary(true);
    try {
      const res = await authFetch('/api/v1/cvs/generate-summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          experience: cvData.experience,
          skills: cvData.skills,
          target_role: cvData.experience[0]?.role || 'Software Engineer'
        })
      });
      if (res.ok) {
        const data = await res.json();
        setCvData(prev => ({ ...prev, summary: data.summary }));
        toast.success('Summary generated!');
      }
    } catch (err) {
      toast.error('Failed to generate summary');
    } finally {
      setGeneratingSummary(false);
    }
  };

  const handleUploadFile = async (file: File) => {
    if (!file) return;
    const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowed.includes(file.type)) {
      toast.error('Only PDF and DOCX files are allowed');
      return;
    }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await authFetch('/api/v1/cvs/upload', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        toast.success('CV uploaded successfully!');
        await loadCVs();
        setStep('list');
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Upload failed');
      }
    } catch (err) {
      toast.error('Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) {
      handleUploadFile(e.dataTransfer.files[0]);
    }
  };

  const goToTemplates = () => {
    if (!cvData.full_name || !cvData.email) {
      toast.error('Name and email are required');
      return;
    }
    setStep('templates');
  };

  const goToPreview = async (templateId: string) => {
    setSelectedTemplate(templateId);
    setCvData(prev => ({ ...prev, template_id: templateId }));
    setLoading(true);
    try {
      const res = await authFetch('/api/v1/cvs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...cvData, template_id: templateId })
      });
      if (res.ok) {
        const saved = await res.json();
        const previewRes = await authFetch(`/api/v1/cvs/${saved.id}/export?template_id=${templateId}`);
        if (previewRes.ok) {
          const html = await previewRes.text();
          setPreviewHtml(html);
        }
        setCvData(prev => ({ ...prev, template_id: templateId }));
        await loadCVs();
        toast.success('CV saved!');
        setStep('preview');
      }
    } catch (err) {
      toast.error('Failed to save CV');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAndFinish = () => {
    toast.success('CV ready! You can now apply to jobs.');
    router.push('/dashboard');
  };

  if (authLoading || !user) {
    return (
      <AppShell>
        <div className="max-w-4xl mx-auto">
          <div className="mb-6">
            <div className="h-7 w-32 bg-slate-100 rounded animate-pulse" />
            <div className="h-4 w-56 bg-slate-50 rounded mt-2 animate-pulse" />
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-6 animate-pulse">
            <div className="h-5 w-24 bg-slate-100 rounded mb-6" />
            <div className="space-y-4">
              <div className="h-16 bg-slate-50 rounded" />
              <div className="h-16 bg-slate-50 rounded" />
            </div>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">
        {/* Page header */}
        <div className="mb-6">
          <h1 className="text-xl font-semibold text-navy-900 tracking-tight">CV Builder</h1>
          <p className="text-sm text-slate-500 mt-1">Create and manage your professional CVs</p>
        </div>

        {/* CV List */}
        {step === 'list' && (
          <div className="bg-white rounded-lg border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-900">Your CVs</h2>
                {cvs.length > 0 && (
                  <button
                    onClick={() => setStep('choice')}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-teal-500 text-white rounded-md text-xs font-medium hover:bg-teal-600 transition-colors"
                  >
                    <PlusIcon className="w-3.5 h-3.5" />
                    New CV
                  </button>
                )}
              </div>
            </div>

            {cvs.length === 0 ? (
              <div className="px-6 py-16 text-center">
                <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <DocumentIcon className="w-6 h-6 text-slate-400" />
                </div>
                <h3 className="text-sm font-semibold text-slate-900 mb-1">No CVs yet</h3>
                <p className="text-sm text-slate-500 mb-6">Create your first CV to start applying for jobs</p>
                <button
                  onClick={() => setStep('choice')}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-500 text-white rounded-md text-sm font-medium hover:bg-teal-600 transition-colors"
                >
                  <PlusIcon className="w-4 h-4" />
                  Create Your CV
                </button>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {cvs.map((cv) => (
                  <div key={cv.id} className="px-6 py-4 hover:bg-slate-50/60 transition-colors">
                    <div className="flex justify-between items-start">
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 bg-slate-100 rounded-md flex items-center justify-center mt-0.5 flex-shrink-0">
                          <DocumentIcon className="w-4 h-4 text-slate-500" />
                        </div>
                        <div>
                          <h3 className="text-sm font-medium text-slate-900">{cv.full_name}</h3>
                          <p className="text-xs text-slate-500 mt-0.5">{cv.email}</p>
                          <div className="mt-1.5 flex items-center gap-3 text-xs text-slate-400">
                            <span className="capitalize">{cv.template_id} template</span>
                            <span>{new Date(cv.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step: Choice */}
        {step === 'choice' && (
          <div className="bg-white rounded-lg border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-100">
              <button onClick={() => setStep('list')} className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors">
                <ArrowLeftIcon className="w-3.5 h-3.5" />
                Back
              </button>
            </div>
            <div className="px-6 py-10">
              <div className="text-center mb-8">
                <h2 className="text-base font-semibold text-navy-900">How would you like to start?</h2>
                <p className="text-sm text-slate-500 mt-1">Upload an existing CV or create a new one from scratch</p>
              </div>
              <div className="grid md:grid-cols-2 gap-4 max-w-xl mx-auto">
                <button
                  onClick={() => setStep('upload')}
                  className="group p-6 border border-slate-200 rounded-lg hover:border-teal-300 hover:bg-teal-50/30 transition-all text-left"
                >
                  <div className="w-10 h-10 bg-teal-50 rounded-lg flex items-center justify-center mb-4 group-hover:bg-teal-100 transition-colors">
                    <CloudUploadIcon className="w-5 h-5 text-teal-600" />
                  </div>
                  <h3 className="text-sm font-medium text-slate-900 mb-1">Upload Existing CV</h3>
                  <p className="text-xs text-slate-500">Upload a PDF or DOCX file</p>
                </button>
                <button
                  onClick={() => setStep('create')}
                  className="group p-6 border border-slate-200 rounded-lg hover:border-teal-300 hover:bg-teal-50/30 transition-all text-left"
                >
                  <div className="w-10 h-10 bg-teal-50 rounded-lg flex items-center justify-center mb-4 group-hover:bg-teal-100 transition-colors">
                    <PencilSquareIcon className="w-5 h-5 text-teal-600" />
                  </div>
                  <h3 className="text-sm font-medium text-slate-900 mb-1">Create New CV</h3>
                  <p className="text-xs text-slate-500">Build a professional CV step by step</p>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step: Upload */}
        {step === 'upload' && (
          <div className="bg-white rounded-lg border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-100">
              <button onClick={() => setStep('choice')} className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors">
                <ArrowLeftIcon className="w-3.5 h-3.5" />
                Back
              </button>
            </div>
            <div className="p-6">
              <h2 className="text-sm font-semibold text-slate-900 mb-6 text-center">Upload Your CV</h2>
              <div
                className={`border border-dashed rounded-lg p-12 text-center transition-colors ${dragActive ? 'border-teal-400 bg-teal-50/50' : 'border-slate-300 hover:border-slate-400'}`}
                onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleDrop}
              >
                <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <CloudUploadIcon className="w-5 h-5 text-slate-400" />
                </div>
                <p className="text-sm font-medium text-slate-700 mb-1">Drop your CV here</p>
                <p className="text-xs text-slate-400 mb-5">PDF or DOCX accepted</p>
                <input ref={fileInputRef} type="file" accept=".pdf,.docx" className="hidden" onChange={(e) => e.target.files?.[0] && handleUploadFile(e.target.files[0])} />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={loading}
                  className="px-4 py-2 bg-teal-500 text-white rounded-md text-sm font-medium hover:bg-teal-600 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Uploading...' : 'Browse Files'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step: Create CV Form */}
        {step === 'create' && (
          <div className="space-y-4">
            {/* Breadcrumb navigation */}
            <div className="bg-white rounded-lg border border-slate-200 px-5 py-3.5">
              <div className="flex items-center justify-between mb-3">
                <button onClick={() => setStep('choice')} className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors">
                  <ArrowLeftIcon className="w-3.5 h-3.5" />
                  Back
                </button>
                <span className="text-xs text-slate-400">Step {createSection + 1} of 4</span>
              </div>
              <nav className="flex items-center gap-1">
                {BREADCRUMB_STEPS.map((s, i) => (
                  <div key={s.label} className="flex items-center">
                    {i > 0 && (
                      <svg className="w-4 h-4 text-slate-300 mx-1 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                      </svg>
                    )}
                    <button
                      onClick={() => setCreateSection(i)}
                      className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                        createSection === i
                          ? 'bg-navy-900 text-white'
                          : createSection > i
                            ? 'text-teal-600 hover:bg-teal-50'
                            : 'text-slate-400 hover:text-slate-600'
                      }`}
                    >
                      {s.label}
                    </button>
                  </div>
                ))}
              </nav>
              <div className="mt-3 w-full bg-slate-100 rounded-full h-0.5">
                <div className="bg-teal-500 h-0.5 rounded-full transition-all" style={{ width: `${((createSection + 1) / 4) * 100}%` }} />
              </div>
            </div>

            {/* Personal Info */}
            {createSection === 0 && (
              <div className="bg-white rounded-lg border border-slate-200 p-6">
                <h3 className="text-sm font-semibold text-slate-900 mb-5">Personal Information</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1.5">Full Name *</label>
                    <input type="text" value={cvData.full_name} onChange={(e) => setCvData(prev => ({ ...prev, full_name: e.target.value }))} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none" placeholder="John Doe" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1.5">Email *</label>
                    <input type="email" value={cvData.email} onChange={(e) => setCvData(prev => ({ ...prev, email: e.target.value }))} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none" placeholder="john@example.com" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1.5">Phone</label>
                    <input type="tel" value={cvData.phone} onChange={(e) => setCvData(prev => ({ ...prev, phone: e.target.value }))} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none" placeholder="+44 7700 900000" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1.5">Location</label>
                    <input type="text" value={cvData.location} onChange={(e) => setCvData(prev => ({ ...prev, location: e.target.value }))} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none" placeholder="London, UK" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1.5">LinkedIn URL</label>
                    <input type="url" value={cvData.linkedin_url} onChange={(e) => setCvData(prev => ({ ...prev, linkedin_url: e.target.value }))} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none" placeholder="https://linkedin.com/in/johndoe" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1.5">Portfolio URL</label>
                    <input type="url" value={cvData.portfolio_url} onChange={(e) => setCvData(prev => ({ ...prev, portfolio_url: e.target.value }))} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none" placeholder="https://johndoe.com" />
                  </div>
                </div>
                <div className="mt-5">
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="block text-xs font-medium text-slate-600">Professional Summary</label>
                    <button
                      onClick={handleGenerateSummary}
                      disabled={generatingSummary}
                      className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 text-slate-600 rounded-md hover:bg-slate-200 text-xs font-medium disabled:opacity-50 transition-colors"
                    >
                      {generatingSummary ? 'Generating...' : 'Generate summary'}
                    </button>
                  </div>
                  <textarea value={cvData.summary} onChange={(e) => setCvData(prev => ({ ...prev, summary: e.target.value }))} rows={4} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none resize-none" placeholder="A compelling summary about your experience..." />
                </div>
                <div className="flex justify-end mt-6">
                  <button onClick={() => setCreateSection(1)} className="px-5 py-2 bg-navy-900 text-white rounded-md text-sm font-medium hover:bg-navy-800 transition-colors">
                    Next
                  </button>
                </div>
              </div>
            )}

            {/* Experience */}
            {createSection === 1 && (
              <div className="bg-white rounded-lg border border-slate-200 p-6">
                <div className="flex justify-between items-center mb-5">
                  <h3 className="text-sm font-semibold text-slate-900">Work Experience</h3>
                  <button onClick={handleAddExperience} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-teal-600 hover:bg-teal-50 rounded-md text-xs font-medium transition-colors">
                    <PlusIcon className="w-3.5 h-3.5" />
                    Add Position
                  </button>
                </div>
                <div className="space-y-4">
                  {cvData.experience.map((exp, index) => (
                    <div key={index} className="border border-slate-200 rounded-lg p-5 relative">
                      {cvData.experience.length > 1 && (
                        <button onClick={() => handleRemoveExperience(index)} className="absolute top-3 right-3 p-1 text-slate-400 hover:text-red-500 transition-colors">
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      )}
                      <div className="grid md:grid-cols-2 gap-3 mb-3">
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1.5">Company</label>
                          <input type="text" value={exp.company} onChange={(e) => handleUpdateExperience(index, 'company', e.target.value)} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none" placeholder="Google" />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1.5">Role</label>
                          <input type="text" value={exp.role} onChange={(e) => handleUpdateExperience(index, 'role', e.target.value)} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none" placeholder="Software Engineer" />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1.5">Start Date</label>
                          <input type="text" value={exp.start_date} onChange={(e) => handleUpdateExperience(index, 'start_date', e.target.value)} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none" placeholder="Jan 2020" />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1.5">End Date</label>
                          <input type="text" value={exp.end_date} onChange={(e) => handleUpdateExperience(index, 'end_date', e.target.value)} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none" placeholder="Present" />
                        </div>
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-slate-600 mb-1.5">Description</label>
                        <textarea value={exp.description} onChange={(e) => handleUpdateExperience(index, 'description', e.target.value)} rows={3} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none resize-none" placeholder="Describe your responsibilities and achievements..." />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex justify-between mt-6">
                  <button onClick={() => setCreateSection(0)} className="px-4 py-2 text-sm text-slate-600 font-medium hover:bg-slate-50 rounded-md transition-colors">
                    Back
                  </button>
                  <button onClick={() => setCreateSection(2)} className="px-5 py-2 bg-navy-900 text-white rounded-md text-sm font-medium hover:bg-navy-800 transition-colors">
                    Next
                  </button>
                </div>
              </div>
            )}

            {/* Education */}
            {createSection === 2 && (
              <div className="bg-white rounded-lg border border-slate-200 p-6">
                <div className="flex justify-between items-center mb-5">
                  <h3 className="text-sm font-semibold text-slate-900">Education</h3>
                  <button onClick={handleAddEducation} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-teal-600 hover:bg-teal-50 rounded-md text-xs font-medium transition-colors">
                    <PlusIcon className="w-3.5 h-3.5" />
                    Add Education
                  </button>
                </div>
                <div className="space-y-4">
                  {cvData.education.map((edu, index) => (
                    <div key={index} className="border border-slate-200 rounded-lg p-5 relative">
                      {cvData.education.length > 1 && (
                        <button onClick={() => handleRemoveEducation(index)} className="absolute top-3 right-3 p-1 text-slate-400 hover:text-red-500 transition-colors">
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      )}
                      <div className="grid md:grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1.5">Institution</label>
                          <input type="text" value={edu.institution} onChange={(e) => handleUpdateEducation(index, 'institution', e.target.value)} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none" placeholder="University of London" />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1.5">Degree</label>
                          <input type="text" value={edu.degree} onChange={(e) => handleUpdateEducation(index, 'degree', e.target.value)} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none" placeholder="BSc Computer Science" />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1.5">Field of Study</label>
                          <input type="text" value={edu.field} onChange={(e) => handleUpdateEducation(index, 'field', e.target.value)} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none" placeholder="Computer Science" />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1.5">Graduation Year</label>
                          <input type="text" value={edu.graduation_year} onChange={(e) => handleUpdateEducation(index, 'graduation_year', e.target.value)} className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none" placeholder="2020" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex justify-between mt-6">
                  <button onClick={() => setCreateSection(1)} className="px-4 py-2 text-sm text-slate-600 font-medium hover:bg-slate-50 rounded-md transition-colors">
                    Back
                  </button>
                  <button onClick={() => setCreateSection(3)} className="px-5 py-2 bg-navy-900 text-white rounded-md text-sm font-medium hover:bg-navy-800 transition-colors">
                    Next
                  </button>
                </div>
              </div>
            )}

            {/* Skills */}
            {createSection === 3 && (
              <div className="bg-white rounded-lg border border-slate-200 p-6">
                <h3 className="text-sm font-semibold text-slate-900 mb-5">Skills</h3>
                <div className="flex gap-2 mb-4">
                  <input
                    type="text"
                    value={skillInput}
                    onChange={(e) => setSkillInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddSkill())}
                    className="flex-1 px-3 py-2 border border-slate-200 rounded-md text-sm focus:border-teal-500 focus:ring-1 focus:ring-teal-500 focus:outline-none"
                    placeholder="Add a skill (e.g., Python, React, AWS)"
                  />
                  <button onClick={handleAddSkill} className="px-4 py-2 bg-teal-500 text-white rounded-md text-sm font-medium hover:bg-teal-600 transition-colors">
                    Add
                  </button>
                </div>
                <div className="flex flex-wrap gap-2 mb-6 min-h-[32px]">
                  {cvData.skills.map((skill) => (
                    <span key={skill} className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-xs font-medium">
                      {skill}
                      <button onClick={() => handleRemoveSkill(skill)} className="text-slate-400 hover:text-slate-600 transition-colors">
                        <XMarkIcon className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                  {cvData.skills.length === 0 && (
                    <p className="text-xs text-slate-400">No skills added yet</p>
                  )}
                </div>
                <div className="flex justify-between">
                  <button onClick={() => setCreateSection(2)} className="px-4 py-2 text-sm text-slate-600 font-medium hover:bg-slate-50 rounded-md transition-colors">
                    Back
                  </button>
                  <button onClick={goToTemplates} className="px-5 py-2 bg-teal-500 text-white rounded-md text-sm font-medium hover:bg-teal-600 transition-colors">
                    Choose Template
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step: Choose Template */}
        {step === 'templates' && (
          <div className="bg-white rounded-lg border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-100">
              <button onClick={() => { setStep('create'); setCreateSection(3); }} className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors">
                <ArrowLeftIcon className="w-3.5 h-3.5" />
                Back to editing
              </button>
            </div>
            <div className="p-6">
              <div className="text-center mb-8">
                <h2 className="text-base font-semibold text-navy-900">Choose Your Design</h2>
                <p className="text-sm text-slate-500 mt-1">Pick a professional template for your CV</p>
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                {[
                  { id: 'modern', name: 'Modern Professional', desc: 'Clean, contemporary. Best for tech and startups.', headerColor: 'bg-navy-900', accentColor: 'bg-teal-500' },
                  { id: 'classic', name: 'Classic Professional', desc: 'Traditional, conservative. Best for finance and law.', headerColor: 'bg-slate-700', accentColor: 'bg-slate-400' },
                  { id: 'minimal', name: 'Minimalist', desc: 'Ultra-clean, simple. Best for developers and designers.', headerColor: 'bg-slate-900', accentColor: 'bg-slate-200' },
                ].map((tmpl) => {
                  const isSelected = selectedTemplate === tmpl.id;
                  return (
                    <button
                      key={tmpl.id}
                      onClick={() => goToPreview(tmpl.id)}
                      disabled={loading}
                      className={`relative group border rounded-lg overflow-hidden transition-all text-left ${
                        isSelected ? 'border-teal-500 ring-1 ring-teal-500/20' : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className="bg-slate-50 p-4 flex items-center justify-center h-44">
                        <div className="w-28 h-36 bg-white rounded border border-slate-100 overflow-hidden">
                          <div className={`${tmpl.headerColor} h-6 w-full`} />
                          <div className="p-2 space-y-1.5">
                            <div className="w-full h-1.5 bg-slate-200 rounded" />
                            <div className="w-3/4 h-1 bg-slate-100 rounded" />
                            <div className={`mt-2 w-8 h-0.5 ${tmpl.accentColor} rounded`} />
                            <div className="w-full h-0.5 bg-slate-100 rounded" />
                            <div className="w-full h-0.5 bg-slate-100 rounded" />
                            <div className="w-2/3 h-0.5 bg-slate-100 rounded" />
                            <div className={`mt-2 w-8 h-0.5 ${tmpl.accentColor} rounded`} />
                            <div className="w-full h-0.5 bg-slate-100 rounded" />
                            <div className="w-1/2 h-0.5 bg-slate-100 rounded" />
                          </div>
                        </div>
                      </div>
                      <div className="p-4 border-t border-slate-100 flex items-start gap-3">
                        <div className={`mt-0.5 w-4 h-4 rounded-full border-2 flex-shrink-0 flex items-center justify-center ${
                          isSelected ? 'border-teal-500' : 'border-slate-300'
                        }`}>
                          {isSelected && <div className="w-2 h-2 rounded-full bg-teal-500" />}
                        </div>
                        <div>
                          <h3 className="text-sm font-medium text-slate-900 mb-0.5">{tmpl.name}</h3>
                          <p className="text-xs text-slate-500">{tmpl.desc}</p>
                        </div>
                      </div>
                      {loading && isSelected && (
                        <div className="absolute inset-0 bg-white/80 flex items-center justify-center">
                          <div className="animate-spin rounded-full h-5 w-5 border-2 border-slate-200 border-t-teal-500" />
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Step: Preview */}
        {step === 'preview' && (
          <div className="space-y-4">
            <div className="bg-white rounded-lg border border-slate-200">
              <div className="px-6 py-4 border-b border-slate-100">
                <div className="flex justify-between items-center">
                  <div>
                    <h2 className="text-sm font-semibold text-slate-900">CV Preview</h2>
                    <p className="text-xs text-slate-500 mt-0.5">Template: <span className="capitalize">{selectedTemplate}</span></p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => setStep('templates')} className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 rounded-md font-medium transition-colors">
                      Change Template
                    </button>
                    <button onClick={handleSaveAndFinish} className="px-4 py-2 bg-teal-500 text-white rounded-md text-sm font-medium hover:bg-teal-600 transition-colors">
                      Done
                    </button>
                  </div>
                </div>
              </div>
              <div className="p-4">
                <div className="border border-slate-200 rounded-md overflow-hidden">
                  <iframe srcDoc={previewHtml} className="w-full h-[800px] border-0" title="CV Preview" />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
