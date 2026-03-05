import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <div className="max-w-7xl mx-auto px-4 py-16">
        {/* Hero */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">JobScale</h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Your AI-powered career accelerator. We find jobs that match your skills, 
            tailor your applications, and help you land better positions.
          </p>
          <div className="mt-8 flex justify-center space-x-4">
            <Link
              href="/login"
              className="px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700"
            >
              Get Started
            </Link>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-3 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50"
            >
              API Docs
            </a>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-3xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold mb-2">Smart Matching</h3>
            <p className="text-gray-600">
              AI analyzes your skills and preferences to find jobs you're actually qualified for.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-3xl mb-4">✍️</div>
            <h3 className="text-xl font-semibold mb-2">AI Applications</h3>
            <p className="text-gray-600">
              Automatically tailored CVs and cover letters for each application.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-3xl mb-4">📈</div>
            <h3 className="text-xl font-semibold mb-2">Career Growth</h3>
            <p className="text-gray-600">
              Even after you're hired, we keep finding better opportunities for you.
            </p>
          </div>
        </div>

        {/* Status */}
        <div className="bg-white p-6 rounded-lg shadow max-w-2xl mx-auto">
          <h2 className="text-xl font-semibold mb-4 text-center">MVP Status</h2>
          <div className="space-y-2">
            <div className="flex items-center">
              <span className="text-green-500 mr-2">✓</span>
              <span>User authentication (register/login)</span>
            </div>
            <div className="flex items-center">
              <span className="text-green-500 mr-2">✓</span>
              <span>Job scrapers (Greenhouse, Lever, Workable)</span>
            </div>
            <div className="flex items-center">
              <span className="text-green-500 mr-2">✓</span>
              <span>AI-powered CV tailoring & cover letters</span>
            </div>
            <div className="flex items-center">
              <span className="text-green-500 mr-2">✓</span>
              <span>Job matching algorithm</span>
            </div>
            <div className="flex items-center">
              <span className="text-green-500 mr-2">✓</span>
              <span>Application tracking</span>
            </div>
            <div className="flex items-center">
              <span className="text-yellow-500 mr-2">⏳</span>
              <span>Profile management (coming soon)</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
