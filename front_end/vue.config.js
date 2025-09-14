const { defineConfig } = require('@vue/cli-service')
module.exports = {
  devServer: {
    proxy: {
      '/login': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      },
      '/register': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      }
    }
  }
}
