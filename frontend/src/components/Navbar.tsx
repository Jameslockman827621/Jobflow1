"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavbarProps {
  isLoggedIn?: boolean;
  onLogout?: () => void;
}

export default function Navbar({ isLoggedIn = false, onLogout }: NavbarProps) {
  const pathname = usePathname();
  
  const isActive = (path: string) => pathname === path;

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex-shrink-0 flex items-center">
              <span className="text-2xl font-bold text-blue-600">JobScale</span>
            </Link>
            
            {isLoggedIn && (
              <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
                <Link
                  href="/dashboard"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    isActive("/dashboard")
                      ? "border-blue-500 text-gray-900"
                      : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                  }`}
                >
                  Dashboard
                </Link>
                <Link
                  href="/profile"
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    isActive("/profile")
                      ? "border-blue-500 text-gray-900"
                      : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                  }`}
                >
                  Profile
                </Link>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-4">
            {isLoggedIn ? (
              <>
                <span className="text-sm text-gray-500 hidden sm:inline">
                  {new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                </span>
                <button
                  onClick={onLogout}
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-sm font-medium text-gray-600 hover:text-gray-900"
                >
                  Sign In
                </Link>
                <Link
                  href="/login"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
