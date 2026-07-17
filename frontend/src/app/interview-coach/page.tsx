'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import AppShell from '@/components/AppShell';
import { useToast } from '@/components/ui/Toast';

interface CoachFeedback {
  clarity?: number;
  technical_depth?: number;
  structure?: number;
}

export default function InterviewCoachPage() {
  const router = useRouter();
  const { user, loading: authLoading, authFetch } = useAuth();
  const toast = useToast();
  const [role, setRole] = useState('Software Engineer');
  const [company, setCompany] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState<CoachFeedback | null>(null);
  const [busy, setBusy] = useState(false);
  const [unavailable, setUnavailable] = useState<string | null>(null);
  const [history, setHistory] = useState<Array<{ q: string; a?: string; feedback?: CoachFeedback }>>([]);

  useEffect(() => {
    if (!authLoading && !user) router.push('/login');
  }, [user, authLoading, router]);

  async function startSession(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setUnavailable(null);
    setFeedback(null);
    setHistory([]);
    try {
      const res = await authFetch('/api/v1/interview-coach/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: role.trim(),
          company: company.trim() || null,
          seniority: 'mid',
          duration_minutes: 30,
          focus_areas: ['technical', 'behavioral'],
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.status === 503) {
        setUnavailable(
          typeof data.detail === 'string'
            ? data.detail
            : 'Interview coach requires OPENAI_API_KEY on the server.'
        );
        return;
      }
      if (!res.ok) throw new Error(data.detail || 'Failed to start session');
      setSessionId(data.session_id);
      setQuestion(data.initial_question || '');
      setHistory([{ q: data.initial_question || '' }]);
      toast.success('Interview started');
    } catch (err: any) {
      toast.error(err.message || 'Failed to start');
    } finally {
      setBusy(false);
    }
  }

  async function sendAnswer(e: React.FormEvent) {
    e.preventDefault();
    if (!sessionId || !answer.trim()) return;
    setBusy(true);
    try {
      const res = await authFetch(
        `/api/v1/interview-coach/${encodeURIComponent(sessionId)}/message?message=${encodeURIComponent(answer.trim())}`,
        { method: 'POST' }
      );
      const data = await res.json().catch(() => ({}));
      if (res.status === 503) {
        setUnavailable(typeof data.detail === 'string' ? data.detail : 'Coach unavailable');
        return;
      }
      if (!res.ok) throw new Error(data.detail || 'Failed to evaluate answer');
      const fb = data.feedback || null;
      setFeedback(fb);
      setHistory((h) => {
        const next = [...h];
        if (next.length) next[next.length - 1] = { ...next[next.length - 1], a: answer.trim(), feedback: fb };
        if (data.follow_up_question) next.push({ q: data.follow_up_question });
        return next;
      });
      setQuestion(data.follow_up_question || question);
      setAnswer('');
    } catch (err: any) {
      toast.error(err.message || 'Failed');
    } finally {
      setBusy(false);
    }
  }

  if (authLoading) {
    return (
      <AppShell>
        <div className="max-w-2xl mx-auto py-16 text-center text-slate-500 text-sm">Loading…</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto pb-16">
        <div className="mb-6">
          <h1 className="text-xl font-semibold text-navy-900 tracking-tight">Interview coach</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real LLM practice — fails clearly when OpenAI is not configured (no fake scores).
          </p>
        </div>

        {unavailable && (
          <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            {unavailable}
          </div>
        )}

        {!sessionId ? (
          <form onSubmit={startSession} className="bg-white border border-slate-200 rounded-lg p-4 space-y-3">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">Role</label>
              <input
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
                Company (optional)
              </label>
              <input
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                placeholder="Acme"
              />
            </div>
            <button
              type="submit"
              disabled={busy}
              className="px-4 py-2 text-sm font-semibold rounded-md bg-navy-900 text-white hover:bg-navy-800 disabled:opacity-50"
            >
              {busy ? 'Starting…' : 'Start practice'}
            </button>
          </form>
        ) : (
          <div className="space-y-4">
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">Question</p>
              <p className="text-sm text-slate-900 whitespace-pre-wrap">{question}</p>
            </div>

            {feedback && (
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-sm text-slate-700">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">Feedback</p>
                <div className="flex flex-wrap gap-3">
                  {feedback.clarity != null && <span>Clarity {feedback.clarity}/10</span>}
                  {feedback.technical_depth != null && <span>Depth {feedback.technical_depth}/10</span>}
                  {feedback.structure != null && <span>Structure {feedback.structure}/10</span>}
                </div>
              </div>
            )}

            <form onSubmit={sendAnswer} className="bg-white border border-slate-200 rounded-lg p-4 space-y-3">
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                rows={5}
                className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                placeholder="Type your answer…"
              />
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={busy || !answer.trim()}
                  className="px-4 py-2 text-sm font-semibold rounded-md bg-navy-900 text-white hover:bg-navy-800 disabled:opacity-50"
                >
                  {busy ? 'Evaluating…' : 'Submit answer'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSessionId(null);
                    setQuestion('');
                    setAnswer('');
                    setFeedback(null);
                    setHistory([]);
                  }}
                  className="px-3 py-2 text-sm text-slate-600 hover:text-slate-900"
                >
                  End
                </button>
              </div>
            </form>

            {history.length > 1 && (
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Session</p>
                {history.map((h, i) => (
                  <div key={i} className="text-sm border border-slate-100 rounded-md p-3 bg-white">
                    <p className="text-slate-500 text-xs mb-1">Q{i + 1}</p>
                    <p className="text-slate-800">{h.q}</p>
                    {h.a && <p className="text-slate-600 mt-2"><span className="text-slate-400">You:</span> {h.a}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
