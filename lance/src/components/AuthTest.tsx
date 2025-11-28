"use client";

import { useAuth } from "@/hooks/useAuth";
import { useBusinessProfile } from "@/contexts/BusinessProfileContext";

export default function AuthTest() {
  const { user, loading, isAuthenticated } = useAuth();
  const {
    selectedBusinessProfile,
    userType,
    isLoading: profileLoading,
    availableProfiles,
    setSelectedBusinessProfile,
  } = useBusinessProfile();

  if (loading || profileLoading) {
    return (
      <div className="p-4">Loading authentication and profile data...</div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Authentication & Profile Test</h1>

      {/* Authentication Status */}
      <div className="mb-6 p-4 border rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Authentication Status</h2>
        <p>
          <strong>Authenticated:</strong> {isAuthenticated ? "Yes" : "No"}
        </p>
        <p>
          <strong>User Type:</strong> {userType || "None"}
        </p>
        {user && (
          <div className="mt-2">
            <p>
              <strong>User Info:</strong>
            </p>
            <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto">
              {JSON.stringify(user, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Business Profile */}
      <div className="mb-6 p-4 border rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Business Profile</h2>
        {selectedBusinessProfile ? (
          <div>
            <p>
              <strong>Profile Name:</strong> {selectedBusinessProfile.name}
            </p>
            <p>
              <strong>Company:</strong> {selectedBusinessProfile.companyName}
            </p>
            <p>
              <strong>Industry:</strong>{" "}
              {selectedBusinessProfile.brandGuidelines?.industry}
            </p>
            <p>
              <strong>Primary Color:</strong>
              <span
                className="inline-block w-4 h-4 ml-2 rounded"
                style={{
                  backgroundColor:
                    selectedBusinessProfile.colorPalette?.primary,
                }}
              ></span>
              {selectedBusinessProfile.colorPalette?.primary}
            </p>

            {userType === "admin" && (
              <div className="mt-4">
                <p>
                  <strong>Available Mock Profiles:</strong>
                </p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {availableProfiles.map(profile => (
                    <button
                      key={profile.id}
                      onClick={() => setSelectedBusinessProfile(profile)}
                      className={`px-3 py-1 rounded text-sm ${
                        selectedBusinessProfile.id === profile.id
                          ? "bg-blue-500 text-white"
                          : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                      }`}
                    >
                      {profile.name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <details className="mt-4">
              <summary className="cursor-pointer font-medium">
                Full Profile Data
              </summary>
              <pre className="bg-gray-100 p-2 rounded text-sm overflow-auto mt-2">
                {JSON.stringify(selectedBusinessProfile, null, 2)}
              </pre>
            </details>
          </div>
        ) : (
          <p>No business profile available</p>
        )}
      </div>

      {/* Profile Source Info */}
      <div className="p-4 border rounded-lg bg-blue-50">
        <h2 className="text-lg font-semibold mb-2">Profile Source</h2>
        {userType === "business" && (
          <p className="text-blue-700">
            ✓ Using real business profile from API (created during onboarding)
          </p>
        )}
        {userType === "admin" && (
          <p className="text-green-700">
            ✓ Using mock business profile for admin testing (can switch between
            profiles)
          </p>
        )}
        {!userType && (
          <p className="text-red-700">✗ Not authenticated - please log in</p>
        )}
      </div>
    </div>
  );
}
