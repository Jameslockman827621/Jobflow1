import Link from 'next/link';

export default function BillingCancelPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center px-4">
      <div className="max-w-md w-full bg-white border border-slate-200 rounded-xl shadow-sm p-8 text-center">
        <h1 className="text-xl font-semibold text-navy-900 mb-2">Checkout cancelled</h1>
        <p className="text-sm text-slate-600 mb-6">
          No charges were made. You can return to pricing whenever you are ready.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/pricing"
            className="inline-flex justify-center px-4 py-2.5 rounded-lg bg-navy-900 text-white text-sm font-medium hover:bg-navy-800"
          >
            Back to pricing
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex justify-center px-4 py-2.5 rounded-lg border border-slate-200 text-slate-700 text-sm font-medium hover:bg-slate-50"
          >
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
