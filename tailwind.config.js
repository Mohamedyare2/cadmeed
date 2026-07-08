/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        'brand-navy': '#071b3c',
        'brand-gold': '#e7b055',
        'brand-gold-hover': '#d39c49'
      },
      fontFamily: {
        'sans': ['Outfit', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
