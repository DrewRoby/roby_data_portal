const path = require('path');
const { VueLoaderPlugin } = require('vue-loader');

module.exports = {
  entry: './static/storycraft/js/app.js',
  output: {
    path: path.resolve(__dirname, 'static/storycraft/dist'),
    filename: 'bundle.js',
  },
  module: {
    rules: [
      {
        test: /\.vue$/,
        loader: 'vue-loader'
      },
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env']
          }
        }
      },
      {
        test: /\.css$/,
        use: ['vue-style-loader', 'css-loader']
      }
    ]
  },
  resolve: {
    alias: {
      // Vue 3 uses different runtime
      'vue$': 'vue/dist/vue.esm-bundler.js'
    },
    extensions: ['*', '.js', '.vue', '.json']
  },
  plugins: [
    new VueLoaderPlugin()
  ],
  devtool: process.env.NODE_ENV === 'production' ? 'source-map' : 'eval-source-map'
};