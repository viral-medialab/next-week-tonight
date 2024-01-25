/** @type {import('tailwindcss').Config} */
const withMT = require("@material-tailwind/react/utils/withMT");
module.exports = withMT({
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/*.{js,ts,jsx,tsx}",
    "./node_modules/@material-tailwind/react/components/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@material-tailwind/react/theme/components/**/*.{js,ts,jsx,tsx}",
  ],
  experimental: {
    reactRoot: true,
    workerThreads: true,
    reactMode: "concurrent",
    serverComponents: true,
    largePageDataBytes: 30 * 1024 * 1024, // Set the limit to 30MB
  },
  api: {
    bodyParser: {
      sizeLimit: "50mb", // set the body size limit to 50MB
    },
  },
  serverless: {
    // Increase the bodySize limit to 50 MB
    maxPayload: 50000000,
  },
  layers: {
    selected: {
      ".selected": {
        boxShadow: "0 0 0 3px rgba(66, 153, 225, 0.5)",
      },
    },
  },
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
      fontFamily: {
        "avenue-mono": ["Avenue Mono", "monospace"],
      },
      fontFamily: {
        arctic: ["BL Arctic", "sans-serif"],
      },
      // fontFamily: {
      //   prune: ["Prune", "sans-serif"],
      // },
      // fontFamily: {
      //   avenue: ["Avenue", "sans-serif"],
      // },
      // fontFamily: {
      //   office: ["OfficeTimesRound-Regular", "sans-serif"],
      // },
    },
  },
  plugins: [require('@tailwindcss/typography'),
  require("tailwind-scrollbar-hide")],
});
