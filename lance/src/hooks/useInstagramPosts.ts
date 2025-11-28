import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createInstagramPost,
  getInstagramPosts,
  postToInstagramAPI,
  InstagramPost,
  CreateInstagramPostRequest,
} from "@/lib/api/socialMedia";

const instagramPostKeys = {
  all: ["instagram-posts"] as const,
  lists: () => [...instagramPostKeys.all, "list"] as const,
  list: (filters: string) =>
    [...instagramPostKeys.lists(), { filters }] as const,
};

export const useInstagramPosts = () => {
  return useQuery({
    queryKey: instagramPostKeys.lists(),
    queryFn: async () => {
      const response = await getInstagramPosts();
      return response.data.data as InstagramPost[];
    },
  });
};

export const useCreateInstagramPost = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateInstagramPostRequest) => {
      const response = await createInstagramPost(payload);
      return response.data.data as InstagramPost;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: instagramPostKeys.lists() });
    },
  });
};

export const usePostToInstagram = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (postId: number | string) => {
      const response = await postToInstagramAPI(postId);
      return response.data.data as InstagramPost;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: instagramPostKeys.lists() });
    },
  });
};
