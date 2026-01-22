/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../../../templates/**/*.html",
    "./src/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        'inter': ['Inter', 'sans-serif'],
      },
      colors: {
        'docu-blue': '#3b82f6',   // Core Blue
        'docu-gold': '#FBBF24',   // Smart Gold
        'docu-dark': '#0f172a',   // Dark Slate
        'docu-base': '#f1f5f9',   // Soft Grey
      },
      borderRadius: {
        'docu-max': '3rem',       // Основной радиус секций
        'docu-input': '1.5rem',   // Радиус инпутов и кнопок
      },
      letterSpacing: {
        'docu-tight': '-0.05em',  // Для заголовков
        'docu-wide': '0.4em',     // Для лейблов и тегов
      }
    },
  },
  plugins: [],
}
