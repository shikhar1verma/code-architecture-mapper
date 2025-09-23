/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#2563eb",
          light: "#3b82f6"
        },
        accent: "#eab308",
        surface: "#f8fafc",
        foreground: "#171717",
        background: "#ffffff",
      },
      fontFamily: {
        inter: ['"Inter"', 'sans-serif'],
        sans: ['"Inter"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      textColor: {
        DEFAULT: "#171717", // Set default text color to dark
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography')
  ],
}; 