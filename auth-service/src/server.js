const app = require('./app');
const config = require('./config/env');

const PORT = config.PORT;

app.listen(PORT, () => {
  console.log(`[AUTH-SERVICE] Running on port ${PORT} in ${config.NODE_ENV} mode`);
});
