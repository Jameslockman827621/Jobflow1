"use client";

import Link from "next/link";
import { useState } from "react";

export default function Home() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50" style={{
      backgroundImage: 'linear-gradient(to right, rgba(148, 163, 184, 0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(148, 163, 184, 0.08) 1px, transparent 1px)',
      backgroundSize: '32px 32px'
    }}>
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex justify-between items-center">
            {/* Logo */}
            <Link href="/" className="flex items-center space-x-2 sm:space-x-3">
              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-navy-900 flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <span className="text-lg sm:text-xl font-bold text-navy-900">JobScale</span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              <a href="#" className="text-sm text-slate-600 hover:text-navy-900 transition-colors">Product</a>
              <a href="/pricing" className="text-sm text-slate-600 hover:text-navy-900 transition-colors">Pricing</a>
              <a href="#" className="text-sm text-slate-600 hover:text-navy-900 transition-colors">Company</a>
              <Link href="/login" className="text-sm font-semibold text-navy-900">Sign In</Link>
              <Link href="/login" className="px-5 py-2.5 text-sm font-semibold rounded-lg bg-navy-900 text-white hover:bg-navy-800 transition-all shadow-md hover:shadow-lg">
                Get Started
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg hover:bg-slate-100 transition-colors"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? (
                <svg className="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden absolute top-full left-0 right-0 bg-white border-b border-slate-200 shadow-lg py-4 px-4 space-y-4">
              <a href="#" className="block py-2 text-base text-slate-600 hover:text-navy-900 transition-colors">Product</a>
              <a href="/pricing" className="block py-2 text-base text-slate-600 hover:text-navy-900 transition-colors">Pricing</a>
              <a href="#" className="block py-2 text-base text-slate-600 hover:text-navy-900 transition-colors">Company</a>
              <div className="pt-4 border-t border-slate-200 space-y-3">
                <Link 
                  href="/login" 
                  className="block w-full text-center py-3 text-base font-semibold text-navy-900"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Sign In
                </Link>
                <Link 
                  href="/login" 
                  className="block w-full text-center py-3 text-base font-semibold rounded-lg bg-navy-900 text-white hover:bg-navy-800 transition-all"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Get Started
                </Link>
              </div>
            </div>
          )}
        </div>
      </nav>

      <main className="pt-20 sm:pt-32 pb-16 sm:pb-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          {/* Hero Section */}
          <div className="max-w-4xl mx-auto text-center mb-12 sm:mb-20">
            {/* Badge */}
            <div className="inline-flex items-center space-x-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full bg-white border border-slate-200 shadow-md mb-6 sm:mb-8">
              <span className="w-2 h-2 rounded-full bg-teal-500"></span>
              <span className="text-xs font-medium tracking-wide text-slate-600">Production Ready — 20 Features Complete</span>
            </div>
            
            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold text-navy-900 mb-4 sm:mb-6 tracking-tight leading-tight px-2">
              Your career, <span className="text-teal-500">accelerated</span>
            </h1>
            
            {/* Subheadline */}
            <p className="text-base sm:text-lg text-slate-600 mb-6 sm:mb-10 leading-relaxed px-4 sm:px-0">
              JobScale finds opportunities that match your skills, tailors your applications with AI, 
              and tracks your path from application to offer.
            </p>
            
            {/* CTA Group */}
            <div className="flex flex-col sm:flex-row justify-center items-center space-y-3 sm:space-y-0 sm:space-x-4 px-4">
              <Link href="/login" className="w-full sm:w-auto px-6 sm:px-8 py-3.5 text-base font-semibold rounded-lg bg-navy-900 text-white hover:bg-navy-800 transition-all shadow-md hover:shadow-lg text-center">
                Start Free Trial
              </Link>
              <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="w-full sm:w-auto px-6 sm:px-8 py-3.5 text-base font-semibold rounded-lg border-2 border-slate-200 text-navy-900 hover:bg-slate-50 transition-colors text-center">
                View Demo
              </a>
            </div>
            
            {/* Social Proof */}
            <p className="text-xs font-medium tracking-wide text-slate-600 mt-4 sm:mt-6">
              No credit card required · 5 free applications per month
            </p>
          </div>

          {/* Stats Bar */}
          <div className="bg-white border border-slate-200 rounded-2xl shadow-xl mb-12 sm:mb-20 overflow-hidden">
            <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-slate-200">
              <div className="py-6 sm:py-8 text-center px-4">
                <div className="text-3xl sm:text-4xl font-bold text-navy-900 mb-1">50+</div>
                <div className="text-xs font-medium tracking-wide text-slate-600">Companies Tracked</div>
              </div>
              <div className="py-6 sm:py-8 text-center px-4">
                <div className="text-3xl sm:text-4xl font-bold text-navy-900 mb-1">958</div>
                <div className="text-xs font-medium tracking-wide text-slate-600">Live Jobs</div>
              </div>
              <div className="py-6 sm:py-8 text-center px-4">
                <div className="text-3xl sm:text-4xl font-bold text-navy-900 mb-1">77%</div>
                <div className="text-xs font-medium tracking-wide text-slate-600">Match Accuracy</div>
              </div>
              <div className="py-6 sm:py-8 text-center px-4">
                <div className="text-3xl sm:text-4xl font-bold text-navy-900 mb-1">3</div>
                <div className="text-xs font-medium tracking-wide text-slate-600">AI Services</div>
              </div>
            </div>
          </div>

          {/* Features Grid */}
          <div className="mb-12 sm:mb-20">
            <div className="text-center mb-12 sm:mb-16 px-4">
              <h2 className="text-3xl sm:text-4xl font-bold text-navy-900 mb-3 sm:mb-4">Everything you need</h2>
              <p className="text-base sm:text-lg text-slate-600">From discovery to offer negotiation</p>
            </div>
            
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              {/* Feature 1 */}
              <div className="bg-white border border-slate-200 rounded-2xl shadow-md p-6 sm:p-8 hover:border-teal-300 hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-navy-900 flex items-center justify-center mb-4 sm:mb-6">
                  <svg className="w-5 h-5 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="text-xl sm:text-2xl font-semibold text-navy-900 mb-2 sm:mb-3">Smart Matching</h3>
                <p className="text-sm sm:text-base text-slate-600 mb-3 sm:mb-4 leading-relaxed">
                  Our AI analyzes your skills, experience level, and preferences to surface opportunities you're genuinely qualified for.
                </p>
                <a href="#" className="inline-flex items-center text-sm font-semibold text-teal-500 hover:text-teal-600 transition-colors">
                  Learn more
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </a>
              </div>

              {/* Feature 2 */}
              <div className="bg-white border border-slate-200 rounded-2xl shadow-md p-6 sm:p-8 hover:border-teal-300 hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-teal-500 flex items-center justify-center mb-4 sm:mb-6">
                  <svg className="w-5 h-5 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </div>
                <h3 className="text-xl sm:text-2xl font-semibold text-navy-900 mb-2 sm:mb-3">AI Applications</h3>
                <p className="text-sm sm:text-base text-slate-600 mb-3 sm:mb-4 leading-relaxed">
                  Generate tailored resumes and cover letters for each application. Stand out with personalized, relevant content.
                </p>
                <a href="#" className="inline-flex items-center text-sm font-semibold text-teal-500 hover:text-teal-600 transition-colors">
                  Learn more
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </a>
              </div}

              {/* Feature 3 */}
              <div className="bg-white border border-slate-200 rounded-2xl shadow-md p-6 sm:p-8 hover:border-teal-300 hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-amber-100 flex items-center justify-center mb-4 sm:mb-6">
                  <svg className="w-5 h-5 sm:w-6 sm:h-6 text-amber-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-xl sm:text-2xl font-semibold text-navy-900 mb-2 sm:mb-3">Career Pathing</h3>
                <p className="text-sm sm:text-base text-slate-600 mb-3 sm:mb-4 leading-relaxed">
                  See your career trajectory, identify skill gaps, and get actionable milestones to reach your next level.
                </p>
                <a href="/career" className="inline-flex items-center text-sm font-semibold text-teal-500 hover:text-teal-600 transition-colors">
                  Learn more
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </a>
              </div>

              {/* Feature 4 */}
              <div className="bg-white border border-slate-200 rounded-2xl shadow-md p-6 sm:p-8 hover:border-teal-300 hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-navy-900 flex items-center justify-center mb-4 sm:mb-6">
                  <svg className="w-5 h-5 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-xl sm:text-2xl font-semibold text-navy-900 mb-2 sm:mb-3">Analytics Dashboard</h3>
                <p className="text-sm sm:text-base text-slate-600 mb-3 sm:mb-4 leading-relaxed">
                  Track application funnel, interview rates, and market trends. Make data-driven decisions about your search.
                </p>
                <a href="/analytics" className="inline-flex items-center text-sm font-semibold text-teal-500 hover:text-teal-600 transition-colors">
                  Learn more
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </a>
              </div>

              {/* Feature 5 */}
              <div className="bg-white border border-slate-200 rounded-2xl shadow-md p-6 sm:p-8 hover:border-teal-300 hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-teal-500 flex items-center justify-center mb-4 sm:mb-6">
                  <svg className="w-5 h-5 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <h3 className="text-xl sm:text-2xl font-semibold text-navy-900 mb-2 sm:mb-3">Company Reviews</h3>
                <p className="text-sm sm:text-base text-slate-600 mb-3 sm:mb-4 leading-relaxed">
                  Read verified reviews from employees. Understand culture, compensation, and work-life balance before applying.
                </p>
                <a href="/reviews" className="inline-flex items-center text-sm font-semibold text-teal-500 hover:text-teal-600 transition-colors">
                  Learn more
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </a>
              </div}

              {/* Feature 6 */}
              <div className="bg-white border border-slate-200 rounded-2xl shadow-md p-6 sm:p-8 hover:border-teal-300 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 sm:col-span-2 lg:col-span-1">
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg bg-amber-100 flex items-center justify-center mb-4 sm:mb-6">
                  <svg className="w-5 h-5 sm:w-6 sm:h-6 text-amber-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </div>
                <h3 className="text-xl sm:text-2xl font-semibold text-navy-900 mb-2 sm:mb-3">Interview Coach</h3>
                <p className="text-sm sm:text-base text-slate-600 mb-3 sm:mb-4 leading-relaxed">
                  Practice with AI-powered mock interviews. Get real-time feedback on your responses and improve your delivery.
                </p>
                <a href="/interview-coach" className="inline-flex items-center text-sm font-semibold text-teal-500 hover:text-teal-600 transition-colors">
                  Learn more
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </a>
              </div>
            </div>
          </div>

          {/* CTA Section */}
          <div className="bg-navy-900 rounded-2xl shadow-xl p-6 sm:p-12 text-center">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-3 sm:mb-4 px-4">Ready to accelerate your career?</h2>
            <p className="text-base sm:text-lg text-slate-300 mb-6 sm:mb-8 max-w-2xl mx-auto px-4">
              Join thousands of professionals who landed their dream job with JobScale.
            </p>
            <Link href="/login" className="inline-block px-6 sm:px-8 py-3.5 text-base font-semibold rounded-lg bg-teal-500 text-white hover:bg-teal-600 transition-all shadow-lg hover:shadow-xl">
              Get Started Free
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
          <div className="flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0">
            <div className="flex items-center space-x-2 sm:space-x-3">
              <div className="w-8 h-8 rounded-lg bg-navy-900 flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <span className="text-sm font-semibold text-navy-900">JobScale</span>
            </div>
            <div className="flex items-center space-x-6 sm:space-x-8">
              <a href="#" className="text-xs font-medium tracking-wide text-slate-600 hover:text-navy-900 transition-colors">Privacy</a>
              <a href="#" className="text-xs font-medium tracking-wide text-slate-600 hover:text-navy-900 transition-colors">Terms</a>
              <a href="#" className="text-xs font-medium tracking-wide text-slate-600 hover:text-navy-900 transition-colors">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
