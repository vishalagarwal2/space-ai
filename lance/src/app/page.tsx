"use client";

import { useRouter } from "next/navigation";
import { SpaceIcon } from "@/components/icons/SpaceIcon";
import "./landing.css";
import { SpaceButton } from "@/components/base/SpaceButton";
import { RightChevronIcon } from "@/components/icons/RightChevron";

export default function Home() {
  const router = useRouter();

  const handleGetStarted = () => {
    router.push("/business-signup");
  };

  return (
    <div className="landing-container">
      <div className="landing-content">
        <div className="landing-logo">
          <SpaceIcon fill="#FF2E00" height={86} />
          <h1 className="landing-brand">Space AI</h1>
        </div>
        <p className="landing-tagline">
          Easily create on-brand content for your business — and let AI plan
          your entire content calendar for you.
        </p>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <SpaceButton onClick={handleGetStarted}>
            <div
              className="button-content"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                marginRight: "-8px",
              }}
            >
              Get Started <RightChevronIcon stroke="#ff4f08" size={32} />
            </div>
          </SpaceButton>
        </div>
      </div>
    </div>
  );
}
