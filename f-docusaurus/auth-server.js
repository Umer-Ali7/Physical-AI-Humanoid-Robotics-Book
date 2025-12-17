const express = require('express');
const cors = require('cors');
const { betterAuth } = require('better-auth');
const { Pool } = require('pg');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

const connectionString = process.env.DATABASE_URL;

// Initialize PostgreSQL pool
const pool = new Pool({
  connectionString: connectionString,
  ssl: {
    rejectUnauthorized: false
  }
});

// Middleware (must be before routes)
const allowedOrigins = process.env.FRONTEND_URL
  ? process.env.FRONTEND_URL.split(',')
  : [
      'http://localhost:3000',
      'https://physical-ai-humanoid-robotics-book-ebon.vercel.app'
    ];

app.use(cors({
  origin: allowedOrigins,
  credentials: true
}));
app.use(express.json());

// Test database connection and create schema if needed
async function initializeDatabase() {
  try {
    await pool.query('SELECT NOW()');
    console.log('✅ Database connected successfully');

    // Create user table with technical_background field
    await pool.query(`
      CREATE TABLE IF NOT EXISTS "user" (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        email_verified BOOLEAN DEFAULT FALSE,
        image TEXT,
        technical_background TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // Create session table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS session (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
        expires_at TIMESTAMP NOT NULL,
        token TEXT NOT NULL UNIQUE,
        ip_address TEXT,
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // Create account table
    await pool.query(`
      CREATE TABLE IF NOT EXISTS account (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
        account_id TEXT NOT NULL,
        provider_id TEXT NOT NULL,
        access_token TEXT,
        refresh_token TEXT,
        id_token TEXT,
        access_token_expires_at TIMESTAMP,
        refresh_token_expires_at TIMESTAMP,
        scope TEXT,
        password TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(provider_id, account_id)
      );
    `);

    console.log('✅ Database schema initialized');
  } catch (error) {
    console.error('❌ Database initialization error:', error);
    throw error;
  }
}

// Custom signup endpoint to handle technical_background
app.post('/api/auth/signup-custom', async (req, res) => {
  try {
    const { name, email, password, technicalBackground } = req.body;

    if (!name || !email || !password || !technicalBackground) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'Name, email, password, and technical background are required'
      });
    }

    // Generate user ID
    const userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const accountId = `account_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Hash password
    const bcrypt = require('bcryptjs');
    const hashedPassword = await bcrypt.hash(password, 10);

    // Insert user with technical_background
    await pool.query(
      'INSERT INTO "user" (id, name, email, technical_background) VALUES ($1, $2, $3, $4)',
      [userId, name, email, technicalBackground]
    );

    // Insert account with password
    await pool.query(
      'INSERT INTO account (id, user_id, account_id, provider_id, password) VALUES ($1, $2, $3, $4, $5)',
      [accountId, userId, email, 'credential', hashedPassword]
    );

    // Create session token
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const token = `token_${Date.now()}_${Math.random().toString(36).substr(2, 16)}`;
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days

    await pool.query(
      'INSERT INTO session (id, user_id, expires_at, token) VALUES ($1, $2, $3, $4)',
      [sessionId, userId, expiresAt, token]
    );

    res.status(201).json({
      success: true,
      message: 'User created successfully',
      user: { id: userId, name, email, technicalBackground },
      session: { token, expiresAt }
    });
  } catch (error) {
    console.error('Signup error:', error);

    if (error.code === '23505') { // Unique violation
      return res.status(409).json({
        error: 'Email already exists',
        message: 'A user with this email already exists'
      });
    }

    res.status(500).json({
      error: 'Signup failed',
      message: error.message
    });
  }
});

// Custom signin endpoint
app.post('/api/auth/signin', async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'Email and password are required'
      });
    }

    // Find user by email
    const userResult = await pool.query(
      'SELECT u.*, a.password FROM "user" u JOIN account a ON u.id = a.user_id WHERE u.email = $1 AND a.provider_id = $2',
      [email, 'credential']
    );

    if (userResult.rows.length === 0) {
      return res.status(401).json({
        error: 'Invalid credentials',
        message: 'Email or password is incorrect'
      });
    }

    const user = userResult.rows[0];

    // Verify password
    const bcrypt = require('bcryptjs');
    const isValid = await bcrypt.compare(password, user.password);

    if (!isValid) {
      return res.status(401).json({
        error: 'Invalid credentials',
        message: 'Email or password is incorrect'
      });
    }

    // Create session token
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const token = `token_${Date.now()}_${Math.random().toString(36).substr(2, 16)}`;
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days

    await pool.query(
      'INSERT INTO session (id, user_id, expires_at, token) VALUES ($1, $2, $3, $4)',
      [sessionId, user.id, expiresAt, token]
    );

    res.status(200).json({
      success: true,
      message: 'Signed in successfully',
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        technicalBackground: user.technical_background
      },
      session: { token, expiresAt }
    });
  } catch (error) {
    console.error('Signin error:', error);
    res.status(500).json({
      error: 'Signin failed',
      message: error.message
    });
  }
});

// Signout endpoint
app.post('/api/auth/signout', async (req, res) => {
  try {
    const { token } = req.body;

    if (token) {
      await pool.query('DELETE FROM session WHERE token = $1', [token]);
    }

    res.status(200).json({
      success: true,
      message: 'Signed out successfully'
    });
  } catch (error) {
    console.error('Signout error:', error);
    res.status(500).json({
      error: 'Signout failed',
      message: error.message
    });
  }
});

// Get session endpoint
app.get('/api/auth/session', async (req, res) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');

    if (!token) {
      return res.status(401).json({
        error: 'Unauthorized',
        message: 'No token provided'
      });
    }

    const sessionResult = await pool.query(
      'SELECT s.*, u.name, u.email, u.technical_background FROM session s JOIN "user" u ON s.user_id = u.id WHERE s.token = $1 AND s.expires_at > NOW()',
      [token]
    );

    if (sessionResult.rows.length === 0) {
      return res.status(401).json({
        error: 'Unauthorized',
        message: 'Invalid or expired token'
      });
    }

    const session = sessionResult.rows[0];

    res.status(200).json({
      success: true,
      user: {
        id: session.user_id,
        name: session.name,
        email: session.email,
        technicalBackground: session.technical_background
      },
      session: {
        token: session.token,
        expiresAt: session.expires_at
      }
    });
  } catch (error) {
    console.error('Session error:', error);
    res.status(500).json({
      error: 'Session check failed',
      message: error.message
    });
  }
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'Authentication API',
    version: '1.0.0',
    status: 'running',
    endpoints: {
      health: 'GET /health',
      signup: 'POST /api/auth/signup-custom',
      signin: 'POST /api/auth/signin',
      signout: 'POST /api/auth/signout',
      session: 'GET /api/auth/session'
    },
    documentation: 'https://github.com/your-repo'
  });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Auth server is running' });
});

// Start server
async function startServer() {
  try {
    await initializeDatabase();
    app.listen(PORT, () => {
      console.log(`🚀 Auth server running on http://localhost:${PORT}`);
      console.log(`📡 Auth API available at http://localhost:${PORT}/api/auth`);
      console.log(`\nAvailable endpoints:`);
      console.log(`  POST /api/auth/signup-custom - Sign up with technical background`);
      console.log(`  POST /api/auth/signin - Sign in`);
      console.log(`  POST /api/auth/signout - Sign out`);
      console.log(`  GET  /api/auth/session - Get current session`);
      console.log(`  GET  /health - Health check`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();
