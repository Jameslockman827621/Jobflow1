"use client";

import { useState } from "react";
import Link from "next/link";

const PLANS = [
  {
    name: "Free",
    price: 0,
    yearlyPrice: 0,
    period: "forever",
    description: "For getting started with your job search",
    features: [
      "5 applications per month",
      "Basic CV tailoring",
      "Job matching",
      "Application tracking",
      "Email support",
    ],
    cta: "Get Started",
    highlighted: false,
  },
  {
    name: "Pro",
    price: 29,
    yearlyPrice: 23,
    period: "per month",
    description: "For active job seekers",
    features: [
      "Unlimited applications",
      "Priority processing",
      "Advanced matching (80%+ only)",
      "Interview prep questions",
      "Cover letter generation",
      "Daily job alerts",
      "Application analytics",
      "Priority support",
    ],
    cta: "Start Free Trial",
    highlighted: true,
  },
  {
    name: "Premium",
    price: 79,
    yearlyPrice: 63,
    period: "per month",
    description: "Full-service job search support",
    features: [
      "Everything in Pro",
      "Interview coaching",
      "Resume review by experts",
      "Salary negotiation guidance",
      "Career path recommendations",
      "Recruiter network access",
      "Monthly 1-on-1 coaching",
      "Dedicated support",
    ],
    cta: "Contact Sales",
    highlighted: false,
  },
];

const FAQ = [
  {
    question: "How does JobScale differ from a job board?",
    answer:
      "Job boards list openings. JobScale automates the application process -- tailoring your CV, generating cover letters, and tracking every application so you can focus on interviewing.",
  },
  {
    question: "What if I don't get interviews?",
    answer:
      "We offer a 30-day money-back guarantee. If you are not seeing results, we will work with you to improve your profile or refund your subscription.",
  },
  {
    question: "Can I cancel anytime?",
    answer:
      "Yes. Cancel from your account settings at any time. No questions asked.",
  },
  {
    question: "Which industries do you support?",
    answer:
      "All industries and seniority levels, from entry-level to executive. The platform adapts to your specific field and experience.",
  },
];

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 20 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
        fill="currentColor"
      />
    </svg>
  );
}

function ChevronIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  );
}

export default function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "yearly">(
    "monthly"
  );
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <div className="min-h-screen bg-white">
      {/* Public nav */}
      <nav className="border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#0c1a3b] flex items-center justify-center">
              <svg
                className="w-4 h-4 text-white"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                />
              </svg>
            </div>
            <span className="text-lg font-semibold text-slate-900">
              JobScale
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
            >
              Sign in
            </Link>
            <Link
              href="/login"
              className="text-sm font-medium px-4 py-2 rounded-lg bg-[#0c1a3b] text-white hover:bg-[#162d5a] transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-20 pb-12">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold text-[#0c1a3b] mb-4">
            Simple, transparent pricing
          </h1>
          <p className="text-lg text-slate-500 max-w-xl mx-auto mb-10">
            Choose the plan that fits your job search. Upgrade or downgrade at
            any time.
          </p>

          {/* Billing toggle */}
          <div className="inline-flex items-center gap-3 rounded-full border border-slate-200 p-1">
            <button
              onClick={() => setBillingPeriod("monthly")}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                billingPeriod === "monthly"
                  ? "bg-[#0c1a3b] text-white"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod("yearly")}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                billingPeriod === "yearly"
                  ? "bg-[#0c1a3b] text-white"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              Yearly
              <span className="ml-1.5 text-xs text-teal-600 font-semibold">
                Save 20%
              </span>
            </button>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="pb-20">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {PLANS.map((plan) => {
              const displayPrice =
                billingPeriod === "yearly" ? plan.yearlyPrice : plan.price;
              return (
                <div
                  key={plan.name}
                  className={`relative rounded-2xl p-8 flex flex-col ${
                    plan.highlighted
                      ? "bg-[#0c1a3b] text-white ring-2 ring-teal-500"
                      : "bg-white text-slate-900 border border-slate-200"
                  }`}
                >
                  {plan.highlighted && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-teal-500 text-white px-3 py-0.5 rounded-full text-xs font-semibold tracking-wide">
                      Most Popular
                    </div>
                  )}

                  <h3 className="text-lg font-semibold mb-1">{plan.name}</h3>
                  <p
                    className={`text-sm mb-6 ${
                      plan.highlighted ? "text-slate-300" : "text-slate-500"
                    }`}
                  >
                    {plan.description}
                  </p>

                  <div className="mb-8">
                    <span className="text-5xl font-bold tracking-tight">
                      ${displayPrice}
                    </span>
                    {plan.price > 0 && (
                      <span
                        className={`text-sm ml-1 ${
                          plan.highlighted ? "text-slate-400" : "text-slate-500"
                        }`}
                      >
                        /{plan.period}
                      </span>
                    )}
                    {plan.price === 0 && (
                      <span
                        className={`text-sm ml-1 ${
                          plan.highlighted ? "text-slate-400" : "text-slate-500"
                        }`}
                      >
                        /forever
                      </span>
                    )}
                  </div>

                  <ul className="space-y-3 mb-8 flex-1">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-start gap-3">
                        <CheckIcon
                          className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                            plan.highlighted ? "text-teal-400" : "text-teal-500"
                          }`}
                        />
                        <span
                          className={`text-sm ${
                            plan.highlighted ? "text-slate-200" : "text-slate-600"
                          }`}
                        >
                          {feature}
                        </span>
                      </li>
                    ))}
                  </ul>

                  <Link
                    href="/login"
                    className={`block w-full py-3 rounded-lg text-center text-sm font-semibold transition-colors ${
                      plan.highlighted
                        ? "bg-teal-500 text-white hover:bg-teal-600"
                        : "bg-slate-100 text-slate-900 hover:bg-slate-200"
                    }`}
                  >
                    {plan.cta}
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 border-t border-slate-100">
        <div className="max-w-2xl mx-auto px-4">
          <h2 className="text-2xl font-bold text-[#0c1a3b] mb-8 text-center">
            Frequently Asked Questions
          </h2>
          <div className="divide-y divide-slate-200">
            {FAQ.map((faq, i) => (
              <div key={i}>
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full py-5 text-left flex justify-between items-center gap-4"
                >
                  <span className="font-medium text-slate-900">
                    {faq.question}
                  </span>
                  <ChevronIcon
                    className={`w-5 h-5 flex-shrink-0 text-slate-400 transition-transform ${
                      openFaq === i ? "rotate-180" : ""
                    }`}
                  />
                </button>
                {openFaq === i && (
                  <p className="pb-5 text-sm text-slate-500 leading-relaxed">
                    {faq.answer}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-[#0c1a3b]">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to streamline your job search?
          </h2>
          <p className="text-slate-400 mb-8">
            Get started for free. No credit card required.
          </p>
          <Link
            href="/login"
            className="inline-block px-8 py-3 bg-teal-500 text-white rounded-lg font-semibold hover:bg-teal-600 transition-colors"
          >
            Get Started
          </Link>
        </div>
      </section>
    </div>
  );
}
