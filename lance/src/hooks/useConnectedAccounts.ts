import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  getConnectedAccounts,
  initiateInstagramConnection,
  disconnectAccount,
  ConnectedAccount,
  InstagramConnectionResponse,
  DisconnectAccountResponse,
} from "@/lib/api/connectedAccounts";

export const connectedAccountsKeys = {
  all: ["connectedAccounts"] as const,
  lists: () => [...connectedAccountsKeys.all, "list"] as const,
  list: (filters: Record<string, unknown>) =>
    [...connectedAccountsKeys.lists(), { filters }] as const,
};

export function useConnectedAccounts() {
  return useQuery({
    queryKey: connectedAccountsKeys.lists(),
    queryFn: async (): Promise<ConnectedAccount[]> => {
      try {
        const response = await getConnectedAccounts();

        if (!response.success) {
          throw new Error(
            response.error || "Failed to fetch connected accounts"
          );
        }

        return response.data.accounts;
      } catch (error) {
        console.error("Error in useConnectedAccounts queryFn:", error);
        throw error;
      }
    },
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    retry: 1,
  });
}

export function useInstagramConnection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (): Promise<InstagramConnectionResponse> => {
      return await initiateInstagramConnection();
    },
    onSuccess: response => {
      if (response.data.success) {
        window.open(
          response.data.data.authorization_url,
          "_blank",
          "noopener,noreferrer"
        );

        toast.success("Instagram authorization opened in new tab");
      } else {
        if (response.data.error === "Instagram account already connected") {
          toast.info(
            "Instagram account is already connected. Refreshing data..."
          );
          queryClient.invalidateQueries({
            queryKey: connectedAccountsKeys.all,
          });
        } else {
          throw new Error(
            response.data.error || "Failed to initiate connection"
          );
        }
      }
    },
    onError: (error: unknown) => {
      let errorMessage = "Failed to connect Instagram account";
      const axiosError = error as {
        response?: { data?: { error?: string } };
        message?: string;
      };

      if (axiosError?.response?.data?.error) {
        errorMessage = axiosError.response.data.error;
      } else if (axiosError?.message) {
        errorMessage = axiosError.message;
      }

      toast.error(errorMessage);
    },
  });
}

export function useDisconnectAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      accountId,
    }: {
      accountId: string;
      platform: string;
    }): Promise<DisconnectAccountResponse> => {
      return await disconnectAccount(accountId);
    },
    onSuccess: (response, variables) => {
      if (response.success) {
        toast.success(
          `${variables.platform} account disconnected successfully`
        );

        queryClient.invalidateQueries({ queryKey: connectedAccountsKeys.all });
      } else {
        throw new Error(response.error || "Failed to disconnect account");
      }
    },
    onError: (error: unknown) => {
      let errorMessage = "Failed to disconnect account";
      const axiosError = error as {
        response?: { data?: { error?: string } };
        message?: string;
      };

      if (axiosError?.response?.data?.error) {
        errorMessage = axiosError.response.data.error;
      } else if (axiosError?.message) {
        errorMessage = axiosError.message;
      }

      toast.error(errorMessage);
    },
  });
}

export function useIsInstagramConnected() {
  const { data: accounts = [] } = useConnectedAccounts();

  return accounts.some(account => account.platform === "instagram");
}
