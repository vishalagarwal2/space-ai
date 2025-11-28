import axiosInstance from "../axios";

export interface ConnectedAccount {
  id: string;
  platform: "instagram" | "linkedin" | "twitter" | "facebook";
  username: string;
  display_name: string;
  profile_picture_url: string;
  is_verified: boolean;
  last_sync_at: string | null;
  created_at: string;
  granted_scopes: string[];
  permissions: Record<string, unknown>;
}

export interface InstagramConnectionResponse {
  data: {
    success: boolean;
    data: {
      authorization_url: string;
      state: string;
    };
    error?: string;
  };
  status: number;
  statusText: string;
}

export interface ConnectedAccountsResponse {
  success: boolean;
  data: {
    accounts: ConnectedAccount[];
    total: number;
  };
  error?: string;
}

export const getConnectedAccounts =
  async (): Promise<ConnectedAccountsResponse> => {
    try {
      const url = "/api/knowledge-base/connected-accounts/";
      const response = await axiosInstance.get(url);
      return response.data;
    } catch (error: unknown) {
      const axiosError = error as {
        message?: string;
        code?: string;
        response?: unknown;
        request?: unknown;
        config?: unknown;
      };
      console.error("Error details:", {
        message: axiosError?.message,
        code: axiosError?.code,
        response: axiosError?.response,
        request: axiosError?.request,
        config: axiosError?.config,
      });

      if (!axiosError.response && axiosError.request) {
        console.error(
          "Request was made but no response received (network/CORS issue?)"
        );
      } else if (!axiosError.request) {
        console.error("Request was never made (error before sending)");
      }

      throw error;
    }
  };

export const initiateInstagramConnection =
  async (): Promise<InstagramConnectionResponse> => {
    return axiosInstance.post(
      "/api/knowledge-base/connected-accounts/instagram/connect/"
    );
  };

export interface DisconnectAccountResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export const disconnectAccount = async (
  accountId: string
): Promise<DisconnectAccountResponse> => {
  const response = await axiosInstance.delete(
    `/api/knowledge-base/connected-accounts/${accountId}/disconnect/`
  );
  return response.data;
};

export const postToInstagram = async (payload: {
  account_id: string;
  content: string;
  image_url: string;
  post_type?: "POST" | "STORY";
}) => {
  return axiosInstance.post(
    "/api/knowledge-base/connected-accounts/instagram/post/",
    payload
  );
};
