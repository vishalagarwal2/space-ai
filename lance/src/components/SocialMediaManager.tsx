"use client";

import React from "react";
import { InstagramIcon, ArrowRightIcon } from "./icons";
import "./SocialMediaManager.css";

interface SocialMediaManagerProps {
  onStartChat: () => void;
}

export default function SocialMediaManager({
  onStartChat,
}: SocialMediaManagerProps) {
  return (
    <div className="instagram-card">
      <div className="instagram-gradient">
        <div className="instagram-content">
          <div className="instagram-logo">
            <InstagramIcon size={28} color="white" />
          </div>
          <h3 className="instagram-card-title">Make an Instagram Post</h3>
          <p className="instagram-card-description">
            Create engaging posts for your business with AI-powered content
            generation
          </p>
          <button className="instagram-button" onClick={onStartChat}>
            <span>Start Creating</span>
            <ArrowRightIcon size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
