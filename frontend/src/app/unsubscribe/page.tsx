'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { getApiBase } from '@/lib/apiBase';

function UnsubscribeInner() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');
  const [message, setMessage] = useState('Unsubscribing…');

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setStatus('error');
      setMessage('Missing unsubscribe token.');
      return;
    }
    const apiBase = getApiBase();
    fetch(`${apiBase}/alerts/unsubscribe?token=${encodeURIComponent(token)}`)
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          setStatus('error');
          setMessage(typeof data.detail === 'string' ? data.detail : 'Unsubscribe failed');
          return;
        }
        setStatus('ok');
        setMessage(data.message || 'You have been unsubscribed from alert emails.');
      })
      .catch(() => {
        setStatus('error');
        setMessage('Network error — try again from Alerts settings.');
      });
  }, [searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md bg-white border border-slate-200 rounded-xl p-8 text-center">
        <h1 className="text-lg font-semibold text-navy-900 mb-2">Email alerts</h1>
        <p className={`text-sm ${status === 'error' ? 'text-red-700' : 'text-slate-600'}`}>{message}</p>
        <div className="mt-6 flex flex-col gap-2">
          <Link href="/alerts" className="text-sm font-medium text-teal-700 hover:text-teal-900">
            Manage alert preferences
          </Link>
          <Link href="/login" className="text-sm text-slate-500 hover:text-slate-800">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function UnsubscribePage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-slate-500 text-sm">Loading…</div>}>
      <UnsubscribeInner />
    </Suspense>
  );
}
