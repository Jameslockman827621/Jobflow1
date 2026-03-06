"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ReviewsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [companies, setCompanies] = useState<any[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  const [reviews, setReviews] = useState<any>(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    company_name: "",
    overall_rating: 5,
    title: "",
    pros: "",
    cons: "",
  });

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      router.push("/login");
      return;
    }
    setToken(storedToken);
    fetchCompanies(storedToken);
  }, [router]);

  const fetchCompanies = async (authToken: string) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/reviews/companies`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCompanies(data.companies || []);
      }
    } catch (error) {
      console.error("Error fetching companies:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCompanyReviews = async (companyName: string) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/reviews/company/${encodeURIComponent(companyName)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setReviews(data);
      }
    } catch (error) {
      console.error("Error fetching reviews:", error);
    }
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/reviews/company`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        alert("Review submitted!");
        setShowForm(false);
        setFormData({ company_name: "", overall_rating: 5, title: "", pros: "", cons: "" });
        fetchCompanies(token);
      }
    } catch (error) {
      console.error("Error submitting review:", error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-lg text-slate-600">Loading reviews...</div>
      </div>
    );
  }

  // Mock data for demo
  const companyList = [
    { name: "Stripe", rating: 4.5, reviews: 127, color: "bg-navy-900", location: "Fintech • San Francisco" },
    { name: "Airbnb", rating: 4.2, reviews: 89, color: "bg-red-500", location: "Travel • San Francisco" },
    { name: "GitLab", rating: 4.0, reviews: 56, color: "bg-orange-500", location: "DevTools • Remote" },
    { name: "Figma", rating: 4.3, reviews: 42, color: "bg-blue-500", location: "Design • San Francisco" },
    { name: "Monzo", rating: 3.8, reviews: 31, color: "bg-slate-800", location: "Fintech • London" },
  ];

  const reviewData = {
    name: "Stripe",
    rating: 4.5,
    totalReviews: 127,
    location: "Financial Services • San Francisco, CA",
    ratings: {
      workLife: 4.2,
      culture: 4.7,
      compensation: 4.6,
      opportunities: 4.3,
    },
    recommendToFriend: 75,
    reviews: [
      {
        id: 1,
        title: "Great place for career growth",
        rating: 5,
        author: "Current Employee • Software Engineer",
        date: "2 weeks ago",
        pros: "Excellent compensation package, incredibly smart colleagues, cutting-edge technology stack, amazing learning opportunities, great work-life balance for the industry.",
        cons: "Can be high pressure during product launches, sometimes long hours expected, very high performance bar.",
        helpful: 24,
      },
      {
        id: 2,
        title: "Best decision I made",
        rating: 5,
        author: "Former Employee • Senior Engineer",
        date: "1 month ago",
        pros: "Top-tier engineering culture, excellent benefits (health, 401k, equity), meaningful work that impacts millions, collaborative team environment.",
        cons: "Very selective hiring process can be lengthy, high expectations from day one.",
        helpful: 18,
      },
      {
        id: 3,
        title: "Good but intense",
        rating: 4,
        author: "Current Employee • Product Manager",
        date: "2 months ago",
        pros: "Fast-paced environment, great team culture, competitive compensation, excellent growth opportunities.",
        cons: "Work-life balance can suffer during busy periods, high stress environment.",
        helpful: 12,
      },
    ],
  };

  return (
    <div className="min-h-screen bg-slate-50" style={{
      backgroundImage: 'linear-gradient(to right, rgba(148, 163, 184, 0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(148, 163, 184, 0.08) 1px, transparent 1px)',
      backgroundSize: '32px 32px'
    }}>
      <Navbar onLogout={handleLogout} />

      <main className="pt-28 pb-16">
        <div className="max-w-7xl mx-auto px-6">
          {/* Header */}
          <div className="mb-12">
            <div className="flex items-center space-x-2 text-xs font-medium tracking-wide text-slate-600 mb-4">
              <a href="/dashboard" className="text-slate-600 hover:text-navy-900">Dashboard</a>
              <span>/</span>
              <span className="text-navy-900">Company Reviews</span>
            </div>
            <div className="flex justify-between items-end">
              <div>
                <h1 className="text-4xl font-bold text-navy-900 mb-2">Company Reviews</h1>
                <p className="text-lg text-slate-600">Real insights from verified employees</p>
              </div>
              <button 
                onClick={() => setShowForm(true)}
                className="px-6 py-3 text-sm font-semibold rounded-lg bg-teal-500 text-white hover:bg-teal-600 transition-colors flex items-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                <span>Write a Review</span>
              </button>
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Company List */}
            <div className="lg:col-span-1">
              <div className="bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden">
                <div className="p-6 border-b border-slate-200">
                  <div className="relative">
                    <input 
                      type="text" 
                      placeholder="Search companies..." 
                      className="w-full px-5 py-3 pl-12 text-sm rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 text-navy-900 placeholder-slate-400"
                    />
                    <svg className="w-5 h-5 absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                </div>
                <div className="divide-y divide-slate-200 max-h-[600px] overflow-y-auto">
                  {companyList.map((company) => (
                    <div 
                      key={company.name}
                      onClick={() => { setSelectedCompany(company.name); fetchCompanyReviews(company.name); }}
                      className={`p-5 cursor-pointer transition-colors ${selectedCompany === company.name ? 'bg-teal-50 border-l-4 border-teal-500' : 'hover:bg-slate-50'}`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center space-x-3">
                          <div className={`w-10 h-10 rounded-xl ${company.color} flex items-center justify-center text-white font-bold text-sm`}>
                            {company.name[0]}
                          </div>
                          <div>
                            <h3 className="font-semibold text-sm text-navy-900">{company.name}</h3>
                            <p className="text-sm text-slate-600">{company.location}</p>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="flex">
                          {[...Array(5)].map((_, i) => (
                            <span key={i} className={i < Math.floor(company.rating) ? 'text-amber-400' : 'text-slate-300'}>★</span>
                          ))}
                        </div>
                        <span className="text-sm font-semibold text-navy-900">{company.rating}</span>
                        <span className="text-sm text-slate-600">({company.reviews} reviews)</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Review Details */}
            <div className="lg:col-span-2 space-y-8">
              {/* Company Overview */}
              <div className="bg-white border border-slate-200 rounded-2xl shadow-xl p-8">
                <div className="flex items-start justify-between mb-8">
                  <div className="flex items-center space-x-5">
                    <div className="w-20 h-20 rounded-2xl bg-navy-900 flex items-center justify-center text-white text-3xl font-bold">
                      {reviewData.name[0]}
                    </div>
                    <div>
                      <h2 className="text-3xl font-bold text-navy-900 mb-1">{reviewData.name}</h2>
                      <p className="text-base text-slate-600">{reviewData.location}</p>
                      <div className="flex items-center space-x-4 mt-2">
                        <div className="flex items-center space-x-2">
                          <div className="flex">
                            {[...Array(5)].map((_, i) => (
                              <span key={i} className="text-amber-400 text-xl">★</span>
                            ))}
                          </div>
                          <span className="text-2xl font-bold text-navy-900">{reviewData.rating}</span>
                        </div>
                        <span className="text-slate-300">•</span>
                        <span className="text-base text-slate-600">{reviewData.totalReviews} reviews</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex space-x-3">
                    <button className="px-5 py-2.5 text-sm font-semibold rounded-lg border border-slate-200 text-navy-900 hover:bg-slate-50 transition-colors">Follow</button>
                    <button className="px-5 py-2.5 text-sm font-semibold rounded-lg bg-teal-500 text-white hover:bg-teal-600 transition-colors">Write Review</button>
                  </div>
                </div>

                {/* Ratings Breakdown */}
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold text-navy-900 mb-4">Rating Breakdown</h3>
                    <div className="space-y-4">
                      {[
                        { label: "Work-Life Balance", value: reviewData.ratings.workLife },
                        { label: "Culture & Values", value: reviewData.ratings.culture },
                        { label: "Compensation & Benefits", value: reviewData.ratings.compensation },
                        { label: "Career Opportunities", value: reviewData.ratings.opportunities },
                      ].map((item) => (
                        <div key={item.label}>
                          <div className="flex justify-between text-sm mb-2">
                            <span className="text-slate-600">{item.label}</span>
                            <span className="font-semibold text-navy-900">{item.value}</span>
                          </div>
                          <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                            <div className="h-full bg-teal-500 rounded-full" style={{ width: `${(item.value / 5) * 100}%` }}></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold text-navy-900 mb-4">Recommend to Friend</h3>
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <div className="relative w-40 h-40 mx-auto mb-4">
                          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                            <circle cx="50" cy="50" r="40" stroke="#e2e8f0" strokeWidth="12" fill="none"/>
                            <circle cx="50" cy="50" r="40" stroke="#14b8a6" strokeWidth="12" fill="none" strokeDasharray="251.2" strokeDashoffset="62.8" strokeLinecap="round"/>
                          </svg>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <div className="text-center">
                              <div className="text-3xl font-bold text-navy-900">{reviewData.recommendToFriend}%</div>
                              <div className="text-xs font-medium tracking-wide text-slate-600">Yes</div>
                            </div>
                          </div>
                        </div>
                        <p className="text-sm text-slate-600">of employees would recommend {reviewData.name} to a friend</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Reviews */}
              <div className="bg-white border border-slate-200 rounded-2xl shadow-xl p-8">
                <div className="flex justify-between items-center mb-8">
                  <h3 className="text-2xl font-semibold text-navy-900">Recent Reviews</h3>
                  <select className="px-4 py-2 text-sm font-semibold rounded-lg border border-slate-200 bg-white text-navy-900 focus:outline-none focus:ring-2 focus:ring-teal-500">
                    <option>Most Recent</option>
                    <option>Highest Rated</option>
                    <option>Lowest Rated</option>
                  </select>
                </div>

                <div className="space-y-6">
                  {reviewData.reviews.map((review) => (
                    <div key={review.id} className="bg-white border border-slate-200 rounded-xl p-6 hover:shadow-lg transition-shadow">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h4 className="font-semibold text-lg text-navy-900 mb-2">{review.title}</h4>
                          <div className="flex items-center space-x-3">
                            <div className="flex">
                              {[...Array(5)].map((_, i) => (
                                <span key={i} className={i < review.rating ? 'text-amber-400' : 'text-slate-300'}>★</span>
                              ))}
                            </div>
                            <span className="text-sm text-slate-600">{review.author}</span>
                          </div>
                        </div>
                        <span className="text-sm text-slate-600">{review.date}</span>
                      </div>
                      <div className="space-y-3">
                        <div className="flex items-start space-x-3">
                          <span className="font-semibold text-sm text-emerald-600 flex-shrink-0">👍 Pros:</span>
                          <p className="text-sm text-slate-700">{review.pros}</p>
                        </div>
                        <div className="flex items-start space-x-3">
                          <span className="font-semibold text-sm text-red-600 flex-shrink-0">👎 Cons:</span>
                          <p className="text-sm text-slate-700">{review.cons}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4 mt-4 pt-4 border-t border-slate-200">
                        <button className="text-sm text-slate-600 hover:text-navy-900 flex items-center space-x-1 transition-colors">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                          </svg>
                          <span>Helpful ({review.helpful})</span>
                        </button>
                        <button className="text-sm text-slate-600 hover:text-navy-900 transition-colors">Share</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Write Review Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-6">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-8">
            <h2 className="text-2xl font-bold text-navy-900 mb-6">Write a Review</h2>
            <form onSubmit={handleSubmitReview} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Company</label>
                <input
                  type="text"
                  required
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500"
                  placeholder="e.g., Stripe"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Rating</label>
                <select
                  value={formData.overall_rating}
                  onChange={(e) => setFormData({ ...formData, overall_rating: Number(e.target.value) })}
                  className="w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500"
                >
                  {[5, 4, 3, 2, 1].map((r) => (
                    <option key={r} value={r}>{r} Stars</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Title</label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500"
                  placeholder="e.g., Great place to work"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Pros</label>
                <textarea
                  required
                  value={formData.pros}
                  onChange={(e) => setFormData({ ...formData, pros: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500"
                  placeholder="What did you like about working here?"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Cons</label>
                <textarea
                  required
                  value={formData.cons}
                  onChange={(e) => setFormData({ ...formData, cons: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500"
                  placeholder="What could be improved?"
                />
              </div>
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="flex-1 px-5 py-2.5 text-sm font-semibold rounded-lg border border-slate-200 text-navy-900 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-5 py-2.5 text-sm font-semibold rounded-lg bg-teal-500 text-white hover:bg-teal-600 transition-colors"
                >
                  Submit Review
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function Navbar({ onLogout }: { onLogout: () => void }) {
  const router = useRouter();
  
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-navy-900 flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <span className="text-xl font-bold text-navy-900">JobScale</span>
        </div>
        <div className="flex items-center space-x-8">
          <a href="/dashboard" className="text-sm text-slate-600 hover:text-navy-900 transition-colors">Dashboard</a>
          <a href="/career" className="text-sm text-slate-600 hover:text-navy-900 transition-colors">Career</a>
          <a href="/analytics" className="text-sm text-slate-600 hover:text-navy-900 transition-colors">Analytics</a>
          <div className="w-px h-6 bg-slate-200"></div>
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-full bg-teal-500 flex items-center justify-center text-white font-semibold text-sm">JD</div>
            <span className="text-sm font-medium text-navy-900">John Doe</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
