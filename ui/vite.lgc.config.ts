import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  root: '.',
  base: './',
  resolve: {
    alias: [
      { find: '@', replacement: resolve(__dirname, 'src') },
      { find: 'child_process', replacement: resolve(__dirname, 'src/shims/child-process.ts') },
      { find: 'node:child_process', replacement: resolve(__dirname, 'src/shims/child-process.ts') },
      {
        find: '@loaders.gl/worker-utils/dist/lib/process-utils/child-process-proxy.js',
        replacement: resolve(__dirname, 'src/shims/child-process-proxy.ts'),
      },
      { find: /.*\/convex\/_generated\/api/, replacement: resolve(__dirname, 'src/shims/convex-api.ts') },
      { find: /.*\/convex\/_generated\/dataModel/, replacement: resolve(__dirname, 'src/shims/convex-api.ts') },
    ],
  },
  define: {
    __APP_VERSION__: JSON.stringify('2.12.3'),
    __CLERK_JS_VERSION__: JSON.stringify('6.0.0'),
    __BUILD_HASH__: JSON.stringify('prod'),
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    target: 'esnext',
    chunkSizeWarningLimit: 4000,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
      },
    },
  },
});
