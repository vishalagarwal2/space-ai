import React from "react";
import { IconProps } from "./index";

export const ShareIcon: React.FC<IconProps> = ({
  size = 24,
  color = "currentColor",
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
      <path
        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

