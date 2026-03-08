'use client';

import { useState, useEffect } from 'react';
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

export default function CVBuilderPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [cvs, setCvs] = useState<CV[]>([]);
  
  const [cvData, setCvData] = useState({
    full_name: '',
    email: user?.email || '',
    phone: '',
    location: '',
    linkedin_url: '',
    portfolio_url: '',
    summary: '',
    experience: [{ company: '', role: '', start_date: '', end_date: '', description: '' }],
    education: [{ institution: '', degree: '', field: '', graduation_year: '' }],
    skills: [] as string[],
    certifications: [] as any[],
    projects: [] as any[],
    template_id: 'modern'
  });

  const [skillInput, setSkillInput] = useState('');
  const [generatingSummary, setGeneratingSummary] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      loadCVs();
    }
  }, [user]);

  async function loadCVs() {
    try {
      const res = await fetch('/api/v1/cvs');
      if (res.ok) {
        const data = await res.json();
        setCvs(data.cvs);
      }
    } catch (err) {
      console.error('Failed to load CVs:', err);
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
    setCvData(prev => ({
      ...prev,
      experience: prev.experience.filter((_, i) => i !== index)
    }));
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
    setCvData(prev => ({
      ...prev,
      education: prev.education.filter((_, i) => i !== index)
    }));
  };

  const handleAddSkill = () => {
    if (skillInput.trim() && !cvData.skills.includes(skillInput.trim())) {
      setCvData(prev => ({
        ...prev,
        skills: [...prev.skills, skillInput.trim()]
      }));
      setSkillInput('');
    }
  };

  const handleRemoveSkill = (skill: string) => {
    setCvData(prev => ({
      ...prev,
      skills: prev.skills.filter(s => s !== skill)
    }));
  };

  const handleGenerateSummary = async () => {
    if (cvData.experience.length === 0 || cvData.skills.length === 0) {
      toast.error('Please add at least one experience and skill first');
      return;
    }

    setGeneratingSummary(true);
    try {
      const res = await fetch('/api/v1/cvs/generate-summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          experience: cvData.experience,
          skills: cvData.skills,
          target_role: 'Software Engineer' // Could be dynamic
        })
      });

      if (res.ok) {
        const data = await res.json();
        setCvData(prev => ({ ...prev, summary: data.summary }));
        toast.success('AI-generated summary created!');
      } else {
        toast.error('Failed to generate summary');
      }
    } catch (err) {
      toast.error('Failed to generate summary');
    } finally {
      setGeneratingSummary(false);
    }
  };

  const handleSaveCV = async () => {
    // Validate required fields
    if (!cvData.full_name || !cvData.email) {
      toast.error('Name and email are required');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('/api/v1/cvs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cvData)
      });

      if (res.ok) {
        toast.success('CV saved successfully!');
        loadCVs();
        setStep(1);
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Failed to save CV');
      }
    } catch (err) {
      toast.error('Failed to save CV');
    } finally {
      setLoading(false);
    }
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
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-slate-900">CV Builder</h1>
            <button
              onClick={() => router.push('/dashboard')}
              className="text-sm text-slate-600 hover:text-navy-900"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Existing CVs */}
        {step === 1 && (
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
                <button
                  onClick={() => setStep(2)}
                  className="px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors font-semibold"
                >
                  Create New CV
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
                          <span>📄 {cv.template_id}</span>
                          <span>📅 {new Date(cv.created_at).toLocaleDateString()}</span>
                          {cv.is_ai_generated && <span>✨ AI-Generated</span>}
                        </div>
                      </div>
                      <div className="flex space-x-3">
                        <button className="px-4 py-2 text-sm text-teal-600 hover:bg-teal-50 rounded-lg transition-colors">
                          Edit
                        </button>
                        <button className="px-4 py-2 text-sm text-navy-900 bg-navy-900 text-white rounded-lg hover:bg-navy-800 transition-colors">
                          Download PDF
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
                <button
                  onClick={() => setStep(2)}
                  className="w-full py-3 border-2 border-dashed border-slate-300 rounded-xl text-slate-600 hover:border-teal-500 hover:text-teal-600 transition-colors font-medium"
                >
                  + Create New CV
                </button>
              </div>
            )}
          </div>
        )}

        {/* CV Builder Form */}
        {step === 2 && (
          <div className="space-y-6">
            {/* Progress */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-slate-900">Build Your CV</h2>
                <button onClick={() => setStep(1)} className="text-sm text-slate-600 hover:text-navy-900">
                  Cancel
                </button>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2">
                <div className="bg-teal-500 h-2 rounded-full transition-all" style={{ width: '50%' }}></div>
              </div>
            </div>

            {/* Personal Info */}
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h3 className="text-xl font-bold text-slate-900 mb-6">Personal Information</h3>
              
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Full Name *</label>
                  <input
                    type="text"
                    value={cvData.full_name}
                    onChange={(e) => setCvData(prev => ({ ...prev, full_name: e.target.value }))}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                    placeholder="John Doe"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Email *</label>
                  <input
                    type="email"
                    value={cvData.email}
                    onChange={(e) => setCvData(prev => ({ ...prev, email: e.target.value }))}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                    placeholder="john@example.com"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Phone</label>
                  <input
                    type="tel"
                    value={cvData.phone}
                    onChange={(e) => setCvData(prev => ({ ...prev, phone: e.target.value }))}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                    placeholder="+44 7700 900000"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Location</label>
                  <input
                    type="text"
                    value={cvData.location}
                    onChange={(e) => setCvData(prev => ({ ...prev, location: e.target.value }))}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                    placeholder="London, UK"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">LinkedIn URL</label>
                  <input
                    type="url"
                    value={cvData.linkedin_url}
                    onChange={(e) => setCvData(prev => ({ ...prev, linkedin_url: e.target.value }))}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                    placeholder="https://linkedin.com/in/johndoe"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Portfolio URL</label>
                  <input
                    type="url"
                    value={cvData.portfolio_url}
                    onChange={(e) => setCvData(prev => ({ ...prev, portfolio_url: e.target.value }))}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                    placeholder="https://johndoe.com"
                  />
                </div>
              </div>
            </div>

            {/* Professional Summary */}
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-slate-900">Professional Summary</h3>
                <button
                  onClick={handleGenerateSummary}
                  disabled={generatingSummary || cvData.experience.length === 0}
                  className="px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors text-sm font-medium disabled:opacity-50 flex items-center space-x-2"
                >
                  {generatingSummary ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Generating...</span>
                    </>
                  ) : (
                    <>
                      <span>✨</span>
                      <span>AI Generate</span>
                    </>
                  )}
                </button>
              </div>
              
              <textarea
                value={cvData.summary}
                onChange={(e) => setCvData(prev => ({ ...prev, summary: e.target.value }))}
                rows={4}
                className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none resize-none"
                placeholder="Write a compelling 3-4 sentence summary about your experience and career goals..."
              />
            </div>

            {/* Experience */}
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-slate-900">Work Experience</h3>
                <button
                  onClick={handleAddExperience}
                  className="px-4 py-2 text-teal-600 hover:bg-teal-50 rounded-lg transition-colors text-sm font-medium flex items-center space-x-2"
                >
                  <span>+</span>
                  <span>Add Position</span>
                </button>
              </div>
              
              <div className="space-y-6">
                {cvData.experience.map((exp, index) => (
                  <div key={index} className="border border-slate-200 rounded-xl p-6 relative">
                    {cvData.experience.length > 1 && (
                      <button
                        onClick={() => handleRemoveExperience(index)}
                        className="absolute top-4 right-4 text-red-600 hover:text-red-700 text-sm"
                      >
                        Remove
                      </button>
                    )}
                    
                    <div className="grid md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">Company</label>
                        <input
                          type="text"
                          value={exp.company}
                          onChange={(e) => handleUpdateExperience(index, 'company', e.target.value)}
                          className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                          placeholder="Google"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">Role</label>
                        <input
                          type="text"
                          value={exp.role}
                          onChange={(e) => handleUpdateExperience(index, 'role', e.target.value)}
                          className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                          placeholder="Software Engineer"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">Start Date</label>
                        <input
                          type="text"
                          value={exp.start_date}
                          onChange={(e) => handleUpdateExperience(index, 'start_date', e.target.value)}
                          className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                          placeholder="Jan 2020"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">End Date</label>
                        <input
                          type="text"
                          value={exp.end_date}
                          onChange={(e) => handleUpdateExperience(index, 'end_date', e.target.value)}
                          className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                          placeholder="Present"
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">Description</label>
                      <textarea
                        value={exp.description}
                        onChange={(e) => handleUpdateExperience(index, 'description', e.target.value)}
                        rows={3}
                        className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none resize-none"
                        placeholder="Describe your responsibilities and achievements..."
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Skills */}
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h3 className="text-xl font-bold text-slate-900 mb-6">Skills</h3>
              
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddSkill())}
                  className="flex-1 px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                  placeholder="Add a skill (e.g., Python, React, AWS)"
                />
                <button
                  onClick={handleAddSkill}
                  className="px-6 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors font-medium"
                >
                  Add
                </button>
              </div>
              
              <div className="flex flex-wrap gap-2">
                {cvData.skills.map((skill) => (
                  <div
                    key={skill}
                    className="px-4 py-2 bg-teal-50 text-teal-700 rounded-lg flex items-center space-x-2"
                  >
                    <span>{skill}</span>
                    <button
                      onClick={() => handleRemoveSkill(skill)}
                      className="text-teal-600 hover:text-teal-800"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => setStep(1)}
                className="px-6 py-3 text-slate-700 font-medium hover:bg-slate-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveCV}
                disabled={loading}
                className="px-8 py-3 bg-navy-900 text-white rounded-lg hover:bg-navy-800 transition-colors font-semibold disabled:opacity-50 flex items-center space-x-2"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Saving...</span>
                  </>
                ) : (
                  <span>Save CV</span>
                )}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
