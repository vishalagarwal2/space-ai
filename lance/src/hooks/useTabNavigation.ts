import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

/**
 * Custom hook for handling tab navigation across the application
 * @param currentRoute - The current route (e.g., "dev", "dashboard")
 * @param onTabChange - Optional callback for when tab changes (useful for updating local state)
 * @returns A function to handle tab changes
 */
export function useTabNavigation(
  currentRoute?: string,
  onTabChange?: (tab: string) => void
) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleTabChange = useCallback(
    (tab: string) => {
      if (currentRoute === "dashboard") {
        if (onTabChange) {
          onTabChange(tab);
        }

        const params = new URLSearchParams(searchParams?.toString() || "");
        if (tab === "dashboard") {
          params.delete("tab");
        } else {
          params.set("tab", tab);
        }
        router.replace(`/dashboard?${params.toString()}`, { scroll: false });
        return;
      }

      if (currentRoute === "dev") {
        if (tab === "dev") {
          return;
        }
        if (tab === "dashboard") {
          router.push("/dashboard");
        } else {
          router.push(`/dashboard?tab=${tab}`);
        }
        return;
      }

      if (tab === "dashboard") {
        router.push("/dashboard");
      } else {
        router.push(`/dashboard?tab=${tab}`);
      }
    },
    [currentRoute, router, searchParams, onTabChange]
  );

  return handleTabChange;
}
