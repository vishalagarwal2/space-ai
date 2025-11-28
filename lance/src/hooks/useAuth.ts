import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  signUp,
  login,
  verifyEmail,
  forgotPassword,
  resetPassword,
  getProfile,
  logout,
  businessSignUp,
  businessLogin,
  businessLogout,
  getAuthStatus,
} from "@/lib/api/auth";
import {
  ForgotPassword,
  LoginValues,
  ResetPassword,
  SignUpValues,
  VerifyOtpValues,
} from "@/types/Auth/authForm";

interface ApiError {
  response?: {
    data?: {
      message?: string;
    };
  };
  message?: string;
}

export const authKeys = {
  all: ["auth"] as const,
  profile: () => [...authKeys.all, "profile"] as const,
};

export function useUserProfile() {
  return useQuery({
    queryKey: authKeys.profile(),
    queryFn: async () => {
      const authStatus = await getAuthStatus();

      if (!authStatus.authenticated) {
        return null;
      }

      if (authStatus.userType === "business") {
        const businessUser = {
          ...authStatus.business,
          userType: "business",
          profile: authStatus.profile,
        };
        return businessUser;
      } else if (authStatus.userType === "admin") {
        const adminUser = {
          ...authStatus.user,
          userType: "admin",
        };
        return adminUser;
      }

      return null;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function useAuth() {
  const { data: user, isLoading: loading, error } = useUserProfile();

  return {
    user: user || null,
    loading,
    error,
    isAuthenticated: !!user,
  };
}

export function useSignUp() {
  return useMutation({
    mutationFn: async (payload: SignUpValues) => {
      const response = await signUp(payload);
      return response.data;
    },
    onSuccess: () => {
      toast.success("Account created successfully! Please verify your email.");
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.message || "Failed to create account";
      toast.error(message);
    },
  });
}

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: LoginValues) => {
      const response = await login(payload);
      return response.data;
    },
    onSuccess: () => {
      toast.success("Login successful!");
      queryClient.invalidateQueries({ queryKey: authKeys.all });
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message = apiError?.response?.data?.message || "Login failed";
      toast.error(message);
    },
  });
}

export function useVerifyEmail() {
  return useMutation({
    mutationFn: async (payload: VerifyOtpValues) => {
      const response = await verifyEmail(payload);
      return response.data;
    },
    onSuccess: () => {
      toast.success("Email verified successfully!");
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.message || "Email verification failed";
      toast.error(message);
    },
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: async (payload: ForgotPassword) => {
      const response = await forgotPassword(payload);
      return response.data;
    },
    onSuccess: () => {
      toast.success("Password reset email sent!");
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.message || "Failed to send reset email";
      toast.error(message);
    },
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: async (payload: ResetPassword) => {
      const response = await resetPassword(payload);
      return response.data;
    },
    onSuccess: () => {
      toast.success("Password reset successfully!");
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.message || "Password reset failed";
      toast.error(message);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  return useMutation({
    mutationFn: async () => {
      // Determine which logout endpoint to use based on user type
      if (user?.userType === "business") {
        const response = await businessLogout();
        return response.data;
      } else {
        const response = await logout();
        return response.data;
      }
    },
    onSuccess: () => {
      toast.success("Logged out successfully!");
      queryClient.clear();
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message = apiError?.response?.data?.message || "Logout failed";
      toast.error(message);
    },
  });
}

// Business-specific authentication hooks
export function useBusinessSignUp() {
  return useMutation({
    mutationFn: async (payload: {
      first_name: string;
      last_name: string;
      email: string;
      password: string;
    }) => {
      const response = await businessSignUp(payload);
      return response.data;
    },
    onSuccess: () => {
      toast.success("Business account created successfully!");
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.message ||
        "Failed to create business account";
      toast.error(message);
    },
  });
}

export function useBusinessLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { email: string; password: string }) => {
      const response = await businessLogin(payload);
      return response.data;
    },
    onSuccess: () => {
      toast.success("Business login successful!");
      queryClient.invalidateQueries({ queryKey: authKeys.all });
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.message || "Business login failed";
      toast.error(message);
    },
  });
}
