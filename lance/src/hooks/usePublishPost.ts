import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { publishSocialMediaPost } from "@/lib/api/socialMediaPosts";
import { useConnectedAccounts } from "./useConnectedAccounts";
import axiosInstance from "@/lib/axios";

interface PublishPostParams {
  postId: string;
  renderedImageUrl?: string;
  postPreview?: {
    generated_image_url?: string;
  };
}

export function usePublishPost() {
  const { data: connectedAccounts = [] } = useConnectedAccounts();

  return useMutation({
    mutationFn: async ({
      postId,
      renderedImageUrl,
      postPreview,
    }: PublishPostParams) => {
      // Find connected Instagram account
      // Note: is_active might not be in the type but exists in the API response
      const instagramAccount = connectedAccounts.find(
        account => account.platform === "instagram"
      );

      if (!instagramAccount) {
        throw new Error(
          "No active Instagram account connected. Please connect an Instagram account first."
        );
      }

      // Check if we need to upload the rendered image
      const hasGeneratedImageUrl = postPreview?.generated_image_url;

      if (!hasGeneratedImageUrl && renderedImageUrl) {
        // We need to upload the rendered image first
        // Convert data URL to blob
        const response = await fetch(renderedImageUrl);
        const blob = await response.blob();
        const file = new File([blob], "post-image.png", { type: "image/png" });

        // Upload image and update post
        const formData = new FormData();
        formData.append("image", file);
        formData.append("post_id", postId);

        const uploadResponse = await axiosInstance.post(
          "/api/social-media/upload-image/",
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          }
        );

        if (uploadResponse.data.status !== "success") {
          throw new Error(
            uploadResponse.data.error || "Failed to upload image"
          );
        }
      }

      // Publish the post
      const result = await publishSocialMediaPost({
        post_id: postId,
        connected_account_id: instagramAccount.id,
        publish_immediately: true,
      });

      return result.data;
    },
    onSuccess: () => {
      toast.success("Post published to Instagram successfully!");
    },
    onError: (error: unknown) => {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Failed to publish post to Instagram";
      toast.error(errorMessage);
    },
  });
}
