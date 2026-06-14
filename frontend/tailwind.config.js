/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        surface:    '#1A1A1A',
        'surface-2':'#242424',
        attentive:  '#4ADE80',
        confused:   '#FACC15',
        distracted: '#F87171',
        'accent-blue': '#60A5FA',
      },
    },
  },
  plugins: [],
};
