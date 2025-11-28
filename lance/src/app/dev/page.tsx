"use client";

import { useState, Suspense } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useTabNavigation } from "@/hooks/useTabNavigation";
import Sidebar from "@/components/Sidebar";
import SVGTemplateBuilder from "@/components/SVGTemplateBuilder";
import AuthTest from "@/components/AuthTest";
import LoadingState from "@/components/contentCalendar/LoadingState";
import "./dev.css";

function DevContent() {
  const { loading } = useAuth();
  const handleTabChange = useTabNavigation("dev");
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [activeDevTab, setActiveDevTab] = useState<"auth-test" | "svg-builder">(
    "auth-test"
  );

  if (loading) {
    return <LoadingState />;
  }

  return (
    <div className="dev-page-container">
      <Sidebar
        activeTab="dev"
        onTabChange={handleTabChange}
        onCollapseChange={setIsSidebarCollapsed}
      />
      <div
        className={`dev-main-content ${isSidebarCollapsed ? "sidebar-collapsed" : ""}`}
      >
        <div className="dev-tabs mb-4">
          <button
            onClick={() => setActiveDevTab("auth-test")}
            className={`px-4 py-2 mr-2 rounded ${
              activeDevTab === "auth-test"
                ? "bg-blue-500 text-white"
                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            Auth & Profile Test
          </button>
          <button
            onClick={() => setActiveDevTab("svg-builder")}
            className={`px-4 py-2 rounded ${
              activeDevTab === "svg-builder"
                ? "bg-blue-500 text-white"
                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            SVG Template Builder
          </button>
        </div>

        {activeDevTab === "auth-test" && <AuthTest />}
        {activeDevTab === "svg-builder" && (
          <SVGTemplateBuilder width={800} height={600} />
        )}
      </div>
    </div>
  );
}

export default function DevPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <DevContent />
    </Suspense>
  );
}
