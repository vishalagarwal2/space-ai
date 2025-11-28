import {
  ForgotPassword,
  LoginValues,
  ResetPassword,
  SignUpValues,
  VerifyOtpValues,
} from "@/types/Auth/authForm";
import axiosInstance from "../axios";

// Admin authentication functions
export const signUp = async (payload: SignUpValues) => {
  return axiosInstance.post("/api/auth/register/", payload);
};

export const login = async (payload: LoginValues) => {
  return axiosInstance.post("/api/auth/login/", payload);
};

export const verifyEmail = async (payload: VerifyOtpValues) => {
  return axiosInstance.post("/api/auth/verify-otp/", payload);
};

export const forgotPassword = async (payload: ForgotPassword) => {
  return axiosInstance.post("/api/auth/forgot-password/", payload);
};

export const resetPassword = async (payload: ResetPassword) => {
  return axiosInstance.post("/api/auth/reset-password/", payload);
};

export const getProfile = async () => {
  return axiosInstance.get("/api/user/profile/");
};

export const logout = async () => {
  return axiosInstance.post("/api/auth/logout/");
};

// Business authentication functions
export const businessSignUp = async (payload: {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}) => {
  return axiosInstance.post("/api/business/auth/register/", payload);
};

export const businessLogin = async (payload: {
  email: string;
  password: string;
}) => {
  return axiosInstance.post("/api/business/auth/login/", payload);
};

export const businessLogout = async () => {
  return axiosInstance.post("/api/business/auth/logout/");
};

export const getBusinessProfile = async () => {
  return axiosInstance.get("/api/business/profile/");
};

// Unified auth status check
export const getAuthStatus = async () => {
  // First check business auth
  try {
    const businessResponse = await axiosInstance.get(
      "/api/business/auth/status/"
    );

    if (businessResponse.data.authenticated) {
      const result = {
        ...businessResponse.data,
        userType: "business",
      };
      return result;
    }
  } catch (error) {
    // Business auth failed, continue to admin auth
  }

  // Check admin auth
  try {
    const adminResponse = await axiosInstance.get("/api/auth/status/");

    if (adminResponse.data.authenticated) {
      const result = {
        ...adminResponse.data,
        userType: "admin",
      };
      return result;
    }
  } catch (error) {
    // Admin auth failed
  }

  return {
    authenticated: false,
    userType: null,
  };
};
