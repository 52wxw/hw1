module.exports = {
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost', // 后端服务入口（Docker Compose部署时）
        changeOrigin: true,
        pathRewrite: { '^/api': '/api' }
      }
    }
  },
  transpileDependencies: true
};
