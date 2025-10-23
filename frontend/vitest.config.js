import { defineConfig } from "vitest/config";
import react from '@vitejs/plugin-react';

export default defineConfig({
  test: {
    globals: true,         // así no hace falta importar test/expect
    css: true,  
    environment: "jsdom",  // aquí le decimos que use jsdom
    setupFiles: "./src/setupTests.js", // archivo de configuración adicional
    include: ['src/**/*.{test,spec}.{js,jsx}'],
  },
});
