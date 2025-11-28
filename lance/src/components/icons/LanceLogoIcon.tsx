import React from "react";

interface IconProps {
  size?: number;
  color?: string;
  className?: string;
  strokeWidth?: number;
}

export const LanceLogoIcon: React.FC<IconProps> = ({
  size = 24,
  color = "#1EC3C8",
  className,
  strokeWidth = 2,
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <circle
        cx="8"
        cy="8"
        r="6"
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
      />
      <circle
        cx="16"
        cy="16"
        r="6"
        fill={color}
        stroke={color}
        strokeWidth={strokeWidth}
      />
    </svg>
  );
};
