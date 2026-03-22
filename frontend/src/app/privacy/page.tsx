import Link from 'next/link';

export const metadata = {
  title: 'Privacy Policy | JobScale',
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-slate-200">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="text-sm font-semibold text-navy-900">JobScale</Link>
          <Link href="/" className="text-sm text-slate-500 hover:text-navy-900">Home</Link>
        </div>
      </header>
      <main className="max-w-3xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold text-navy-900 mb-6">Privacy Policy</h1>
        <p className="text-slate-600 leading-relaxed mb-4">
          JobScale helps you manage your job search. This policy describes how we handle information you provide when you use our website,
          API, and related services.
        </p>
        <h2 className="text-lg font-semibold text-navy-900 mt-8 mb-2">Information we collect</h2>
        <ul className="list-disc pl-5 text-slate-600 space-y-2">
          <li>Account details such as email address and name when you register.</li>
          <li>Profile and preference data you choose to save (roles, locations, CV content, skills).</li>
          <li>Usage data needed to operate the service (for example application logs and error reports).</li>
        </ul>
        <h2 className="text-lg font-semibold text-navy-900 mt-8 mb-2">How we use information</h2>
        <p className="text-slate-600 leading-relaxed mb-4">
          We use your information to provide the product (matching, tracking, billing), to communicate with you about your account,
          and to improve reliability and security. We do not sell your personal data to third parties.
        </p>
        <h2 className="text-lg font-semibold text-navy-900 mt-8 mb-2">Payments</h2>
        <p className="text-slate-600 leading-relaxed mb-4">
          Subscription billing is processed by Stripe. Card details are handled by Stripe according to their privacy policy; we store only
          what Stripe returns (such as customer and subscription identifiers) as needed to manage your plan.
        </p>
        <h2 className="text-lg font-semibold text-navy-900 mt-8 mb-2">Contact</h2>
        <p className="text-slate-600 leading-relaxed mb-8">
          For privacy questions, use the <Link href="/contact" className="text-teal-600 hover:underline">contact page</Link>.
        </p>
        <p className="text-xs text-slate-400">Last updated: March 2026. This is a template — have it reviewed by counsel before launch.</p>
      </main>
    </div>
  );
}
