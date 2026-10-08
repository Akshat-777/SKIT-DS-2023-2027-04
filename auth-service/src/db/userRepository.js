const path = require('path');
const config = require('../config/env');

// ---------------------------------------------------------------------------
// SQLite persistence layer (no PostgreSQL required)
// Users, refresh tokens are stored in a local .db file that survives restarts.
// Falls back to pure in-memory if better-sqlite3 is not installed.
// ---------------------------------------------------------------------------

let Database = null;
try {
  Database = require('better-sqlite3');
} catch (_) {
  console.warn('[UserRepository] better-sqlite3 not found – using in-memory store (users lost on restart).');
}

const DB_PATH = path.resolve(__dirname, '../../data/careerlens_auth.db');

class UserRepository {
  constructor() {
    this.inMemoryUsersByEmail = new Map();
    this.inMemoryUsersById    = new Map();
    this.inMemoryRefreshTokens = new Set();
    this.db = null;

    if (Database && process.env.NODE_ENV !== 'test') {
      try {
        const fs = require('fs');
        fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });

        this.db = new Database(DB_PATH);
        this._initSchema();
        console.log(`[UserRepository] SQLite connected → ${DB_PATH}`);
      } catch (err) {
        console.warn('[UserRepository] SQLite init failed, using in-memory fallback:', err.message);
        this.db = null;
      }
    }
  }

  _initSchema() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS users (
        id           TEXT PRIMARY KEY,
        email        TEXT UNIQUE NOT NULL,
        name         TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role         TEXT NOT NULL DEFAULT 'user',
        created_at   TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS refresh_tokens (
        token TEXT PRIMARY KEY,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
      );
    `);
  }

  // ── User CRUD ──────────────────────────────────────────────────────────────

  async findByEmail(email) {
    const normalizedEmail = email.toLowerCase().trim();

    if (this.db) {
      const row = this.db.prepare('SELECT * FROM users WHERE LOWER(email) = ?').get(normalizedEmail);
      if (row) return row;
    }

    return this.inMemoryUsersByEmail.get(normalizedEmail) || null;
  }

  async findById(id) {
    if (this.db) {
      const row = this.db.prepare('SELECT * FROM users WHERE id = ?').get(id);
      if (row) return row;
    }

    return this.inMemoryUsersById.get(id) || null;
  }

  async createUser(userData) {
    const normalizedEmail = userData.email.toLowerCase().trim();

    const existing = await this.findByEmail(normalizedEmail);
    if (existing) {
      const error = new Error('User already exists with this email');
      error.code = 'USER_ALREADY_EXISTS';
      throw error;
    }

    const id        = userData.id || `usr_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    const role      = userData.role || 'user';
    const createdAt = new Date().toISOString();

    const user = {
      id,
      email:         normalizedEmail,
      name:          userData.name,
      password_hash: userData.password_hash,
      role,
      created_at:    createdAt,
    };

    if (this.db) {
      try {
        this.db.prepare(
          'INSERT INTO users (id, name, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?)'
        ).run(id, userData.name, normalizedEmail, userData.password_hash, role, createdAt);
      } catch (err) {
        console.warn('[UserRepository] SQLite insert error, saving to in-memory fallback:', err.message);
      }
    }

    // Always mirror to in-memory so in-flight requests see it immediately
    this.inMemoryUsersByEmail.set(normalizedEmail, user);
    this.inMemoryUsersById.set(id, user);
    return user;
  }

  // ── Refresh token store ────────────────────────────────────────────────────

  async saveRefreshToken(token) {
    if (this.db) {
      try {
        this.db.prepare('INSERT OR IGNORE INTO refresh_tokens (token) VALUES (?)').run(token);
      } catch (_) {}
    }
    this.inMemoryRefreshTokens.add(token);
  }

  async isRefreshTokenValid(token) {
    if (this.db) {
      const row = this.db.prepare('SELECT 1 FROM refresh_tokens WHERE token = ?').get(token);
      if (row) return true;
    }
    return this.inMemoryRefreshTokens.has(token);
  }

  async revokeRefreshToken(token) {
    if (this.db) {
      try {
        this.db.prepare('DELETE FROM refresh_tokens WHERE token = ?').run(token);
      } catch (_) {}
    }
    this.inMemoryRefreshTokens.delete(token);
  }

  async clearAll() {
    if (this.db) {
      this.db.exec('DELETE FROM users; DELETE FROM refresh_tokens;');
    }
    this.inMemoryUsersByEmail.clear();
    this.inMemoryUsersById.clear();
    this.inMemoryRefreshTokens.clear();
  }
}

const userRepository = new UserRepository();
module.exports = userRepository;
