import axios from "axios";

let API_URL: string = "http://localhost:8000";

if (typeof window !== "undefined") {
  // Client-side-only code
  let host = window.location.hostname;
  let port = window.location.port;
  let protocol = window.location.protocol;
  API_URL = protocol + "//" + host + ":" + port;
}


export { API_URL }

const axiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || API_URL, // Changed to localhost for development
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true",
  },
});

export default axiosInstance;
