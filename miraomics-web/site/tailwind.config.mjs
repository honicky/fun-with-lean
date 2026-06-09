/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Design tokens mirroring the MiraTyper page: deep navy canvas,
        // teal -> sky accent, soft off-white text. Adjust here to retune
        // the whole site's palette in one place.
        ink: {
          950: "#070B16",
          900: "#0A0F1C",
          850: "#0E1424",
          800: "#111A2E",
          700: "#16213C",
          600: "#1D2A4A",
        },
        accent: {
          DEFAULT: "#2DD4BF", // teal
          soft: "#5EEAD4",
          deep: "#0D9488",
        },
        sky: {
          DEFAULT: "#38BDF8",
        },
        mist: "#E8EEF7", // primary text
        muted: "#93A1B5", // secondary text
        line: "rgba(255,255,255,0.08)",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      maxWidth: {
        content: "72rem",
      },
      borderRadius: {
        xl2: "1.25rem",
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(45,212,191,0.25), 0 18px 60px -24px rgba(45,212,191,0.45)",
        card: "0 24px 70px -40px rgba(0,0,0,0.8)",
      },
      backgroundImage: {
        "accent-grad": "linear-gradient(135deg, #2DD4BF 0%, #38BDF8 100%)",
        "hero-glow":
          "radial-gradient(60% 60% at 70% 10%, rgba(56,189,248,0.18) 0%, rgba(45,212,191,0.10) 35%, rgba(7,11,22,0) 70%)",
      },
    },
  },
  plugins: [],
};
