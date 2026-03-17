'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toast';

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
  const [createSection, setCreateSection] = useState(0); // 0=personal, 1=experience, 2=education, 3=skills

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
    // Save temporarily to get preview
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
            <h1 className="text-2xl font-bold text-slate-900">CV Builder</h1>
            <button onClick={() => router.push('/dashboard')} className="text-sm text-slate-600 hover:text-navy-900">
              Back to Dashboard
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* CV List */}
        {step === 'list' && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-slate-900 mb-6">Your CVs</h2>
            {cvs.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">No CVs yet</h3>
                <p className="text-slate-600 mb-6">Create your first CV to start applying for jobs</p>
                <button onClick={() => setStep('choice')} className="px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors font-semibold">
                  Create Your CV
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {cvs.map((cv) => (
                  <div key={cv.id} className="border border-slate-200 rounded-xl p-6 hover:border-teal-300 transition-colors">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-lg font-semibold text-slate-900">{cv.full_name}</h3>
                        <p className="text-sm text-slate-600">{cv.email}</p>
                        <div className="mt-2 flex items-center space-x-4 text-xs text-slate-500">
                          <span>{cv.template_id} template</span>
                          <span>{new Date(cv.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                <button onClick={() => setStep('choice')} className="w-full py-3 border-2 border-dashed border-slate-300 rounded-xl text-slate-600 hover:border-teal-500 hover:text-teal-600 transition-colors font-medium">
                  + Create New CV
                </button>
              </div>
            )}
          </div>
        )}

        {/* Step: Choice */}
        {step === 'choice' && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <button onClick={() => setStep('list')} className="text-sm text-slate-600 hover:text-navy-900 mb-6 block">&larr; Back</button>
            <h2 className="text-2xl font-bold text-slate-900 mb-2 text-center">How would you like to start?</h2>
            <p className="text-slate-600 mb-8 text-center">Upload an existing CV or create a new one from scratch</p>
            <div className="grid md:grid-cols-2 gap-6 max-w-2xl mx-auto">
              <button onClick={() => setStep('upload')} className="p-8 border-2 border-slate-200 rounded-2xl hover:border-teal-500 hover:bg-teal-50 transition-all text-center group">
                <div className="w-16 h-16 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-teal-200 transition-colors">
                  <svg className="w-8 h-8 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">Upload Existing CV</h3>
                <p className="text-sm text-slate-600">Upload a PDF or DOCX file</p>
              </button>
              <button onClick={() => setStep('create')} className="p-8 border-2 border-slate-200 rounded-2xl hover:border-teal-500 hover:bg-teal-50 transition-all text-center group">
                <div className="w-16 h-16 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-teal-200 transition-colors">
                  <svg className="w-8 h-8 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">Create New CV</h3>
                <p className="text-sm text-slate-600">We build a professional CV for you</p>
              </button>
            </div>
          </div>
        )}

        {/* Step: Upload */}
        {step === 'upload' && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <button onClick={() => setStep('choice')} className="text-sm text-slate-600 hover:text-navy-900 mb-6 block">&larr; Back</button>
            <h2 className="text-2xl font-bold text-slate-900 mb-6 text-center">Upload Your CV</h2>
            <div
              className={`border-2 border-dashed rounded-2xl p-12 text-center transition-colors ${dragActive ? 'border-teal-500 bg-teal-50' : 'border-slate-300'}`}
              onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
            >
              <svg className="w-16 h-16 text-slate-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-lg font-medium text-slate-900 mb-2">Drop your CV here</p>
              <p className="text-sm text-slate-600 mb-4">or click to browse (PDF, DOCX)</p>
              <input ref={fileInputRef} type="file" accept=".pdf,.docx" className="hidden" onChange={(e) => e.target.files?.[0] && handleUploadFile(e.target.files[0])} />
              <button onClick={() => fileInputRef.current?.click()} disabled={loading} className="px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors font-semibold disabled:opacity-50">
                {loading ? 'Uploading...' : 'Browse Files'}
              </button>
            </div>
          </div>
        )}

        {/* Step: Create CV Form */}
        {step === 'create' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <button onClick={() => setStep('choice')} className="text-sm text-slate-600 hover:text-navy-900">&larr; Back</button>
                <div className="flex space-x-2">
                  {['Personal', 'Experience', 'Education', 'Skills'].map((label, i) => (
                    <button key={label} onClick={() => setCreateSection(i)}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${createSection === i ? 'bg-teal-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2">
                <div className="bg-teal-500 h-2 rounded-full transition-all" style={{ width: `${((createSection + 1) / 4) * 100}%` }}></div>
              </div>
            </div>

            {/* Personal Info */}
            {createSection === 0 && (
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <h3 className="text-xl font-bold text-slate-900 mb-6">Personal Information</h3>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Full Name *</label>
                    <input type="text" value={cvData.full_name} onChange={(e) => setCvData(prev => ({ ...prev, full_name: e.target.value }))} className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="John Doe" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Email *</label>
                    <input type="email" value={cvData.email} onChange={(e) => setCvData(prev => ({ ...prev, email: e.target.value }))} className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="john@example.com" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Phone</label>
                    <input type="tel" value={cvData.phone} onChange={(e) => setCvData(prev => ({ ...prev, phone: e.target.value }))} className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="+44 7700 900000" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Location</label>
                    <input type="text" value={cvData.location} onChange={(e) => setCvData(prev => ({ ...prev, location: e.target.value }))} className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="London, UK" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">LinkedIn URL</label>
                    <input type="url" value={cvData.linkedin_url} onChange={(e) => setCvData(prev => ({ ...prev, linkedin_url: e.target.value }))} className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="https://linkedin.com/in/johndoe" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Portfolio URL</label>
                    <input type="url" value={cvData.portfolio_url} onChange={(e) => setCvData(prev => ({ ...prev, portfolio_url: e.target.value }))} className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="https://johndoe.com" />
                  </div>
                </div>
                <div className="mt-6">
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-sm font-medium text-slate-700">Professional Summary</label>
                    <button onClick={handleGenerateSummary} disabled={generatingSummary} className="px-3 py-1.5 bg-teal-500 text-white rounded-lg hover:bg-teal-600 text-xs font-medium disabled:opacity-50">
                      {generatingSummary ? 'Generating...' : 'AI Generate'}
                    </button>
                  </div>
                  <textarea value={cvData.summary} onChange={(e) => setCvData(prev => ({ ...prev, summary: e.target.value }))} rows={4} className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none resize-none" placeholder="A compelling summary about your experience..." />
                </div>
                <div className="flex justify-end mt-6">
                  <button onClick={() => setCreateSection(1)} className="px-6 py-3 bg-navy-900 text-white rounded-lg font-medium hover:bg-navy-800">Next: Experience</button>
                </div>
              </div>
            )}

            {/* Experience */}
            {createSection === 1 && (
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-bold text-slate-900">Work Experience</h3>
                  <button onClick={handleAddExperience} className="px-4 py-2 text-teal-600 hover:bg-teal-50 rounded-lg text-sm font-medium">+ Add Position</button>
                </div>
                <div className="space-y-6">
                  {cvData.experience.map((exp, index) => (
                    <div key={index} className="border border-slate-200 rounded-xl p-6 relative">
                      {cvData.experience.length > 1 && (
                        <button onClick={() => handleRemoveExperience(index)} className="absolute top-4 right-4 text-red-600 hover:text-red-700 text-sm">Remove</button>
                      )}
                      <div className="grid md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-2">Company</label>
                          <input type="text" value={exp.company} onChange={(e) => handleUpdateExperience(index, 'company', e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="Google" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-2">Role</label>
                          <input type="text" value={exp.role} onChange={(e) => handleUpdateExperience(index, 'role', e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="Software Engineer" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-2">Start Date</label>
                          <input type="text" value={exp.start_date} onChange={(e) => handleUpdateExperience(index, 'start_date', e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="Jan 2020" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-2">End Date</label>
                          <input type="text" value={exp.end_date} onChange={(e) => handleUpdateExperience(index, 'end_date', e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="Present" />
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">Description</label>
                        <textarea value={exp.description} onChange={(e) => handleUpdateExperience(index, 'description', e.target.value)} rows={3} className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none resize-none" placeholder="Describe your responsibilities and achievements..." />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex justify-between mt-6">
                  <button onClick={() => setCreateSection(0)} className="px-6 py-3 text-slate-700 font-medium hover:bg-slate-100 rounded-lg">Back</button>
                  <button onClick={() => setCreateSection(2)} className="px-6 py-3 bg-navy-900 text-white rounded-lg font-medium hover:bg-navy-800">Next: Education</button>
                </div>
              </div>
            )}

            {/* Education */}
            {createSection === 2 && (
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-bold text-slate-900">Education</h3>
                  <button onClick={handleAddEducation} className="px-4 py-2 text-teal-600 hover:bg-teal-50 rounded-lg text-sm font-medium">+ Add Education</button>
                </div>
                <div className="space-y-6">
                  {cvData.education.map((edu, index) => (
                    <div key={index} className="border border-slate-200 rounded-xl p-6 relative">
                      {cvData.education.length > 1 && (
                        <button onClick={() => handleRemoveEducation(index)} className="absolute top-4 right-4 text-red-600 hover:text-red-700 text-sm">Remove</button>
                      )}
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-2">Institution</label>
                          <input type="text" value={edu.institution} onChange={(e) => handleUpdateEducation(index, 'institution', e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="University of London" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-2">Degree</label>
                          <input type="text" value={edu.degree} onChange={(e) => handleUpdateEducation(index, 'degree', e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="BSc Computer Science" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-2">Field of Study</label>
                          <input type="text" value={edu.field} onChange={(e) => handleUpdateEducation(index, 'field', e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="Computer Science" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-2">Graduation Year</label>
                          <input type="text" value={edu.graduation_year} onChange={(e) => handleUpdateEducation(index, 'graduation_year', e.target.value)} className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="2020" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex justify-between mt-6">
                  <button onClick={() => setCreateSection(1)} className="px-6 py-3 text-slate-700 font-medium hover:bg-slate-100 rounded-lg">Back</button>
                  <button onClick={() => setCreateSection(3)} className="px-6 py-3 bg-navy-900 text-white rounded-lg font-medium hover:bg-navy-800">Next: Skills</button>
                </div>
              </div>
            )}

            {/* Skills */}
            {createSection === 3 && (
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <h3 className="text-xl font-bold text-slate-900 mb-6">Skills</h3>
                <div className="flex gap-2 mb-4">
                  <input type="text" value={skillInput} onChange={(e) => setSkillInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddSkill())} className="flex-1 px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none" placeholder="Add a skill (e.g., Python, React, AWS)" />
                  <button onClick={handleAddSkill} className="px-6 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 font-medium">Add</button>
                </div>
                <div className="flex flex-wrap gap-2 mb-8">
                  {cvData.skills.map((skill) => (
                    <div key={skill} className="px-4 py-2 bg-teal-50 text-teal-700 rounded-lg flex items-center space-x-2">
                      <span>{skill}</span>
                      <button onClick={() => handleRemoveSkill(skill)} className="text-teal-600 hover:text-teal-800">&times;</button>
                    </div>
                  ))}
                </div>
                <div className="flex justify-between">
                  <button onClick={() => setCreateSection(2)} className="px-6 py-3 text-slate-700 font-medium hover:bg-slate-100 rounded-lg">Back</button>
                  <button onClick={goToTemplates} className="px-8 py-3 bg-teal-500 text-white rounded-lg font-semibold hover:bg-teal-600">Choose Template</button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step: Choose Template */}
        {step === 'templates' && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <button onClick={() => { setStep('create'); setCreateSection(3); }} className="text-sm text-slate-600 hover:text-navy-900 mb-6 block">&larr; Back to editing</button>
            <h2 className="text-2xl font-bold text-slate-900 mb-2 text-center">Choose Your Design</h2>
            <p className="text-slate-600 mb-8 text-center">Pick a professional template for your CV</p>
            <div className="grid md:grid-cols-3 gap-6">
              {[
                { id: 'modern', name: 'Modern Professional', desc: 'Clean, contemporary. Best for tech and startups.', color: 'from-blue-500 to-blue-700', accent: 'blue' },
                { id: 'classic', name: 'Classic Professional', desc: 'Traditional, conservative. Best for finance and law.', color: 'from-slate-700 to-slate-900', accent: 'slate' },
                { id: 'minimal', name: 'Minimalist', desc: 'Ultra-clean, simple. Best for developers and designers.', color: 'from-teal-500 to-teal-700', accent: 'teal' },
              ].map((tmpl) => (
                <button key={tmpl.id} onClick={() => goToPreview(tmpl.id)} disabled={loading}
                  className={`relative group border-2 rounded-2xl overflow-hidden transition-all hover:shadow-xl hover:-translate-y-1 ${selectedTemplate === tmpl.id ? 'border-teal-500 ring-2 ring-teal-200' : 'border-slate-200'}`}
                >
                  <div className={`h-40 bg-gradient-to-br ${tmpl.color} flex items-center justify-center`}>
                    <div className="w-24 h-32 bg-white rounded shadow-lg p-2">
                      <div className="w-full h-2 bg-slate-200 rounded mb-1"></div>
                      <div className="w-3/4 h-1.5 bg-slate-100 rounded mb-2"></div>
                      <div className="w-full h-1 bg-slate-100 rounded mb-0.5"></div>
                      <div className="w-full h-1 bg-slate-100 rounded mb-0.5"></div>
                      <div className="w-2/3 h-1 bg-slate-100 rounded mb-2"></div>
                      <div className="w-full h-1 bg-slate-100 rounded mb-0.5"></div>
                      <div className="w-full h-1 bg-slate-100 rounded mb-0.5"></div>
                    </div>
                  </div>
                  <div className="p-4 text-left">
                    <h3 className="font-bold text-slate-900 mb-1">{tmpl.name}</h3>
                    <p className="text-xs text-slate-600">{tmpl.desc}</p>
                  </div>
                  {loading && selectedTemplate === tmpl.id && (
                    <div className="absolute inset-0 bg-white/80 flex items-center justify-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500"></div>
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step: Preview */}
        {step === 'preview' && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">Your CV Preview</h2>
                  <p className="text-slate-600 text-sm">Template: {selectedTemplate}</p>
                </div>
                <div className="flex space-x-3">
                  <button onClick={() => setStep('templates')} className="px-4 py-2 text-slate-700 hover:bg-slate-100 rounded-lg text-sm font-medium">Change Template</button>
                  <button onClick={handleSaveAndFinish} className="px-6 py-3 bg-teal-500 text-white rounded-lg font-semibold hover:bg-teal-600">Done - Go to Jobs</button>
                </div>
              </div>
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <iframe srcDoc={previewHtml} className="w-full h-[800px] border-0" title="CV Preview" />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
