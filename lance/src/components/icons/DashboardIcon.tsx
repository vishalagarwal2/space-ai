import React from "react";

interface IconProps {
  size?: number;
  color?: string;
  className?: string;
}

export const DashboardIcon: React.FC<IconProps> = ({
  size = 24,
  color = "currentColor",
  className,
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
        d="M3 13H8V3H3V13ZM3 21H8V15H3V21ZM10 21H15V11H10V21ZM10 9H15V3H10V9ZM16 21H21V15H16V21ZM16 13H21V3H16V13Z"
        fill={color}
      />
    </svg>
  );
};
