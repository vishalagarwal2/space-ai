"use client";

import React, {
  createContext,
  useContext,
  ReactNode,
  useCallback,
} from "react";
import {
  useBusinessProfile as useUnifiedBusinessProfile,
  UnifiedBusinessProfile,
} from "@/hooks/useBusinessProfile";
import {
  BusinessProfile,
  MOCK_BUSINESS_PROFILES,
} from "@/constants/mockBusinessProfiles";

// Simplified interface that matches the main hook
interface BusinessProfileContextType {
  selectedBusinessProfile: UnifiedBusinessProfile | null;
  setSelectedBusinessProfile: (profile: BusinessProfile) => void;
  availableProfiles: BusinessProfile[];
  onProfileChange: (
    callback: (profile: UnifiedBusinessProfile) => void
  ) => () => void;
  userType: "admin" | "business" | null;
  isLoading: boolean;
  refetch: () => void;
}

const BusinessProfileContext = createContext<
  BusinessProfileContextType | undefined
>(undefined);

export function BusinessProfileProvider({ children }: { children: ReactNode }) {
  const hookResult = useUnifiedBusinessProfile();

  const onProfileChange = useCallback(
    (callback: (profile: UnifiedBusinessProfile) => void) => {
      // Simple implementation - call callback when profile changes
      if (hookResult.selectedBusinessProfile) {
        callback(hookResult.selectedBusinessProfile);
      }
      return () => {}; // Return cleanup function
    },
    [hookResult.selectedBusinessProfile]
  );

  const value: BusinessProfileContextType = {
    selectedBusinessProfile: hookResult.selectedBusinessProfile,
    setSelectedBusinessProfile: hookResult.setSelectedBusinessProfile,
    availableProfiles: hookResult.availableProfiles,
    onProfileChange,
    userType: hookResult.userType?.type || null,
    isLoading: hookResult.isLoading,
    refetch: hookResult.refetch,
  };

  return (
    <BusinessProfileContext.Provider value={value}>
      {children}
    </BusinessProfileContext.Provider>
  );
}

export function useBusinessProfile() {
  const context = useContext(BusinessProfileContext);
  if (context === undefined) {
    throw new Error(
      "useBusinessProfile must be used within a BusinessProfileProvider"
    );
  }
  return context;
}

// Export the unified hook directly for components that want the full functionality
export { useUnifiedBusinessProfile };
