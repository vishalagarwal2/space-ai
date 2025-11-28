import React from "react";

interface ArrowUpIconProps {
  size?: number;
  className?: string;
  fill?: string;
}

export const ArrowUpIcon: React.FC<ArrowUpIconProps> = ({
  size = 13,
  className,
  fill = "white",
}) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="10"
      height={size}
      viewBox="0 0 10 13"
      fill="none"
      className={className}
    >
      <path
        d="M4.41169 0.238049C4.73708 -0.0793496 5.26552 -0.0793496 5.59092 0.238049L9.75595 4.30075C10.0813 4.61814 10.0813 5.1336 9.75595 5.451C9.43056 5.7684 8.90212 5.7684 8.57673 5.451L5.83301 2.7747V12.1875C5.83301 12.6369 5.46076 13 5 13C4.53924 13 4.16699 12.6369 4.16699 12.1875V2.7747L1.42327 5.451C1.09788 5.7684 0.569439 5.7684 0.244045 5.451C-0.0813484 5.1336 -0.0813484 4.61814 0.244045 4.30075L4.40909 0.238049H4.41169Z"
        fill={fill}
      />
    </svg>
  );
};

