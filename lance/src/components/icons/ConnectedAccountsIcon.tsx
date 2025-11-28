import React from "react";

interface IconProps {
  size?: number;
  color?: string;
  className?: string;
}

export const ConnectedAccountsIcon: React.FC<IconProps> = ({
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
        d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2Z"
        fill={color}
      />
      <path
        d="M21 9V7H15V5C15 3.9 14.1 3 13 3H11C9.9 3 9 3.9 9 5V7H3V9H21Z"
        fill={color}
      />
      <path
        d="M7 23C7 19.1 10.1 16 14 16C17.9 16 21 19.1 21 23V24H7V23Z"
        fill={color}
        opacity="0.6"
      />
      <path
        d="M17 13C15.9 13 15 13.9 15 15C15 16.1 15.9 17 17 17C18.1 17 19 16.1 19 15C19 13.9 18.1 13 17 13Z"
        fill={color}
      />
    </svg>
  );
};
