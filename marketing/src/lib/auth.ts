/**
 * Authentication helper for checking user authentication status
 * with the Laravel backend application.
 */

export interface AuthUser {
  id: number;
  name: string;
  email: string;
}

export interface AuthCheckResponse {
  authenticated: boolean;
  user: AuthUser | null;
}

/**
 * Check authentication status by calling the Laravel backend API.
 *
 * This function is called during SSR (server-side rendering) to determine
 * if the current user is authenticated. Cookies from the incoming request
 * are forwarded to the Laravel API to maintain session state.
 *
 * @param request - Optional Astro request object to forward cookies from
 * @returns Authentication status and user data if authenticated
 */
export async function checkAuthStatus(request?: Request): Promise<AuthCheckResponse> {
  const appUrl = import.meta.env.PUBLIC_APP_URL || 'http://localhost:8000';

  try {
    // Prepare headers
    const headers: HeadersInit = {
      'Accept': 'application/json',
    };

    // Forward cookies from the incoming request to Laravel
    if (request) {
      const cookieHeader = request.headers.get('cookie');
      if (cookieHeader) {
        headers['Cookie'] = cookieHeader;
      }
    }

    const response = await fetch(`${appUrl}/api/auth/check`, {
      credentials: 'include',
      headers,
    });

    if (!response.ok) {
      console.error(`Auth check failed: ${response.status}`);
      return { authenticated: false, user: null };
    }

    return await response.json();
  } catch (error) {
    console.error('Auth check error:', error);
    return { authenticated: false, user: null };
  }
}
