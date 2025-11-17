/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        'factory-dark': '#111827', // gray-900
        'factory-accent': '#06b6d4', // cyan-500
      },
      backgroundColor: {
        'factory-dark': '#111827',
      }
    },
  },
  plugins: [],
}

