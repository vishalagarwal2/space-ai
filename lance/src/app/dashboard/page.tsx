"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { useTabNavigation } from "@/hooks/useTabNavigation";
import Sidebar from "@/components/Sidebar";
import BusinessProfile from "@/components/BusinessProfile";
import SocialMediaManager from "@/components/SocialMediaManager";
import SocialMediaChat from "@/components/SocialMediaChat";
import ConnectedAccounts from "@/components/ConnectedAccounts";
import ContentCalendar from "@/components/ContentCalendar";
import LoadingState from "@/components/contentCalendar/LoadingState";
import "./dashboard.css";

function DashboardContent() {
  const { user, loading } = useAuth();
  const searchParams = useSearchParams();

  const getInitialTab = () => {
    const tabFromUrl = searchParams?.get("tab");
    const validTabs = [
      "dashboard",
      "content-calendar",
      "business-profile",
      "connected-accounts",
      "dev",
    ];

    if (tabFromUrl && validTabs.includes(tabFromUrl)) {
      return tabFromUrl;
    }

    return "content-calendar";
  };

  const [activeTab, setActiveTab] = useState(getInitialTab);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [showSocialMediaChat, setShowSocialMediaChat] = useState(false);

  const handleTabChange = useTabNavigation("dashboard", setActiveTab);

  if (loading) {
    return <LoadingState />;
  }

  const renderContent = () => {
    if (activeTab === "business-profile" && user) {
      return <BusinessProfile user={user} />;
    }

    if (activeTab === "content-calendar") {
      return <ContentCalendar />;
    }

    if (activeTab === "connected-accounts") {
      return <ConnectedAccounts onBack={() => handleTabChange("dashboard")} />;
    }

    if (showSocialMediaChat) {
      return <SocialMediaChat onBack={() => setShowSocialMediaChat(false)} />;
    }

    return (
      <div className="dashboard-content">
        <div className="dashboard-header">
          <h1 className="dashboard-title">Dashboard</h1>
        </div>

        <SocialMediaManager onStartChat={() => setShowSocialMediaChat(true)} />
      </div>
    );
  };

  return (
    <div className="dashboard-container">
      <Sidebar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        onCollapseChange={setIsSidebarCollapsed}
      />
      <div
        className={`main-content ${isSidebarCollapsed ? "sidebar-collapsed" : ""}`}
      >
        {renderContent()}
      </div>
    </div>
  );
}

export default function Dashboard() {
  return (
    <Suspense fallback={<LoadingState />}>
      <DashboardContent />
    </Suspense>
  );
}
