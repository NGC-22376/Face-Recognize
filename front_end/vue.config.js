const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
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
  },
  publicPath: '/',
  // 使用重命名后的模板文件
  pages: {
    index: {
      entry: 'src/main.js',
      template: 'public/template.html',
      filename: 'index.html',
      title: 'Face Recognition System'
    }
  }
})
