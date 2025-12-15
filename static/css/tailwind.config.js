module.exports = {
  darkMode: 'class', // Enables dark mode via class (add 'dark' to <html> tag)
  theme: {
    extend: {
      colors: {
        background: '#121212', // Main bg
        surface: '#1E1E1E', // Cards, panels
        text: '#E0E0E0', // Primary text
        muted: '#A0A0A0', // Secondary text
        accent: '#BB86FC', // Buttons, highlights (purple for premium feel)
        secondary: '#03DAC6', // Success/available indicators
        danger: '#CF6679', // Errors, delete buttons
        border: '#333333', // Borders/dividers
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'], // Modern, clean font like Pinterest
      },
    },
  },
  plugins: [require('@tailwindcss/aspect-ratio')], // For image ratios
};