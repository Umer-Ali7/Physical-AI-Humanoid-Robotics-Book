const API_BASE_URL = process.env.REACT_APP_AUTH_URL || 'https://physical-ai-humanoid-robotics-book-h9ap.onrender.com';

export interface User {
  id: string;
  name: string;
  email: string;
  technicalBackground?: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user: User;
  session: {
    token: string;
    expiresAt: string;
  };
}

// Sign up with technical background
export async function signUpWithTechnicalBackground(
  name: string,
  email: string,
  password: string,
  technicalBackground: 'Software' | 'Hardware' | 'Both'
): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/signup-custom`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      name,
      email,
      password,
      technicalBackground
    })
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || 'Signup failed');
  }

  // Store token in localStorage
  if (data.session?.token) {
    localStorage.setItem('auth_token', data.session.token);
  }

  return data;
}

// Sign in
export async function signIn(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/signin`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      email,
      password
    })
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || 'Sign in failed');
  }

  // Store token in localStorage
  if (data.session?.token) {
    localStorage.setItem('auth_token', data.session.token);
  }

  return data;
}

// Sign out
export async function signOut(): Promise<void> {
  const token = localStorage.getItem('auth_token');

  await fetch(`${API_BASE_URL}/api/auth/signout`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ token })
  });

  // Clear token from localStorage
  localStorage.removeItem('auth_token');
}

// Get current session
export async function getSession(): Promise<{ user: User } | null> {
  const token = localStorage.getItem('auth_token');

  if (!token) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/session`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include'
    });

    if (!response.ok) {
      localStorage.removeItem('auth_token');
      return null;
    }

    const data = await response.json();
    return data;
  } catch (error) {
    localStorage.removeItem('auth_token');
    return null;
  }
}

// Check if user is authenticated
export function isAuthenticated(): boolean {
  return !!localStorage.getItem('auth_token');
}
