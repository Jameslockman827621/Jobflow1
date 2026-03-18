"use client";

import Link from "next/link";
import { useState } from "react";

const features = [
  {
    title: "Job Discovery",
    description:
      "Browse curated listings from top companies. Filter by role, location, salary, and experience level to surface positions worth your time.",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
      </svg>
    ),
  },
  {
    title: "Tailored Applications",
    description:
      "Generate resumes and cover letters matched to each job description. The right experience gets highlighted for every application you send.",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
      </svg>
    ),
  },
  {
    title: "Application Tracking",
    description:
      "Follow every application from submission to offer. One dashboard shows exactly where you stand with each company.",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15a2.25 2.25 0 0 1 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25Z" />
      </svg>
    ),
  },
  {
    title: "Job Matching",
    description:
      "See how your skills and experience align with each listing. Understand where you are a strong fit and where to close the gap.",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
      </svg>
    ),
  },
  {
    title: "Company Insights",
    description:
      "Read verified reviews on culture, compensation, and work-life balance. Know what you are walking into before you apply.",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3H21m-3.75 3H21" />
      </svg>
    ),
  },
  {
    title: "Interview Prep",
    description:
      "Practice with mock interviews built around your target role. Get structured feedback on answers, delivery, and positioning.",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 0 1-.825-.242m9.345-8.334a2.126 2.126 0 0 0-.476-.095 48.64 48.64 0 0 0-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0 0 11.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
      </svg>
    ),
  },
];

const stats = [
  { value: "50+", label: "Companies indexed" },
  { value: "900+", label: "Open roles" },
  { value: "77%", label: "Avg. match rate" },
];

export default function Home() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200/80">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex justify-between items-center">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-navy-900 flex items-center justify-center">
                <svg className="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <span className="text-lg font-bold text-navy-900 tracking-tight">JobScale</span>
            </Link>

            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-sm text-slate-600 hover:text-navy-900 transition-colors">Product</a>
              <a href="/pricing" className="text-sm text-slate-600 hover:text-navy-900 transition-colors">Pricing</a>
              <Link href="/login" className="text-sm font-medium text-navy-900 hover:text-navy-700 transition-colors">Sign in</Link>
              <Link
                href="/login"
                className="px-4 py-2 text-sm font-medium rounded-lg bg-navy-900 text-white hover:bg-navy-800 transition-colors"
              >
                Get started
              </Link>
            </div>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg hover:bg-slate-100 transition-colors"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? (
                <svg className="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 9h16.5m-16.5 6.75h16.5" />
                </svg>
              )}
            </button>
          </div>

          {mobileMenuOpen && (
            <div className="md:hidden absolute top-full left-0 right-0 bg-white border-b border-slate-200 shadow-lg py-4 px-4 space-y-3">
              <a href="#features" className="block py-2 text-sm text-slate-600 hover:text-navy-900 transition-colors" onClick={() => setMobileMenuOpen(false)}>Product</a>
              <a href="/pricing" className="block py-2 text-sm text-slate-600 hover:text-navy-900 transition-colors" onClick={() => setMobileMenuOpen(false)}>Pricing</a>
              <div className="pt-3 border-t border-slate-200 space-y-2">
                <Link href="/login" className="block w-full text-center py-2.5 text-sm font-medium text-navy-900" onClick={() => setMobileMenuOpen(false)}>
                  Sign in
                </Link>
                <Link href="/login" className="block w-full text-center py-2.5 text-sm font-medium rounded-lg bg-navy-900 text-white" onClick={() => setMobileMenuOpen(false)}>
                  Get started
                </Link>
              </div>
            </div>
          )}
        </div>
      </nav>

      <main>
        {/* Hero */}
        <section className="relative pt-32 sm:pt-44 pb-16 sm:pb-24 overflow-hidden">
          <div className="absolute inset-0 bg-grid-pattern bg-grid opacity-40" />
          <div className="relative max-w-6xl mx-auto px-4 sm:px-6">
            <div className="max-w-3xl mx-auto text-center">
              <h1 className="text-display-lg text-navy-900 mb-6">
                Land the right role, faster
              </h1>
              <p className="text-body-lg text-slate-600 max-w-2xl mx-auto mb-10 leading-relaxed">
                JobScale organizes your entire job search in one place. Find relevant openings, send stronger applications, and track every conversation from first click to final offer.
              </p>
              <div className="flex justify-center">
                <Link
                  href="/login"
                  className="px-8 py-3 text-sm font-medium rounded-lg bg-navy-900 text-white hover:bg-navy-800 transition-colors"
                >
                  Get started
                </Link>
              </div>
              <p className="text-caption text-slate-400 mt-5">
                Free plan available. No credit card required.
              </p>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="pb-16 sm:pb-24">
          <div className="max-w-3xl mx-auto px-4 sm:px-6">
            <div className="grid grid-cols-3 divide-x divide-slate-200 bg-white border border-slate-200 rounded-xl">
              {stats.map((stat) => (
                <div key={stat.label} className="py-6 sm:py-8 text-center">
                  <div className="text-2xl sm:text-3xl font-bold text-navy-900 tracking-tight">{stat.value}</div>
                  <div className="text-caption text-slate-500 mt-1">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="pb-16 sm:pb-24">
          <div className="max-w-6xl mx-auto px-4 sm:px-6">
            <div className="text-center mb-12 sm:mb-16">
              <h2 className="text-heading-xl text-navy-900 mb-3">Everything you need to run a focused search</h2>
              <p className="text-body-lg text-slate-500 max-w-xl mx-auto">From discovery to offer, one workspace for the entire process.</p>
            </div>

            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="group bg-white border border-slate-200 rounded-xl p-6 hover:border-slate-300 hover:shadow-md transition-all duration-200"
                >
                  <div className="w-9 h-9 rounded-lg bg-navy-900/5 flex items-center justify-center mb-4 text-teal-500 group-hover:bg-navy-900/10 transition-colors">
                    {feature.icon}
                  </div>
                  <h3 className="text-heading-sm text-navy-900 mb-2">{feature.title}</h3>
                  <p className="text-body-sm text-slate-500 leading-relaxed">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="pb-16 sm:pb-24">
          <div className="max-w-6xl mx-auto px-4 sm:px-6">
            <div className="relative bg-navy-900 rounded-2xl px-6 sm:px-12 py-12 sm:py-16 text-center overflow-hidden">
              <div className="absolute inset-0 bg-grid-pattern bg-grid opacity-[0.04]" />
              <div className="relative">
                <h2 className="text-heading-xl text-white mb-3">Start your search today</h2>
                <p className="text-body-lg text-slate-300 max-w-lg mx-auto mb-8">
                  Create a profile, set your preferences, and see matched roles in minutes.
                </p>
                <Link
                  href="/login"
                  className="inline-block px-8 py-3 text-sm font-medium rounded-lg bg-teal-500 text-white hover:bg-teal-400 transition-colors"
                >
                  Get started
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-lg bg-navy-900 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-teal-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <span className="text-sm font-semibold text-navy-900 tracking-tight">JobScale</span>
            </div>
            <div className="flex items-center space-x-6">
              <a href="#" className="text-caption text-slate-500 hover:text-navy-900 transition-colors">Privacy</a>
              <a href="#" className="text-caption text-slate-500 hover:text-navy-900 transition-colors">Terms</a>
              <a href="#" className="text-caption text-slate-500 hover:text-navy-900 transition-colors">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
