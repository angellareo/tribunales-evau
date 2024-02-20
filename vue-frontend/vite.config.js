import { fileURLToPath, URL } from 'node:url'
import { resolve } from 'node:path';
import cssInjectedByJsPlugin from "vite-plugin-css-injected-by-js";

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Check: https://github.com/ilikerobots/cookiecutter-vue-django/blob/vue3-vite/%7B%7Bcookiecutter.project_slug%7D%7D/vue_frontend/vite.config.js
export default defineConfig({
  plugins: [
    vue(),
    cssInjectedByJsPlugin({jsAssetsFilterFunction: () => true}),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    rollupOptions: {
      input: {
        main: resolve('./src/main.js'),
      },
      output: {
        dir: '../tribunales_evau/static/vue/',
        entryFileNames: '[name].js',
      },
    },
  },
})
