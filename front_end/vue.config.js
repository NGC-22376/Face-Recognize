
const { defineConfig } = require('@vue/cli-service');

module.exports = defineConfig({
  devServer: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true, 
        ws: true, 
        pathRewrite: {
          '^/api': '' 
        }
      }
    }
  },
  publicPath: '/',
  pages: {
    index: {
      entry: 'src/main.js',
      template: 'public/template.html',
      filename: 'index.html',
      title: 'Face Recognition System'
    }
  }
});
