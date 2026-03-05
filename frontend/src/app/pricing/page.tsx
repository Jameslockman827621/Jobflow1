"use client";

import { useState } from "react";
import Link from "next/link";
import Navbar from "../../components/Navbar";

const PLANS = [
  {
    name: "Free",
    price: 0,
    period: "forever",
    description: "Get started with AI job search",
    features: [
      "5 applications per month",
      "Basic AI CV tailoring",
      "Job matching algorithm",
      "Application tracking",
      "Email support",
    ],
    cta: "Get Started",
    highlighted: false,
  },
  {
    name: "Pro",
    price: 29,
    period: "per month",
    description: "For serious job seekers",
    features: [
      "Unlimited applications",
      "Priority AI processing",
      "Advanced matching (80%+ only)",
      "Interview prep questions",
      "Cover letter generation",
      "Job alerts (daily)",
      "Application analytics",
      "Priority email support",
    ],
    cta: "Start Free Trial",
    highlighted: true,
  },
  {
    name: "Premium",
    price: 79,
    period: "per month",
    description: "Maximum career acceleration",
    features: [
      "Everything in Pro",
      "AI Interview Coach",
      "Resume review by experts",
      "Salary negotiation scripts",
      "Career pathing recommendations",
      "Recruiter network access",
      "1-on-1 career coaching (monthly)",
      "Priority customer support",
    ],
    cta: "Contact Sales",
    highlighted: false,
  },
];

const FAQ = [
  {
    question: "How is this different from LinkedIn?",
    answer: "LinkedIn is a job board. JobScale is an AI-powered application engine. We don't just show you jobs - we automatically tailor your CV, write cover letters, and help you apply to 10x more positions with higher quality applications.",
  },
  {
    question: "What happens if I don't get interviews?",
    answer: "We offer a 30-day money-back guarantee. If you're not getting interviews, we'll work with you to improve your profile, or refund your subscription.",
  },
  {
    question: "Can I cancel anytime?",
    answer: "Yes! Cancel anytime from your account settings. No questions asked.",
  },
  {
    question: "Do you work with all industries?",
    answer: "Yes! We support all industries and job levels, from entry-level to executive. Our AI adapts to your specific field.",
  },
  {
    question: "How does the referral program work?",
    answer: "Invite friends and earn $10 for each signup, $50 for each Pro subscription. Your friends get 1 month free Pro. Everyone wins!",
  },
];

export default function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "yearly">("monthly");
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <div className="min-h-screen bg-white">
      <Navbar isLoggedIn={false} />

      {/* Hero */}
      <section className="py-20 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Invest in Your Career
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
            One subscription could land you a job that pays $20k+ more. 
            What's that worth?
          </p>
          
          {/* Billing toggle */}
          <div className="flex items-center justify-center gap-4 mb-8">
            <span className={`text-sm ${billingPeriod === "monthly" ? "font-semibold" : "text-gray-500"}`}>
              Monthly
            </span>
            <button
              onClick={() => setBillingPeriod(billingPeriod === "monthly" ? "yearly" : "monthly")}
              className="w-14 h-8 bg-blue-600 rounded-full relative transition-colors"
            >
              <div className={`w-6 h-6 bg-white rounded-full absolute top-1 transition-transform ${
                billingPeriod === "yearly" ? "translate-x-7" : "translate-x-1"
              }`} />
            </button>
            <span className={`text-sm ${billingPeriod === "yearly" ? "font-semibold" : "text-gray-500"}`}>
              Yearly <span className="text-green-600 text-xs">(Save 20%)</span>
            </span>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8">
            {PLANS.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-2xl p-8 ${
                  plan.highlighted
                    ? "bg-blue-600 text-white shadow-xl scale-105"
                    : "bg-white text-gray-900 border border-gray-200"
                }`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-green-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                    Most Popular
                  </div>
                )}
                
                <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                <p className={`text-sm mb-6 ${plan.highlighted ? "text-blue-100" : "text-gray-500"}`}>
                  {plan.description}
                </p>
                
                <div className="mb-6">
                  <span className="text-4xl font-bold">
                    ${billingPeriod === "yearly" ? Math.floor(plan.price * 0.8) : plan.price}
                  </span>
                  <span className={`text-sm ${plan.highlighted ? "text-blue-100" : "text-gray-500"}`}>
                    /{plan.period}
                  </span>
                </div>
                
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <svg className={`w-5 h-5 flex-shrink-0 ${plan.highlighted ? "text-blue-200" : "text-green-500"}`} fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
                
                <Link
                  href="/login"
                  className={`block w-full py-3 px-6 rounded-lg text-center font-semibold transition-colors ${
                    plan.highlighted
                      ? "bg-white text-blue-600 hover:bg-blue-50"
                      : "bg-blue-600 text-white hover:bg-blue-700"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Referral Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Earn While You Search</h2>
          <p className="text-gray-600 mb-8">
            Refer friends and earn up to $600/year. They get 1 month free, you get paid.
          </p>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-3xl font-bold text-blue-600 mb-2">$10</div>
              <div className="text-sm text-gray-600">Per friend who signs up</div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-3xl font-bold text-blue-600 mb-2">$50</div>
              <div className="text-sm text-gray-600">Per friend who subscribes</div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-3xl font-bold text-blue-600 mb-2">Unlimited</div>
              <div className="text-sm text-gray-600">No cap on referrals</div>
            </div>
          </div>
          <Link
            href="/login"
            className="inline-block mt-8 px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700"
          >
            Get Your Referral Link
          </Link>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16">
        <div className="max-w-3xl mx-auto px-4">
          <h2 className="text-3xl font-bold mb-8 text-center">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {FAQ.map((faq, i) => (
              <div key={i} className="border border-gray-200 rounded-lg">
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full px-6 py-4 text-left flex justify-between items-center"
                >
                  <span className="font-semibold">{faq.question}</span>
                  <svg className={`w-5 h-5 transition-transform ${openFaq === i ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {openFaq === i && (
                  <div className="px-6 pb-4 text-gray-600">
                    {faq.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-blue-600">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Transform Your Job Search?
          </h2>
          <p className="text-blue-100 mb-8">
            Join thousands of job seekers landing better jobs with AI.
          </p>
          <Link
            href="/login"
            className="inline-block px-8 py-4 bg-white text-blue-600 rounded-lg font-semibold hover:bg-blue-50"
          >
            Start Your Free Trial
          </Link>
          <p className="text-blue-200 text-sm mt-4">
            No credit card required for free tier
          </p>
        </div>
      </section>
    </div>
  );
}
