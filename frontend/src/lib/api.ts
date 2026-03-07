/**
 * API Utility Layer
 * 
 * Centralized API client with error handling, retries, and token management.
 */

const API_BASE = '/api/v1';

interface ApiError {
  message: string;
  status: number;
  detail?: string;
}

class ApiClient {
  private baseURL: string;
  
  constructor(baseURL: string = API_BASE) {
    this.baseURL = baseURL;
  }

  /**
   * Get authentication token from localStorage
   */
  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('jobscale_token');
  }

  /**
   * Get default headers including auth token
   */
  private getHeaders(customHeaders: HeadersInit = {}): HeadersInit {
    const token = this.getToken();
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...customHeaders,
    };
  }

  /**
   * Handle API errors
   */
  private async handleError(response: Response): Promise<never> {
    let error: ApiError;
    
    try {
      const data = await response.json();
      error = {
        message: data.detail || data.message || 'An error occurred',
        status: response.status,
        detail: data.detail,
      };
    } catch {
      error = {
        message: `HTTP ${response.status}: ${response.statusText}`,
        status: response.status,
      };
    }

    // Handle specific status codes
    switch (response.status) {
      case 401:
        // Token expired or invalid - clear and redirect to login
        localStorage.removeItem('jobscale_token');
        localStorage.removeItem('jobscale_user');
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        throw new Error('Session expired. Please login again.');
      
      case 403:
        throw new Error('You do not have permission to perform this action.');
      
      case 404:
        throw new Error('The requested resource was not found.');
      
      case 429:
        throw new Error('Too many requests. Please wait a moment and try again.');
      
      case 500:
        throw new Error('Server error. Please try again later.');
      
      case 503:
        throw new Error('Service temporarily unavailable. Please try again later.');
      
      default:
        throw new Error(error.message);
    }
  }

  /**
   * Make HTTP request with retry logic
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retries = 3
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers = this.getHeaders(options.headers);

    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

        const response = await fetch(url, {
          ...options,
          headers,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          await this.handleError(response);
        }

        return await response.json();
      } catch (error: any) {
        // Don't retry on auth errors
        if (error.message.includes('expired') || error.message.includes('permission')) {
          throw error;
        }

        // Retry on network errors or server errors
        if (attempt === retries) {
          throw new Error(error.message || 'Network error. Please check your connection.');
        }

        // Wait before retry (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      }
    }

    throw new Error('Request failed after retries');
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export hooks for use in components
export function useApi() {
  return { api };
}
