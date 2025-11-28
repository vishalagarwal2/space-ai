interface SpaceIconProps {
  fill?: string;
  height?: number | string; // dynamically scale without distortion
}

export function SpaceIcon({ fill = "#1ec3c8", height = 50 }: SpaceIconProps) {
  const width = (43 / 50) * Number(height);

  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 43 50"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g fill={fill}>
        <circle cx="21.5" cy="2" r="2" />
        <circle cx="21.5" cy="14.5" r="2.5" />
        <circle cx="2" cy="25" r="2" />
        <circle cx="2" cy="36" r="2" />
        <circle cx="12" cy="42" r="2" />
        <circle cx="11.5" cy="31.5" r="2.5" />
        <circle cx="21.5" cy="25.5" r="3" />
        <circle cx="21.5" cy="36.5" r="2.5" />
        <circle cx="32" cy="42" r="2" />
        <circle cx="41" cy="36" r="2" />
        <circle cx="41" cy="25" r="2" />
        <circle cx="41" cy="14" r="2" />
        <circle cx="31.5" cy="31.5" r="2.5" />
        <circle cx="31.5" cy="19.5" r="2.5" />
        <circle cx="21.5" cy="48" r="2" />
        <circle cx="2" cy="14" r="2" />
        <circle cx="11.5" cy="19.5" r="2.5" />
        <circle cx="12" cy="7" r="2" />
        <circle cx="32" cy="7" r="2" />
      </g>
    </svg>
  );
}
