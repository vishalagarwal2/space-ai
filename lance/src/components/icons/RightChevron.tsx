import React from "react";

interface RightChevronIconProps {
  size?: number;
  stroke?: string;
}

export const RightChevronIcon: React.FC<RightChevronIconProps> = ({
  stroke = "#f4f08",
  size = 24,
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      stroke={stroke}
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="miter"
    >
      <polyline points="11 17 16 12 11 7"></polyline>
    </svg>
  );
};
