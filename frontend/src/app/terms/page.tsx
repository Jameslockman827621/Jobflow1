import Link from 'next/link';

export const metadata = {
  title: 'Terms of Service | JobScale',
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-slate-200">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="text-sm font-semibold text-navy-900">JobScale</Link>
          <Link href="/" className="text-sm text-slate-500 hover:text-navy-900">Home</Link>
        </div>
      </header>
      <main className="max-w-3xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold text-navy-900 mb-6">Terms of Service</h1>
        <p className="text-slate-600 leading-relaxed mb-4">
          By accessing or using JobScale, you agree to these terms. If you do not agree, do not use the service.
        </p>
        <h2 className="text-lg font-semibold text-navy-900 mt-8 mb-2">The service</h2>
        <p className="text-slate-600 leading-relaxed mb-4">
          JobScale provides software to help you discover roles, prepare materials, and track applications. Job listings may come from third-party
          sources; we do not guarantee accuracy, availability, or outcomes of any application.
        </p>
        <h2 className="text-lg font-semibold text-navy-900 mt-8 mb-2">Accounts</h2>
        <p className="text-slate-600 leading-relaxed mb-4">
          You are responsible for safeguarding your credentials and for activity under your account. Notify us if you suspect unauthorized access.
        </p>
        <h2 className="text-lg font-semibold text-navy-900 mt-8 mb-2">Subscriptions and refunds</h2>
        <p className="text-slate-600 leading-relaxed mb-4">
          Paid plans are billed according to the offering shown at checkout. Unless otherwise stated, you may cancel through the billing portal.
          Refund policies communicated on the marketing site or checkout page apply when offered.
        </p>
        <h2 className="text-lg font-semibold text-navy-900 mt-8 mb-2">Disclaimer</h2>
        <p className="text-slate-600 leading-relaxed mb-4">
          The service is provided &quot;as is&quot; without warranties of any kind. To the maximum extent permitted by law, we are not liable for
          indirect or consequential damages arising from your use of JobScale.
        </p>
        <p className="text-xs text-slate-400 mt-8">Last updated: March 2026. This is a template — have it reviewed by counsel before launch.</p>
      </main>
    </div>
  );
}
