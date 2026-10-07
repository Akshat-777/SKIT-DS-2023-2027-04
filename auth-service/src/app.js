const express = require('express');
const helmet = require('helmet');
const cors = require('cors');

const config = require('./config/env');
const authRoutes = require('./routes/authRoutes');
const errorHandler = require('./middleware/errorHandler');

const app = express();

// Security Middlewares
app.use(helmet());
app.use(cors({
  origin: [config.ALLOWED_ORIGIN, 'http://localhost:3000', 'http://localhost:5173'],
  credentials: true
}));

app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: true }));

// Health Check
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', service: 'auth-service', timestamp: new Date().toISOString() });
});

// Routes
app.use('/auth', authRoutes);

// Global Error Handler
app.use(errorHandler);

module.exports = app;
