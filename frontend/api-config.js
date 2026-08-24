// ==========================================================
// PENSIONIQ GHANA
// API CONFIGURATION
// ==========================================================


// Local development API
const LOCAL_API_BASE_URL =
    "http://127.0.0.1:8000";


// Production Render API
const PRODUCTION_API_BASE_URL =
    "https://pensioniq-ghana.onrender.com";


// Detect whether we are running locally
const isLocalDevelopment =
    window.location.hostname === "127.0.0.1"
    ||
    window.location.hostname === "localhost";


// Make the API URL available to all frontend JavaScript files
window.PENSIONIQ_API_BASE_URL =
    isLocalDevelopment
        ? LOCAL_API_BASE_URL
        : PRODUCTION_API_BASE_URL;