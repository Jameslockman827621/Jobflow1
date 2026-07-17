'use client';

import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/auth';

type SubState = 'loading' | 'active' | 'pending' | 'error' | 'unauthenticated';

function BillingSuccessInner() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const { authFetch, getToken, loading: authLoading } = useAuth();
  const [state, setState] = useState<SubState>('loading');
  const [plan, setPlan] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!getToken()) {
      setState('unauthenticated');
      return;
    }

    let cancelled = false;
    let attempts = 0;
    const maxAttempts = 8;

    async function poll() {
      attempts += 1;
      try {
        const res = await authFetch('/api/v1/billing/subscription');
        if (!res.ok) {
          if (!cancelled) setState(attempts >= maxAttempts ? 'error' : 'pending');
          return;
        }
        const data = await res.json();
        const p = (data.plan || 'free').toLowerCase();
        if (!cancelled) setPlan(p);
        if (p !== 'free' && (data.status === 'active' || data.status === 'trialing')) {
          if (!cancelled) setState('active');
          return;
        }
        if (attempts >= maxAttempts) {
          if (!cancelled) setState('pending');
          return;
        }
        if (!cancelled) setState('pending');
        setTimeout(poll, 1500);
      } catch {
        if (!cancelled) setState(attempts >= maxAttempts ? 'error' : 'pending');
        if (attempts < maxAttempts) setTimeout(poll, 1500);
      }
    }

    poll();
    return () => {
      cancelled = true;
    };
  }, [authLoading, authFetch, getToken]);

  const title =
    state === 'active'
      ? 'You are subscribed'
      : state === 'pending' || state === 'loading'
        ? 'Confirming your subscription…'
        : state === 'unauthenticated'
          ? 'Sign in to confirm billing'
          : 'Could not confirm subscription';

  const body =
    state === 'active'
      ? `Your ${plan || 'paid'} plan is active. You can manage billing anytime from your profile.`
      : state === 'pending' || state === 'loading'
        ? 'Payment received — waiting for Stripe to sync your plan. This usually takes a few seconds.'
        : state === 'unauthenticated'
          ? 'Checkout may have succeeded, but we need you signed in to verify your plan.'
          : 'We could not verify your plan yet. Check Account settings — webhooks can lag by a minute.';

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center px-4">
      <div className="max-w-md w-full bg-white border border-slate-200 rounded-xl shadow-sm p-8 text-center">
        <div
          className={`w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4 ${
            state === 'active'
              ? 'bg-emerald-100 text-emerald-600'
              : state === 'error'
                ? 'bg-amber-100 text-amber-700'
                : 'bg-slate-100 text-slate-600'
          }`}
        >
          {state === 'loading' || state === 'pending' ? (
            <span className="inline-block w-5 h-5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
          ) : (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          )}
        </div>
        <h1 className="text-xl font-semibold text-navy-900 mb-2">{title}</h1>
        <p className="text-sm text-slate-600 mb-6">{body}</p>
        {sessionId && (
          <p className="text-xs text-slate-400 mb-6 font-mono break-all">Ref: {sessionId}</p>
        )}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/dashboard"
            className="inline-flex justify-center px-4 py-2.5 rounded-lg bg-navy-900 text-white text-sm font-medium hover:bg-navy-800"
          >
            Go to dashboard
          </Link>
          <Link
            href={state === 'unauthenticated' ? '/login' : '/profile'}
            className="inline-flex justify-center px-4 py-2.5 rounded-lg border border-slate-200 text-slate-700 text-sm font-medium hover:bg-slate-50"
          >
            {state === 'unauthenticated' ? 'Sign in' : 'Account settings'}
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function BillingSuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500 text-sm">
          Loading…
        </div>
      }
    >
      <BillingSuccessInner />
    </Suspense>
  );
}
