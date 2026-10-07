const request = require('supertest');
const app = require('../src/app');
const userRepository = require('../src/db/userRepository');

describe('Auth Service API Endpoints', () => {
  beforeEach(async () => {
    await userRepository.clearAll();
  });

  const testUser = {
    name: 'Akshat Agarwal',
    email: 'akshat@example.com',
    password: 'password123'
  };

  describe('POST /auth/register', () => {
    it('should register a new user successfully and return tokens', async () => {
      const res = await request(app)
        .post('/auth/register')
        .send(testUser);

      expect(res.statusCode).toEqual(201);
      expect(res.body).toHaveProperty('access_token');
      expect(res.body).toHaveProperty('refresh_token');
      expect(res.body.user).toHaveProperty('email', testUser.email);
      expect(res.body.user).not.toHaveProperty('password');
      expect(res.body.user).not.toHaveProperty('password_hash');
    });

    it('should return 409 Conflict if email is already registered', async () => {
      await request(app).post('/auth/register').send(testUser);
      
      const res = await request(app)
        .post('/auth/register')
        .send(testUser);

      expect(res.statusCode).toEqual(409);
      expect(res.body.error).toHaveProperty('code', 'USER_ALREADY_EXISTS');
    });

    it('should return 400 Validation Error for invalid email or short password', async () => {
      const res = await request(app)
        .post('/auth/register')
        .send({ name: 'A', email: 'invalid-email', password: '123' });

      expect(res.statusCode).toEqual(400);
      expect(res.body.error).toHaveProperty('code', 'VALIDATION_ERROR');
    });
  });

  describe('POST /auth/login', () => {
    beforeEach(async () => {
      await request(app).post('/auth/register').send(testUser);
    });

    it('should authenticate user with valid credentials', async () => {
      const res = await request(app)
        .post('/auth/login')
        .send({ email: testUser.email, password: testUser.password });

      expect(res.statusCode).toEqual(200);
      expect(res.body).toHaveProperty('access_token');
      expect(res.body).toHaveProperty('refresh_token');
      expect(res.body.user.email).toEqual(testUser.email);
    });

    it('should return 401 for incorrect password', async () => {
      const res = await request(app)
        .post('/auth/login')
        .send({ email: testUser.email, password: 'wrongpassword' });

      expect(res.statusCode).toEqual(401);
      expect(res.body.error).toHaveProperty('code', 'INVALID_CREDENTIALS');
    });
  });

  describe('POST /auth/refresh', () => {
    it('should issue a new access token when provided a valid refresh token', async () => {
      const regRes = await request(app).post('/auth/register').send(testUser);
      const refreshToken = regRes.body.refresh_token;

      const res = await request(app)
        .post('/auth/refresh')
        .send({ refresh_token: refreshToken });

      expect(res.statusCode).toEqual(200);
      expect(res.body).toHaveProperty('access_token');
      expect(res.body).toHaveProperty('refresh_token');
    });

    it('should return 401 for revoked or invalid refresh token', async () => {
      const res = await request(app)
        .post('/auth/refresh')
        .send({ refresh_token: 'invalid-refresh-token' });

      expect(res.statusCode).toEqual(401);
      expect(res.body.error).toHaveProperty('code', 'INVALID_TOKEN');
    });
  });

  describe('GET /auth/me', () => {
    it('should return 401 Unauthorized if no Authorization header is provided', async () => {
      const res = await request(app).get('/auth/me');

      expect(res.statusCode).toEqual(401);
      expect(res.body.error).toHaveProperty('code', 'UNAUTHORIZED');
    });

    it('should return current user profile when valid Bearer token is provided', async () => {
      const regRes = await request(app).post('/auth/register').send(testUser);
      const token = regRes.body.access_token;

      const res = await request(app)
        .get('/auth/me')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(200);
      expect(res.body).toHaveProperty('email', testUser.email);
      expect(res.body).toHaveProperty('name', testUser.name);
    });
  });
});
