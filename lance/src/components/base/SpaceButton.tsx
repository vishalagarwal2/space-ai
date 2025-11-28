import { cn } from "@/lib/utils";
import "./SpaceButton.css";

type SpaceButtonVariant =
  | "primary"
  | "secondary"
  | "neutral"
  | "delete"
  | "approve";

type SpaceButtonProps = {
  variant?: SpaceButtonVariant;
  children: React.ReactNode;
  onClick?: () => void;
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
  className?: string;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
};

export function SpaceButton({
  variant = "primary",
  children,
  onClick,
  type = "button",
  disabled = false,
  className,
  onMouseEnter,
  onMouseLeave,
  ...props
}: SpaceButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      className={cn("space-button", variant, className, {
        disabled: disabled,
      })}
      {...props}
    >
      {children}
    </button>
  );
}
