/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      colors: {
        surface: {
          base: '#09090b',    // zinc-950
          card: '#18181b',    // zinc-900
          border: '#27272a',  // zinc-800
          muted: '#3f3f46',   // zinc-700
        }
      }
    },
  },
  plugins: [],
}
