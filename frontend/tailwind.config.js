/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f2f8f5',
          100: '#e1efe8',
          200: '#c5dfd3',
          300: '#9bc8b6',
          400: '#6ca992',
          500: '#4c8d76',
          600: '#3a725e',
          700: '#305c4d',
          800: '#274b3f',
          900: '#213f36',
          950: '#11241f',
        },
        accent: {
          50: '#fdfbe7',
          100: '#fbf7c4',
          200: '#f7ee8a',
          300: '#f1dd49',
          400: '#eac51b',
          500: '#d7ab10',
          600: '#ba880c',
          700: '#94630e',
          800: '#794e13',
          900: '#684216',
          950: '#3c2207',
        },
        earth: {
          50: '#f8f6f3',
          100: '#ece7df',
          200: '#d9cfbf',
          300: '#c0ad97',
          400: '#a68c72',
          500: '#92765c',
          600: '#816550',
          700: '#6c5143',
          800: '#594339',
          900: '#4a3831',
          950: '#261c18',
        }
      },
      fontFamily: {
        sans: ['DM Sans', 'sans-serif'],
        serif: ['Fraunces', 'serif'],
      }
    },
  },
  plugins: [],
}
