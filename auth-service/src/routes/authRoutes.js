const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { z } = require('zod');

const config = require('../config/env');
const userRepository = require('../db/userRepository');
const { loginRateLimiter } = require('../middleware/rateLimiter');
const { verifyToken } = require('../middleware/authMiddleware');

const router = express.Router();

// Input Schemas
const registerSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters')
});

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required')
});

const refreshSchema = z.object({
  refresh_token: z.string().min(1, 'Refresh token is required')
});

// Helpers
function generateTokens(user) {
  const payload = {
    sub: user.id,
    email: user.email,
    name: user.name,
    role: user.role
  };

  const accessToken = jwt.sign(payload, config.JWT_SECRET, {
    expiresIn: config.ACCESS_TOKEN_EXPIRES_IN
  });

  const refreshToken = jwt.sign(payload, config.JWT_REFRESH_SECRET, {
    expiresIn: config.REFRESH_TOKEN_EXPIRES_IN
  });

  return { accessToken, refreshToken };
}

/**
 * POST /auth/register
 */
router.post('/register', async (req, res, next) => {
  try {
    const parseResult = registerSchema.safeParse(req.body);
    if (!parseResult.success) {
      return res.status(400).json({
        error: {
          code: 'VALIDATION_ERROR',
          message: parseResult.error.errors.map(e => e.message).join(', ')
        }
      });
    }

    const { name, email, password } = parseResult.data;

    const existingUser = await userRepository.findByEmail(email);
    if (existingUser) {
      return res.status(409).json({
        error: {
          code: 'USER_ALREADY_EXISTS',
          message: 'An account with this email address already exists'
        }
      });
    }

    const salt = await bcrypt.genSalt(10);
    const password_hash = await bcrypt.hash(password, salt);

    const newUser = await userRepository.createUser({
      name,
      email,
      password_hash
    });

    const tokens = generateTokens(newUser);
    await userRepository.saveRefreshToken(tokens.refreshToken);

    return res.status(201).json({
      user: {
        id: newUser.id,
        name: newUser.name,
        email: newUser.email,
        role: newUser.role,
        created_at: newUser.created_at
      },
      access_token: tokens.accessToken,
      refresh_token: tokens.refreshToken,
      token_type: 'Bearer'
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /auth/login
 */
router.post('/login', loginRateLimiter, async (req, res, next) => {
  try {
    const parseResult = loginSchema.safeParse(req.body);
    if (!parseResult.success) {
      return res.status(400).json({
        error: {
          code: 'VALIDATION_ERROR',
          message: parseResult.error.errors.map(e => e.message).join(', ')
        }
      });
    }

    const { email, password } = parseResult.data;

    const user = await userRepository.findByEmail(email);
    if (!user) {
      return res.status(401).json({
        error: {
          code: 'INVALID_CREDENTIALS',
          message: 'Invalid email or password'
        }
      });
    }

    const isMatch = await bcrypt.compare(password, user.password_hash);
    if (!isMatch) {
      return res.status(401).json({
        error: {
          code: 'INVALID_CREDENTIALS',
          message: 'Invalid email or password'
        }
      });
    }

    const tokens = generateTokens(user);
    await userRepository.saveRefreshToken(tokens.refreshToken);

    return res.status(200).json({
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        role: user.role
      },
      access_token: tokens.accessToken,
      refresh_token: tokens.refreshToken,
      token_type: 'Bearer'
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /auth/refresh
 */
router.post('/refresh', async (req, res, next) => {
  try {
    const parseResult = refreshSchema.safeParse(req.body);
    if (!parseResult.success) {
      return res.status(400).json({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'refresh_token field is required'
        }
      });
    }

    const { refresh_token } = parseResult.data;

    const isValidStored = await userRepository.isRefreshTokenValid(refresh_token);
    if (!isValidStored) {
      return res.status(401).json({
        error: {
          code: 'INVALID_TOKEN',
          message: 'Refresh token has been revoked or is invalid'
        }
      });
    }

    let decoded;
    try {
      decoded = jwt.verify(refresh_token, config.JWT_REFRESH_SECRET);
    } catch (err) {
      return res.status(401).json({
        error: {
          code: 'INVALID_TOKEN',
          message: 'Expired or invalid refresh token'
        }
      });
    }

    const user = await userRepository.findById(decoded.sub);
    if (!user) {
      return res.status(401).json({
        error: {
          code: 'USER_NOT_FOUND',
          message: 'Associated user account no longer exists'
        }
      });
    }

    // Rotate refresh token
    await userRepository.revokeRefreshToken(refresh_token);
    const newTokens = generateTokens(user);
    await userRepository.saveRefreshToken(newTokens.refreshToken);

    return res.status(200).json({
      access_token: newTokens.accessToken,
      refresh_token: newTokens.refreshToken,
      token_type: 'Bearer'
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /auth/me
 */
router.get('/me', verifyToken, async (req, res, next) => {
  try {
    const user = await userRepository.findById(req.user.sub);
    if (!user) {
      return res.status(404).json({
        error: {
          code: 'USER_NOT_FOUND',
          message: 'User profile not found'
        }
      });
    }

    return res.status(200).json({
      id: user.id,
      name: user.name,
      email: user.email,
      role: user.role,
      created_at: user.created_at
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
