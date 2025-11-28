import React from "react";
import "./TabTitle.css";

interface TabTitleProps {
  children: React.ReactNode;
  className?: string;
  fontSize?: string;
}

export function TabTitle({
  children,
  className = "",
  fontSize = "2rem",
}: TabTitleProps) {
  return (
    <h2 className={`tab-title ${className}`} style={{ fontSize }}>
      {children}
    </h2>
  );
}
