function errorHandler(err, req, res, next) {
  const statusCode = err.status || err.statusCode || 500;
  const errorCode = err.code || 'INTERNAL_SERVER_ERROR';
  const errorMessage = err.message || 'An unexpected error occurred';

  // Prevent PII leakage in error logs
  console.error(`[ERROR] Code: ${errorCode} | Status: ${statusCode}`);

  res.status(statusCode).json({
    error: {
      code: errorCode,
      message: errorMessage
    }
  });
}

module.exports = errorHandler;
