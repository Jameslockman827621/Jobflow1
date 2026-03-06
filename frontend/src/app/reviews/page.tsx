"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Navbar from "../../components/Navbar";

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
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-xl text-gray-600">Loading reviews...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar isLoggedIn={true} onLogout={handleLogout} />

      <main className="max-w-6xl mx-auto py-8 px-4">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Company Reviews</h1>
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {showForm ? "Cancel" : "Write a Review"}
          </button>
        </div>

        {showForm && (
          <div className="bg-white p-6 rounded-lg shadow mb-8">
            <h2 className="text-xl font-semibold mb-4">Write a Review</h2>
            <form onSubmit={handleSubmitReview} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  placeholder="e.g., Google, Stripe"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Overall Rating *
                </label>
                <select
                  value={formData.overall_rating}
                  onChange={(e) => setFormData({ ...formData, overall_rating: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                >
                  {[5, 4, 3, 2, 1].map((rating) => (
                    <option key={rating} value={rating}>
                      {rating} Star{rating > 1 ? "s" : ""}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title *
                </label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  placeholder="e.g., Great place to work"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Pros *
                </label>
                <textarea
                  required
                  value={formData.pros}
                  onChange={(e) => setFormData({ ...formData, pros: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  rows={3}
                  placeholder="What did you like about working here?"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cons *
                </label>
                <textarea
                  required
                  value={formData.cons}
                  onChange={(e) => setFormData({ ...formData, cons: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  rows={3}
                  placeholder="What could be improved?"
                />
              </div>
              <button
                type="submit"
                className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Submit Review
              </button>
            </form>
          </div>
        )}

        <div className="grid md:grid-cols-3 gap-8">
          {/* Companies List */}
          <div className="md:col-span-1">
            <div className="bg-white p-4 rounded-lg shadow">
              <h2 className="font-semibold mb-4">Companies</h2>
              <div className="space-y-2">
                {companies.map((company) => (
                  <button
                    key={company.name}
                    onClick={() => {
                      setSelectedCompany(company.name);
                      fetchCompanyReviews(company.name);
                    }}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedCompany === company.name
                        ? "bg-blue-50 border-blue-500"
                        : "bg-gray-50 hover:bg-gray-100"
                    }`}
                  >
                    <div className="font-medium">{company.name}</div>
                    <div className="text-sm text-gray-500">
                      {company.review_count} reviews • ⭐ {company.avg_rating}
                    </div>
                  </button>
                ))}
                {companies.length === 0 && (
                  <p className="text-sm text-gray-500">No reviews yet. Be the first!</p>
                )}
              </div>
            </div>
          </div>

          {/* Reviews */}
          <div className="md:col-span-2">
            {selectedCompany && reviews ? (
              <div className="space-y-6">
                {/* Company Header */}
                <div className="bg-white p-6 rounded-lg shadow">
                  <h2 className="text-2xl font-bold mb-4">{reviews.company_name}</h2>
                  <div className="flex items-center gap-6">
                    <div className="text-center">
                      <div className="text-4xl font-bold text-blue-600">
                        {reviews.average_ratings.overall}
                      </div>
                      <div className="text-sm text-gray-500">Overall</div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 flex-1">
                      <div>
                        <div className="text-sm text-gray-500">Work-Life Balance</div>
                        <div className="font-semibold">{reviews.average_ratings.work_life_balance}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">Culture</div>
                        <div className="font-semibold">{reviews.average_ratings.culture}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">Compensation</div>
                        <div className="font-semibold">{reviews.average_ratings.compensation}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">Career Opportunities</div>
                        <div className="font-semibold">{reviews.average_ratings.career_opportunities}</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Reviews List */}
                <div className="space-y-4">
                  {reviews.reviews && reviews.reviews.map((review: any) => (
                    <div key={review.id} className="bg-white p-6 rounded-lg shadow">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="font-semibold text-lg">{review.title}</h3>
                          <div className="text-sm text-gray-500">
                            {review.job_title} • {review.employment_status}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-yellow-500">★</span>
                          <span className="font-semibold">{review.overall_rating}</span>
                        </div>
                      </div>
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <div className="font-medium text-green-600 mb-2">👍 Pros</div>
                          <p className="text-gray-700">{review.pros}</p>
                        </div>
                        <div>
                          <div className="font-medium text-red-600 mb-2">👎 Cons</div>
                          <p className="text-gray-700">{review.cons}</p>
                        </div>
                      </div>
                      <div className="mt-4 text-sm text-gray-400">
                        Posted {new Date(review.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-white p-12 rounded-lg shadow text-center">
                <div className="text-4xl mb-4">🏢</div>
                <h3 className="text-xl font-semibold mb-2">Select a Company</h3>
                <p className="text-gray-500">
                  Choose a company from the list to see reviews, or write your own.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
