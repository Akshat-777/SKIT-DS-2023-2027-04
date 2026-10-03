/**
 * UserRepository Interface
 * Current Implementation: In-Memory Map (Swappable to PostgreSQL in US2)
 */

class UserRepository {
  constructor() {
    this.usersByEmail = new Map();
    this.usersById = new Map();
    this.refreshTokens = new Set();
  }

  async findByEmail(email) {
    const normalizedEmail = email.toLowerCase().trim();
    return this.usersByEmail.get(normalizedEmail) || null;
  }

  async findById(id) {
    return this.usersById.get(id) || null;
  }

  async createUser(userData) {
    const normalizedEmail = userData.email.toLowerCase().trim();
    if (this.usersByEmail.has(normalizedEmail)) {
      const error = new Error('User already exists with this email');
      error.code = 'USER_ALREADY_EXISTS';
      throw error;
    }

    const user = {
      id: userData.id || `usr_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
      email: normalizedEmail,
      name: userData.name,
      password_hash: userData.password_hash,
      role: userData.role || 'user',
      created_at: new Date().toISOString()
    };

    this.usersByEmail.set(normalizedEmail, user);
    this.usersById.set(user.id, user);
    return user;
  }

  async saveRefreshToken(token) {
    this.refreshTokens.add(token);
  }

  async isRefreshTokenValid(token) {
    return this.refreshTokens.has(token);
  }

  async revokeRefreshToken(token) {
    this.refreshTokens.delete(token);
  }

  async clearAll() {
    this.usersByEmail.clear();
    this.usersById.clear();
    this.refreshTokens.clear();
  }
}

// Singleton repository instance for app state
const userRepository = new UserRepository();

module.exports = userRepository;
