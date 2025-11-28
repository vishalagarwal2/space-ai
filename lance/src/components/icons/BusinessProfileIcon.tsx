import React from "react";

interface IconProps {
  size?: number;
  color?: string;
  className?: string;
}

export const BusinessProfileIcon: React.FC<IconProps> = ({
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
        d="M12 12C14.21 12 16 10.21 16 8C16 5.79 14.21 4 12 4C9.79 4 8 5.79 8 8C8 10.21 9.79 12 12 12ZM12 14C9.33 14 4 15.33 4 18V20H20V18C20 15.33 14.67 14 12 14Z"
        fill={color}
      />
      <path
        d="M20 10V7H18V5C18 3.9 17.1 3 16 3H8C6.9 3 6 3.9 6 5V7H4V10H20Z"
        fill={color}
        opacity="0.7"
      />
    </svg>
  );
};
