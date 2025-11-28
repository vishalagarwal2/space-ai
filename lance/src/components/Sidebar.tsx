"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import {
  CollapseIcon,
  ArrowRightIcon,
  ChevronDownIcon,
  LogoutIcon,
  DashboardIcon,
  BusinessProfileIcon,
  ConnectedAccountsIcon,
  CalendarIcon,
  DevIcon,
} from "./icons";
import "./Sidebar.css";
import { SpaceIcon } from "./icons/SpaceIcon";
import { useBusinessProfile } from "@/contexts/BusinessProfileContext";
import { useAuth, useLogout } from "@/hooks/useAuth";

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  onCollapseChange?: (isCollapsed: boolean) => void;
}

export default function Sidebar({
  activeTab,
  onTabChange,
  onCollapseChange,
}: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { user } = useAuth();
  const logoutMutation = useLogout();
  const {
    selectedBusinessProfile,
    setSelectedBusinessProfile,
    availableProfiles,
    isLoading,
  } = useBusinessProfile();
  const profileColor =
    selectedBusinessProfile?.colorPalette.primary ?? "#E2E8F0";
  const profileName =
    selectedBusinessProfile?.name ??
    (isLoading ? "Loading profile..." : "Business Profile");
  const profileLogo = selectedBusinessProfile?.logoUrl;
  const profileId = selectedBusinessProfile?.id;

  const isBusinessUser = user?.userType === "business";

  const allMenuItems = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: DashboardIcon,
      showForBusiness: false, // Business users don't see dashboard
    },
    {
      id: "content-calendar",
      label: "Content Calendar",
      icon: CalendarIcon,
      showForBusiness: true, // Business users see content calendar
    },
    {
      id: "business-profile",
      label: "Business Profile",
      icon: BusinessProfileIcon,
      showForBusiness: true, // Business users see business profile
    },
    {
      id: "connected-accounts",
      label: "Connected Accounts",
      icon: ConnectedAccountsIcon,
      showForBusiness: true,
    },
    {
      id: "dev",
      label: "Dev Canvas",
      icon: DevIcon,
      showForBusiness: false, // Business users don't see dev canvas
    },
  ];

  // Filter menu items based on user type
  const menuItems = isBusinessUser
    ? allMenuItems.filter(item => item.showForBusiness)
    : allMenuItems;

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleLogout = async () => {
    // Capture user type before logout (since logout clears the cache)
    const userType = user?.userType;
    try {
      await logoutMutation.mutateAsync();
      // Redirect based on user type
      if (userType === "business") {
        router.push("/business-login");
      } else {
        router.push("/login");
      }
    } catch (error) {
      console.error("Logout error:", error);
      // Fallback redirect based on user type
      if (userType === "business") {
        router.push("/business-login");
      } else {
        router.push("/login");
      }
    }
  };

  return (
    <div className={`sidebar ${isCollapsed ? "collapsed" : ""}`}>
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="logo-icon">
            <SpaceIcon fill="#ff2e01" height={32} />
          </div>
          <span className="logo-text">Space AI</span>
        </div>
        <button
          className="collapse-button"
          onClick={() => {
            const newCollapsed = !isCollapsed;
            setIsCollapsed(newCollapsed);
            onCollapseChange?.(newCollapsed);
          }}
        >
          {isCollapsed ? (
            <ArrowRightIcon size={16} />
          ) : (
            <CollapseIcon size={16} />
          )}
        </button>
      </div>

      <nav className="sidebar-nav">
        <ul className="nav-list">
          {menuItems.map(item => {
            const IconComponent = item.icon;
            return (
              <li key={item.id} className="nav-item">
                <button
                  className={`nav-button ${activeTab === item.id ? "active" : ""}`}
                  onClick={() => {
                    if (item.id === "dev") {
                      router.push("/dev");
                    } else {
                      onTabChange(item.id);
                    }
                  }}
                  title={isCollapsed ? item.label : undefined}
                >
                  <div className="nav-icon">
                    <IconComponent size={22} />
                  </div>
                  {!isCollapsed && (
                    <span className="nav-label">{item.label}</span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="sidebar-footer">
        <div className="user-info-container" ref={dropdownRef}>
          <div
            className="user-info"
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          >
            <div
              className="user-avatar"
              style={{
                backgroundColor: profileColor,
              }}
            >
              {profileLogo ? (
                <Image
                  src={profileLogo}
                  alt={profileName}
                  width={24}
                  height={24}
                  style={{
                    borderRadius: "50%",
                    objectFit: "cover",
                  }}
                />
              ) : (
                <BusinessProfileIcon size={24} />
              )}
            </div>
            {!isCollapsed && (
              <>
                <div className="user-details">
                  <div className="user-name">{profileName}</div>
                  <div className="user-role">Business Profile</div>
                </div>
                <div className="dropdown-arrow">
                  <ChevronDownIcon size={16} />
                </div>
              </>
            )}
          </div>

          {isDropdownOpen && (
            <div className="user-dropdown">
              {availableProfiles.map(profile => (
                <button
                  key={profile.id}
                  className={`dropdown-item ${profile.id === profileId ? "active" : ""}`}
                  onClick={() => {
                    setSelectedBusinessProfile(profile);
                    setIsDropdownOpen(false);
                  }}
                >
                  <div
                    className="profile-avatar"
                    style={{ backgroundColor: profile.colorPalette.primary }}
                  >
                    {profile.logoUrl ? (
                      <Image
                        src={profile.logoUrl}
                        alt={profile.name}
                        width={16}
                        height={16}
                        style={{
                          borderRadius: "50%",
                          objectFit: "cover",
                        }}
                      />
                    ) : (
                      <BusinessProfileIcon size={16} />
                    )}
                  </div>
                  {!isCollapsed && <span>{profile.name}</span>}
                </button>
              ))}
              <div className="dropdown-divider" />
              <button
                className="dropdown-item logout-button"
                onClick={handleLogout}
              >
                <LogoutIcon size={16} />
                {!isCollapsed && <span>Logout</span>}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
