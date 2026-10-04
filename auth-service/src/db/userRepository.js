const { Pool } = require('pg');
const config = require('../config/env');

class UserRepository {
  constructor() {
    this.inMemoryUsersByEmail = new Map();
    this.inMemoryUsersById = new Map();
    this.inMemoryRefreshTokens = new Set();
    this.pool = null;
    this.usePostgres = false;

    if (config.DATABASE_URL && process.env.NODE_ENV !== 'test') {
      try {
        this.pool = new Pool({
          connectionString: config.DATABASE_URL,
          connectionTimeoutMillis: 2000,
        });
        this.usePostgres = true;
      } catch (err) {
        console.warn('PostgreSQL connection init failed, falling back to in-memory store:', err.message);
        this.usePostgres = false;
      }
    }
  }

  async findByEmail(email) {
    const normalizedEmail = email.toLowerCase().trim();

    if (this.usePostgres && this.pool) {
      try {
        const res = await this.pool.query('SELECT * FROM users WHERE LOWER(email) = $1', [normalizedEmail]);
        if (res.rows.length > 0) {
          const row = res.rows[0];
          return {
            id: row.id,
            email: row.email,
            name: row.name,
            password_hash: row.password_hash,
            role: row.role,
            created_at: row.created_at
          };
        }
        return null;
      } catch (err) {
        console.warn('DB query error, checking in-memory fallback:', err.message);
      }
    }

    return this.inMemoryUsersByEmail.get(normalizedEmail) || null;
  }

  async findById(id) {
    if (this.usePostgres && this.pool) {
      try {
        const res = await this.pool.query('SELECT * FROM users WHERE id = $1', [id]);
        if (res.rows.length > 0) {
          const row = res.rows[0];
          return {
            id: row.id,
            email: row.email,
            name: row.name,
            password_hash: row.password_hash,
            role: row.role,
            created_at: row.created_at
          };
        }
        return null;
      } catch (err) {
        console.warn('DB query error, checking in-memory fallback:', err.message);
      }
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

    const id = userData.id || `usr_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    const role = userData.role || 'user';
    const createdAt = new Date().toISOString();

    const user = {
      id,
      email: normalizedEmail,
      name: userData.name,
      password_hash: userData.password_hash,
      role,
      created_at: createdAt
    };

    if (this.usePostgres && this.pool) {
      try {
        await this.pool.query(
          'INSERT INTO users (id, name, email, password_hash, role, consent_given, retention_days, created_at, updated_at) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())',
          [id, userData.name, normalizedEmail, userData.password_hash, role, true, 365]
        );
      } catch (err) {
        console.warn('Postgres insert error, saving to fallback:', err.message);
      }
    }

    this.inMemoryUsersByEmail.set(normalizedEmail, user);
    this.inMemoryUsersById.set(user.id, user);
    return user;
  }

  async saveRefreshToken(token) {
    this.inMemoryRefreshTokens.add(token);
  }

  async isRefreshTokenValid(token) {
    return this.inMemoryRefreshTokens.has(token);
  }

  async revokeRefreshToken(token) {
    this.inMemoryRefreshTokens.delete(token);
  }

  async clearAll() {
    this.inMemoryUsersByEmail.clear();
    this.inMemoryUsersById.clear();
    this.inMemoryRefreshTokens.clear();
  }
}

const userRepository = new UserRepository();
module.exports = userRepository;
