import { SpaceButton } from "../base/SpaceButton";
import { TabTitle } from "../base/TabTitle";
import "./CalendarHeader.css";

interface CalendarHeaderProps {
  onRefresh: () => void;
  onDelete: () => void;
  isGenerating: boolean;
  isDeleting: boolean;
}

export default function CalendarHeader({
  onRefresh,
  onDelete,
  isGenerating,
  isDeleting,
}: CalendarHeaderProps) {
  return (
    <div className="content-calendar-header">
      <div className="header-left">
        <TabTitle>Your planned upcoming posts</TabTitle>
        <div className="header-actions">
          <SpaceButton
            variant="neutral"
            onClick={onRefresh}
            disabled={isGenerating}
          >
            {isGenerating ? "Generating..." : "Refresh"}
          </SpaceButton>
          <SpaceButton
            variant="delete"
            onClick={onDelete}
            disabled={isDeleting}
          >
            {isDeleting ? "Deleting..." : "Delete"}
          </SpaceButton>
        </div>
      </div>
    </div>
  );
}
