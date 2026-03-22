import Link from 'next/link';

export const metadata = {
  title: 'Contact | JobScale',
};

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-slate-200">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="text-sm font-semibold text-navy-900">JobScale</Link>
          <Link href="/" className="text-sm text-slate-500 hover:text-navy-900">Home</Link>
        </div>
      </header>
      <main className="max-w-3xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold text-navy-900 mb-4">Contact</h1>
        <p className="text-slate-600 leading-relaxed mb-8">
          For support, privacy requests, or Premium plan inquiries, email us at{' '}
          <a href="mailto:support@jobscale.app" className="text-teal-600 hover:underline font-medium">
            support@jobscale.app
          </a>
          . Replace this address with your production inbox before launch.
        </p>
        <Link href="/pricing" className="text-sm font-medium text-teal-600 hover:text-teal-700">
          View pricing
        </Link>
      </main>
    </div>
  );
}
