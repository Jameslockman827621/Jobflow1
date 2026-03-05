"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Navbar from "../../../components/Navbar";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

interface Feedback {
  clarity?: number;
  technical_depth?: number;
  structure?: number;
}

export default function InterviewCoach() {
  const router = useRouter();
  const [started, setStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [role, setRole] = useState("Software Engineer");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [sessionComplete, setSessionComplete] = useState(false);
  const [finalFeedback, setFinalFeedback] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useState(() => {
    scrollToBottom();
  });

  const handleStart = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/interview-coach/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          role: role,
          duration_minutes: 30,
          focus_areas: ["technical", "behavioral"],
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setStarted(true);
        setMessages([
          {
            role: "assistant",
            content: `Hi! I'll be conducting your mock interview today for the ${role} position. Let's start with this question:\n\n**${data.initial_question}**\n\nTake your time and answer as you would in a real interview.`,
            timestamp: Date.now(),
          },
        ]);
      }
    } catch (error) {
      console.error("Error starting interview:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/interview-coach/session_123/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: input }),
      });

      if (res.ok) {
        const data = await res.json();
        
        setFeedback(data.feedback || null);
        
        if (data.is_complete) {
          setSessionComplete(true);
        } else {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: data.follow_up_question,
              timestamp: Date.now(),
            },
          ]);
        }
      }
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleEnd = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/interview-coach/session_123/end`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        const data = await res.json();
        setFinalFeedback(data);
        setSessionComplete(true);
      }
    } catch (error) {
      console.error("Error ending interview:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  if (!started) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar isLoggedIn={true} onLogout={handleLogout} />
        <div className="max-w-2xl mx-auto py-16 px-4">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">AI Interview Coach</h1>
          <p className="text-gray-600 mb-8">
            Practice with AI that simulates real interviews. Get instant feedback and improve your skills.
          </p>

          <div className="bg-white p-6 rounded-lg shadow">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              What role are you interviewing for?
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg mb-6"
            >
              <option>Software Engineer</option>
              <option>Frontend Engineer</option>
              <option>Backend Engineer</option>
              <option>Full Stack Engineer</option>
              <option>Data Scientist</option>
              <option>Product Manager</option>
              <option>Designer</option>
            </select>

            <div className="space-y-4 mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  🎯
                </div>
                <div>
                  <p className="font-medium">Role-specific questions</p>
                  <p className="text-sm text-gray-500">Tailored to your target role</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                  ⚡
                </div>
                <div>
                  <p className="font-medium">Instant feedback</p>
                  <p className="text-sm text-gray-500">Know how you're doing in real-time</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                  📊
                </div>
                <div>
                  <p className="font-medium">Detailed scoring</p>
                  <p className="text-sm text-gray-500">Get actionable improvement tips</p>
                </div>
              </div>
            </div>

            <button
              onClick={handleStart}
              disabled={loading}
              className="w-full py-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "Starting..." : "Start Mock Interview"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar isLoggedIn={true} onLogout={handleLogout} />

      <div className="max-w-4xl mx-auto py-8 px-4">
        {!sessionComplete ? (
          <>
            {/* Chat Area */}
            <div className="bg-white rounded-lg shadow mb-4">
              <div className="p-4 border-b flex justify-between items-center">
                <div>
                  <h2 className="font-semibold">Mock Interview: {role}</h2>
                  <p className="text-sm text-gray-500">Answer naturally, as in a real interview</p>
                </div>
                <button
                  onClick={handleEnd}
                  className="px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded"
                >
                  End Interview
                </button>
              </div>

              <div className="h-96 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[80%] p-4 rounded-lg ${
                        msg.role === "user"
                          ? "bg-blue-600 text-white"
                          : "bg-gray-100 text-gray-900"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 p-4 rounded-lg">
                      <div className="flex gap-2">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="p-4 border-t">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSend()}
                    placeholder="Type your answer..."
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg"
                    disabled={loading}
                  />
                  <button
                    onClick={handleSend}
                    disabled={loading || !input.trim()}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    Send
                  </button>
                </div>
              </div>
            </div>

            {/* Real-time Feedback */}
            {feedback && (
              <div className="bg-white p-4 rounded-lg shadow">
                <h3 className="font-semibold mb-3">Real-time Feedback</h3>
                <div className="grid grid-cols-3 gap-4">
                  {Object.entries(feedback).map(([key, value]) => (
                    <div key={key}>
                      <p className="text-sm text-gray-500 capitalize">{key.replace("_", " ")}</p>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              (value as number) >= 7 ? "bg-green-500" : (value as number) >= 5 ? "bg-yellow-500" : "bg-red-500"
                            }`}
                            style={{ width: `${(value as number) * 10}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">{value}/10</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          /* Final Feedback */
          <div className="bg-white rounded-lg shadow p-8">
            <h2 className="text-2xl font-bold mb-6">Interview Complete! 🎉</h2>
            
            {finalFeedback ? (
              <>
                <div className="flex items-center gap-4 mb-8">
                  <div className="text-6xl font-bold text-blue-600">{finalFeedback.overall_score}/10</div>
                  <div>
                    <p className="text-gray-600">Overall Score</p>
                    <p className="text-sm text-gray-500">Based on {Object.keys(finalFeedback.categories).length} categories</p>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-8 mb-8">
                  <div>
                    <h3 className="font-semibold mb-3 text-green-600">✓ Strengths</h3>
                    <ul className="space-y-2">
                      {finalFeedback.strengths.map((s: string, i: number) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-green-500 mt-1">•</span>
                          <span>{s}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-3 text-orange-600">⚠ Areas to Improve</h3>
                    <ul className="space-y-2">
                      {finalFeedback.improvements.map((s: string, i: number) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-orange-500 mt-1">•</span>
                          <span>{s}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="bg-blue-50 p-6 rounded-lg">
                  <h3 className="font-semibold mb-3">💡 Tips for Next Time</h3>
                  <ul className="space-y-2">
                    {finalFeedback.tips.map((s: string, i: number) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-blue-500 mt-1">•</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <button
                  onClick={() => {
                    setStarted(false);
                    setSessionComplete(false);
                    setMessages([]);
                    setFinalFeedback(null);
                  }}
                  className="mt-8 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Practice Again
                </button>
              </>
            ) : (
              <p>Generating feedback...</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
