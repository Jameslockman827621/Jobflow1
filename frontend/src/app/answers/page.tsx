'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import AppShell from '@/components/AppShell';
import { useToast } from '@/components/ui/Toast';

interface AnswerEntry {
  id: number;
  question: string;
  answer: string;
  use_count: number;
  updated_at?: string | null;
}

export default function AnswersPage() {
  const router = useRouter();
  const { user, loading: authLoading, authFetch } = useAuth();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [answers, setAnswers] = useState<AnswerEntry[]>([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [saving, setSaving] = useState(false);
  const [filter, setFilter] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);

  useEffect(() => {
    if (!authLoading && !user) router.push('/login');
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) loadAnswers();
  }, [user]);

  async function loadAnswers(q?: string) {
    setLoading(true);
    try {
      const qs = q ? `?q=${encodeURIComponent(q)}` : '';
      const res = await authFetch(`/api/v1/answer-bank${qs}`);
      if (!res.ok) throw new Error('Failed to load answers');
      const data = await res.json();
      setAnswers(data.answers || []);
    } catch (err: any) {
      toast.error(err.message || 'Failed to load answer bank');
    } finally {
      setLoading(false);
    }
  }

  async function saveAnswer(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || !answer.trim()) {
      toast.error('Question and answer are required');
      return;
    }
    setSaving(true);
    try {
      if (editingId != null) {
        const res = await authFetch(`/api/v1/answer-bank/${editingId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: question.trim(), answer: answer.trim() }),
        });
        if (!res.ok) throw new Error('Update failed');
        toast.success('Answer updated');
      } else {
        const res = await authFetch('/api/v1/answer-bank', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: question.trim(), answer: answer.trim() }),
        });
        if (!res.ok) throw new Error('Save failed');
        toast.success('Answer saved');
      }
      setQuestion('');
      setAnswer('');
      setEditingId(null);
      await loadAnswers(filter || undefined);
    } catch (err: any) {
      toast.error(err.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  }

  async function deleteAnswer(id: number) {
    if (!confirm('Delete this saved answer?')) return;
    const res = await authFetch(`/api/v1/answer-bank/${id}`, { method: 'DELETE' });
    if (!res.ok) {
      toast.error('Delete failed');
      return;
    }
    toast.success('Deleted');
    await loadAnswers(filter || undefined);
  }

  function startEdit(row: AnswerEntry) {
    setEditingId(row.id);
    setQuestion(row.question);
    setAnswer(row.answer);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  if (authLoading || (loading && answers.length === 0)) {
    return (
      <AppShell>
        <div className="max-w-3xl mx-auto">
          <div className="h-7 w-40 bg-slate-100 rounded animate-pulse mb-4" />
          <div className="h-32 bg-slate-50 rounded animate-pulse" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto pb-16">
        <div className="mb-6">
          <h1 className="text-xl font-semibold text-navy-900 tracking-tight">Answer bank</h1>
          <p className="text-sm text-slate-500 mt-1">
            Reuse answers for recurring ATS questions during auto-apply.
          </p>
        </div>

        <form onSubmit={saveAnswer} className="bg-white border border-slate-200 rounded-lg p-4 mb-6 space-y-3">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
              Question
            </label>
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
              placeholder="Why do you want to work here?"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
              Answer
            </label>
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={4}
              className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
              placeholder="Your reusable answer…"
            />
          </div>
          <div className="flex items-center gap-2">
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 text-sm font-semibold rounded-md bg-navy-900 text-white hover:bg-navy-800 disabled:opacity-50"
            >
              {saving ? 'Saving…' : editingId != null ? 'Update answer' : 'Save answer'}
            </button>
            {editingId != null && (
              <button
                type="button"
                onClick={() => {
                  setEditingId(null);
                  setQuestion('');
                  setAnswer('');
                }}
                className="px-3 py-2 text-sm text-slate-600 hover:text-slate-900"
              >
                Cancel
              </button>
            )}
          </div>
        </form>

        <div className="flex items-center gap-2 mb-4">
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') loadAnswers(filter || undefined);
            }}
            className="flex-1 rounded-md border border-slate-200 px-3 py-2 text-sm"
            placeholder="Filter questions…"
          />
          <button
            type="button"
            onClick={() => loadAnswers(filter || undefined)}
            className="px-3 py-2 text-sm font-medium rounded-md border border-slate-200 bg-white hover:bg-slate-50"
          >
            Search
          </button>
        </div>

        <div className="space-y-3">
          {answers.map((row) => (
            <div key={row.id} className="bg-white border border-slate-200 rounded-lg p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-900">{row.question}</p>
                  <p className="text-sm text-slate-600 mt-2 whitespace-pre-wrap">{row.answer}</p>
                  <p className="text-xs text-slate-400 mt-2">Used {row.use_count || 0}×</p>
                </div>
                <div className="flex flex-col gap-1 shrink-0">
                  <button
                    type="button"
                    onClick={() => startEdit(row)}
                    className="text-xs text-teal-700 hover:text-teal-900 px-2 py-1"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteAnswer(row.id)}
                    className="text-xs text-red-600 hover:text-red-800 px-2 py-1"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
          {answers.length === 0 && !loading && (
            <p className="text-sm text-slate-500 text-center py-10">
              No saved answers yet. Add questions you see often on applications.
            </p>
          )}
        </div>
      </div>
    </AppShell>
  );
}
