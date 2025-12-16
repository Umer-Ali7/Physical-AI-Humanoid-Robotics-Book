import React, { useState, useEffect } from 'react';
import Layout from '@theme/Layout';
import BrowserOnly from '@docusaurus/BrowserOnly';
import { useColorMode } from '@docusaurus/theme-common';
import { signUpWithTechnicalBackground, signIn, signOut, getSession, User } from '../lib/auth-client';

// Client-side only component that uses useColorMode
function LoginContent() {
  const { colorMode } = useColorMode();
  const [activeTab, setActiveTab] = useState<'signin' | 'signup'>('signin');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    technicalBackground: 'Software' as 'Software' | 'Hardware' | 'Both'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [sessionLoading, setSessionLoading] = useState(true);

  // Get theme-aware styles
  const styles = getStyles(colorMode);

  // Check session on mount
  useEffect(() => {
    checkSession();
  }, []);

  const checkSession = async () => {
    setSessionLoading(true);
    try {
      const session = await getSession();
      if (session?.user) {
        setUser(session.user);
      }
    } catch (error) {
      console.error('Session check failed:', error);
    } finally {
      setSessionLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (activeTab === 'signup') {
        if (!formData.name || !formData.email || !formData.password || !formData.technicalBackground) {
          setError('All fields are required');
          setLoading(false);
          return;
        }

        await signUpWithTechnicalBackground(
          formData.name,
          formData.email,
          formData.password,
          formData.technicalBackground
        );

        // Refresh session
        await checkSession();

        // Redirect to docs
        window.location.href = '/docs/intro';
      } else {
        if (!formData.email || !formData.password) {
          setError('Email and password are required');
          setLoading(false);
          return;
        }

        await signIn(formData.email, formData.password);

        // Refresh session
        await checkSession();

        // Redirect to docs
        window.location.href = '/docs/intro';
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut();
      setUser(null);
      window.location.href = '/';
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  if (sessionLoading) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <div style={styles.header}>
            <h1 style={styles.title}>
              <span style={styles.titleGlow}>Loading...</span>
            </h1>
          </div>
        </div>
      </div>
    );
  }

  // If logged in, show user profile card
  if (user) {
    return (
      <div style={styles.container}>
          <div style={styles.card}>
            {/* Header */}
            <div style={styles.header}>
              <h1 style={styles.title}>
                <span style={styles.titleGlow}>User Profile</span>
              </h1>
              <p style={styles.subtitle}>Your cyber-physical identity</p>
            </div>

            {/* User Profile Card */}
            <div style={styles.profileCard}>
              <div style={styles.welcomeSection}>
                <h2 style={styles.welcomeText}>Welcome back,</h2>
                <h3 style={styles.userName}>{user.name}!</h3>
              </div>

              <div style={styles.profileDetails}>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Email:</span>
                  <span style={styles.detailValue}>{user.email}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Technical Background:</span>
                  <span style={styles.detailValue}>
                    {user.technicalBackground || 'Not specified'}
                  </span>
                </div>
              </div>

              <button
                onClick={handleLogout}
                style={styles.logoutButton}
              >
                Logout
              </button>

              <button
                onClick={() => window.location.href = '/docs/intro'}
                style={styles.continueButton}
              >
                Continue Learning
              </button>
            </div>

            {/* Footer */}
            <div style={styles.footer}>
              <div style={styles.footerLine}></div>
              <p style={styles.footerText}>Session Active</p>
            </div>
          </div>
        </div>
    );
  }

  // If logged out, show login/signup form
  return (
    <div style={styles.container}>
        <div style={styles.card}>
          {/* Header */}
          <div style={styles.header}>
            <h1 style={styles.title}>
              <span style={styles.titleGlow}>Authentication</span>
            </h1>
            <p style={styles.subtitle}>Access your cyber-physical workspace</p>
          </div>

          {/* Tabs */}
          <div style={styles.tabContainer}>
            <button
              style={{
                ...styles.tab,
                ...(activeTab === 'signin' ? styles.tabActive : {})
              }}
              onClick={() => {
                setActiveTab('signin');
                setError('');
              }}
            >
              Sign In
            </button>
            <button
              style={{
                ...styles.tab,
                ...(activeTab === 'signup' ? styles.tabActive : {})
              }}
              onClick={() => {
                setActiveTab('signup');
                setError('');
              }}
            >
              Sign Up
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} style={styles.form}>
            {activeTab === 'signup' && (
              <div style={styles.inputGroup}>
                <label style={styles.label}>Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  style={styles.input}
                  placeholder="Enter your name"
                  required
                />
              </div>
            )}

            <div style={styles.inputGroup}>
              <label style={styles.label}>Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                style={styles.input}
                placeholder="Enter your email"
                required
              />
            </div>

            <div style={styles.inputGroup}>
              <label style={styles.label}>Password</label>
              <div style={styles.passwordContainer}>
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  style={{ ...styles.input, paddingRight: '50px' }}
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={styles.eyeButton}
                >
                  {showPassword ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
            </div>

            {activeTab === 'signup' && (
              <div style={styles.inputGroup}>
                <label style={styles.label}>Technical Background</label>
                <select
                  name="technicalBackground"
                  value={formData.technicalBackground}
                  onChange={handleInputChange}
                  style={styles.select}
                  required
                >
                  <option value="Software">Software</option>
                  <option value="Hardware">Hardware</option>
                  <option value="Both">Both</option>
                </select>
              </div>
            )}

            {error && (
              <div style={styles.error}>
                <span style={styles.errorIcon}>⚠</span> {error}
              </div>
            )}

            <button
              type="submit"
              style={styles.submitButton}
              disabled={loading}
            >
              {loading ? (
                <span>Processing...</span>
              ) : (
                <span>{activeTab === 'signin' ? 'Sign In' : 'Sign Up'}</span>
              )}
            </button>
          </form>

          {/* Footer */}
          <div style={styles.footer}>
            <div style={styles.footerLine}></div>
            <p style={styles.footerText}>Secured Authentication</p>
          </div>
        </div>
      </div>
  );
}

// Main page component with BrowserOnly wrapper
export default function Login() {
  return (
    <Layout title="Login" description="Sign in to your account">
      <BrowserOnly fallback={<div>Loading...</div>}>
        {() => <LoginContent />}
      </BrowserOnly>
    </Layout>
  );
}

// Theme-aware styles function
function getStyles(colorMode: 'light' | 'dark'): { [key: string]: React.CSSProperties } {
  const isDark = colorMode === 'dark';

  return {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: isDark
      ? 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%)'
      : 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #dbeafe 100%)',
    padding: '20px'
  },
  card: {
    width: '100%',
    maxWidth: '450px',
    background: isDark ? 'rgba(15, 15, 25, 0.95)' : 'rgba(255, 255, 255, 0.95)',
    border: isDark ? '2px solid #00ffff' : '2px solid #0ea5e9',
    borderRadius: '16px',
    padding: '40px',
    boxShadow: isDark
      ? '0 0 40px rgba(0, 255, 255, 0.3), inset 0 0 20px rgba(0, 255, 255, 0.1)'
      : '0 0 40px rgba(14, 165, 233, 0.3), inset 0 0 20px rgba(14, 165, 233, 0.05)',
    backdropFilter: 'blur(10px)'
  },
  header: {
    textAlign: 'center',
    marginBottom: '32px'
  },
  title: {
    fontSize: '32px',
    fontWeight: '700',
    margin: '0 0 12px 0',
    color: isDark ? '#00ffff' : '#0284c7',
    textTransform: 'uppercase',
    letterSpacing: '2px'
  },
  titleGlow: {
    textShadow: isDark
      ? '0 0 20px rgba(0, 255, 255, 0.8), 0 0 40px rgba(0, 255, 255, 0.5)'
      : '0 0 20px rgba(2, 132, 199, 0.6), 0 0 40px rgba(2, 132, 199, 0.3)'
  },
  subtitle: {
    fontSize: '14px',
    color: isDark ? '#8892b0' : '#64748b',
    margin: '0',
    fontFamily: 'monospace'
  },
  profileCard: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px'
  },
  welcomeSection: {
    textAlign: 'center',
    padding: '20px',
    background: isDark ? 'rgba(0, 255, 255, 0.05)' : 'rgba(14, 165, 233, 0.1)',
    borderRadius: '12px',
    border: isDark ? '1px solid #00ffff33' : '1px solid #0ea5e966'
  },
  welcomeText: {
    fontSize: '18px',
    color: isDark ? '#8892b0' : '#64748b',
    margin: '0 0 8px 0',
    fontFamily: 'monospace'
  },
  userName: {
    fontSize: '28px',
    color: isDark ? '#00ffff' : '#0284c7',
    margin: '0',
    fontWeight: '700',
    textShadow: isDark
      ? '0 0 15px rgba(0, 255, 255, 0.6)'
      : '0 0 15px rgba(2, 132, 199, 0.4)'
  },
  profileDetails: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
    padding: '20px',
    background: isDark ? 'rgba(10, 10, 20, 0.6)' : 'rgba(248, 250, 252, 0.8)',
    borderRadius: '12px',
    border: isDark ? '1px solid #00ffff22' : '1px solid #cbd5e1'
  },
  detailRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '12px'
  },
  detailLabel: {
    fontSize: '14px',
    color: isDark ? '#00ffff' : '#0284c7',
    fontWeight: '600',
    fontFamily: 'monospace',
    textTransform: 'uppercase'
  },
  detailValue: {
    fontSize: '14px',
    color: isDark ? '#ffffff' : '#1e293b',
    fontFamily: 'monospace'
  },
  logoutButton: {
    padding: '16px',
    background: 'linear-gradient(135deg, #ff3232 0%, #cc0000 100%)',
    border: '2px solid #ff3232',
    borderRadius: '8px',
    color: '#ffffff',
    fontSize: '16px',
    fontWeight: '700',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    fontFamily: 'monospace',
    boxShadow: '0 0 20px rgba(255, 50, 50, 0.4)'
  },
  continueButton: {
    padding: '16px',
    background: isDark
      ? 'linear-gradient(135deg, #00ffff 0%, #00cccc 100%)'
      : 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
    border: isDark ? '2px solid #00ffff' : '2px solid #0ea5e9',
    borderRadius: '8px',
    color: isDark ? '#0a0a0a' : '#ffffff',
    fontSize: '16px',
    fontWeight: '700',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    fontFamily: 'monospace',
    boxShadow: isDark
      ? '0 0 20px rgba(0, 255, 255, 0.4)'
      : '0 0 20px rgba(14, 165, 233, 0.4)'
  },
  tabContainer: {
    display: 'flex',
    gap: '8px',
    marginBottom: '32px',
    borderBottom: isDark ? '2px solid #00ffff33' : '2px solid #0ea5e966'
  },
  tab: {
    flex: 1,
    padding: '12px',
    background: 'transparent',
    border: 'none',
    color: isDark ? '#8892b0' : '#64748b',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    position: 'relative',
    fontFamily: 'monospace'
  },
  tabActive: {
    color: isDark ? '#00ffff' : '#0284c7',
    textShadow: isDark
      ? '0 0 10px rgba(0, 255, 255, 0.6)'
      : '0 0 10px rgba(2, 132, 199, 0.4)',
    borderBottom: isDark ? '2px solid #00ffff' : '2px solid #0284c7'
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px'
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px'
  },
  label: {
    color: isDark ? '#00ffff' : '#0284c7',
    fontSize: '14px',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    fontFamily: 'monospace'
  },
  passwordContainer: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center'
  },
  input: {
    padding: '14px 16px',
    background: isDark ? 'rgba(10, 10, 20, 0.8)' : 'rgba(248, 250, 252, 0.9)',
    border: isDark ? '2px solid #00ffff55' : '2px solid #0ea5e999',
    borderRadius: '8px',
    color: isDark ? '#ffffff' : '#1e293b',
    fontSize: '16px',
    outline: 'none',
    transition: 'all 0.3s ease',
    fontFamily: 'monospace',
    width: '100%'
  },
  eyeButton: {
    position: 'absolute',
    right: '12px',
    background: 'transparent',
    border: 'none',
    cursor: 'pointer',
    fontSize: '20px',
    padding: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  select: {
    padding: '14px 16px',
    background: isDark ? 'rgba(10, 10, 20, 0.8)' : 'rgba(248, 250, 252, 0.9)',
    border: isDark ? '2px solid #00ffff55' : '2px solid #0ea5e999',
    borderRadius: '8px',
    color: isDark ? '#ffffff' : '#1e293b',
    fontSize: '16px',
    outline: 'none',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    fontFamily: 'monospace'
  },
  error: {
    padding: '12px 16px',
    background: isDark ? 'rgba(255, 50, 50, 0.1)' : 'rgba(239, 68, 68, 0.15)',
    border: isDark ? '2px solid #ff3232' : '2px solid #ef4444',
    borderRadius: '8px',
    color: isDark ? '#ff6b6b' : '#dc2626',
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontFamily: 'monospace'
  },
  errorIcon: {
    fontSize: '18px'
  },
  submitButton: {
    padding: '16px',
    background: isDark
      ? 'linear-gradient(135deg, #00ffff 0%, #00cccc 100%)'
      : 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
    border: isDark ? '2px solid #00ffff' : '2px solid #0ea5e9',
    borderRadius: '8px',
    color: isDark ? '#0a0a0a' : '#ffffff',
    fontSize: '16px',
    fontWeight: '700',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    fontFamily: 'monospace',
    boxShadow: isDark
      ? '0 0 20px rgba(0, 255, 255, 0.4)'
      : '0 0 20px rgba(14, 165, 233, 0.4)'
  },
  footer: {
    marginTop: '32px',
    textAlign: 'center'
  },
  footerLine: {
    height: '1px',
    background: isDark
      ? 'linear-gradient(90deg, transparent, #00ffff, transparent)'
      : 'linear-gradient(90deg, transparent, #0284c7, transparent)',
    marginBottom: '16px'
  },
  footerText: {
    color: isDark ? '#8892b0' : '#64748b',
    fontSize: '12px',
    fontFamily: 'monospace'
  }
  };
}
