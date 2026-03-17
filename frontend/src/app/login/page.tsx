"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import Link from "next/link";

export default function Login() {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (isRegister) {
        await register(formData.email, formData.password, formData.first_name, formData.last_name);
      } else {
        await login(formData.email, formData.password);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-navy-900 flex items-center justify-center">
              <svg className="w-4 h-4 text-teal-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <span className="text-lg font-bold text-navy-900 tracking-tight">JobScale</span>
          </Link>
        </div>

        {/* Card */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-6 sm:p-8">
          <h1 className="text-heading-md text-navy-900 text-center mb-1">
            {isRegister ? "Create your account" : "Welcome back"}
          </h1>
          <p className="text-body-sm text-slate-500 text-center mb-6">
            {isRegister
              ? "Get started with your free account."
              : "Sign in to continue to JobScale."}
          </p>

          {error && (
            <div className="mb-4 flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <svg className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
              <span className="text-body-sm text-red-700">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-body-sm font-medium text-slate-700 mb-1.5">
                    First name
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    className="w-full px-3 py-2 text-body-sm border border-slate-200 rounded-lg bg-white text-navy-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-colors"
                    placeholder="Jane"
                  />
                </div>
                <div>
                  <label className="block text-body-sm font-medium text-slate-700 mb-1.5">
                    Last name
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    className="w-full px-3 py-2 text-body-sm border border-slate-200 rounded-lg bg-white text-navy-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-colors"
                    placeholder="Doe"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-body-sm font-medium text-slate-700 mb-1.5">
                Email
              </label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 text-body-sm border border-slate-200 rounded-lg bg-white text-navy-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-colors"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label className="block text-body-sm font-medium text-slate-700 mb-1.5">
                Password
              </label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-3 py-2 text-body-sm border border-slate-200 rounded-lg bg-white text-navy-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-colors"
                placeholder="Enter your password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 text-sm font-medium rounded-lg bg-navy-900 text-white hover:bg-navy-800 focus:outline-none focus:ring-2 focus:ring-navy-900/20 disabled:opacity-50 transition-colors"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Please wait...
                </span>
              ) : isRegister ? (
                "Create account"
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-100 text-center">
            <button
              onClick={() => {
                setIsRegister(!isRegister);
                setError("");
              }}
              className="text-body-sm text-slate-500 hover:text-navy-900 transition-colors"
            >
              {isRegister ? (
                <>Already have an account? <span className="font-medium text-navy-900">Sign in</span></>
              ) : (
                <>No account yet? <span className="font-medium text-navy-900">Create one</span></>
              )}
            </button>
          </div>
        </div>

        <div className="mt-6 text-center">
          <Link href="/" className="text-caption text-slate-400 hover:text-slate-600 transition-colors inline-flex items-center gap-1">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
            </svg>
            Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}
