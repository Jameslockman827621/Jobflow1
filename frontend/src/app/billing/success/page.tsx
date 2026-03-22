'use client';

import { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

function BillingSuccessInner() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session_id');

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center px-4">
      <div className="max-w-md w-full bg-white border border-slate-200 rounded-xl shadow-sm p-8 text-center">
        <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
        </div>
        <h1 className="text-xl font-semibold text-navy-900 mb-2">You are subscribed</h1>
        <p className="text-sm text-slate-600 mb-6">
          Thank you for upgrading. Your plan will update in a few moments. You can manage billing anytime from your profile.
        </p>
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
            href="/profile"
            className="inline-flex justify-center px-4 py-2.5 rounded-lg border border-slate-200 text-slate-700 text-sm font-medium hover:bg-slate-50"
          >
            Account settings
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
