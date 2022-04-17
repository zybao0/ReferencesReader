module.exports = {
    devServer: {
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:5000/',
                // 允许跨域
                changeOrigin: true,
                ws: true,
                // pathRewrite: {
                //     '^/api': ''
                // }
            }
        }
    }
}
