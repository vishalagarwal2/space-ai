import type { ContentIdea } from "@/types/ContentCalendar";
import {
  formatContentDate,
  getStatusLabel,
  getStatusLabelColor,
  getStatusLabelBgColor,
  getContentTypeBadgeColor,
  getContentTypeBadgeBackgroundColor,
  getContentTypeLabel,
} from "@/types/ContentCalendar";
import "./ContentIdeaCard.css";

interface ContentIdeaCardProps {
  idea: ContentIdea;
  isSelected: boolean;
  onClick: (idea: ContentIdea) => void;
}

export default function ContentIdeaCard({
  idea,
  isSelected,
  onClick,
}: ContentIdeaCardProps) {
  return (
    <div
      className={`content-idea-card ${isSelected ? "selected" : ""}`}
      onClick={() => onClick(idea)}
    >
      <div className="idea-header">
        <div className={`idea-date-badge${isSelected ? " selected" : ""}`}>
          {formatContentDate(idea.scheduled_date)}
        </div>
        <div
          className="idea-type-badge"
          style={{
            border: `1px solid ${getContentTypeBadgeColor(idea.content_type)}`,
            backgroundColor: getContentTypeBadgeBackgroundColor(
              idea.content_type
            ),
            color: "#000",
          }}
        >
          {getContentTypeLabel(idea.content_type)}
        </div>
      </div>

      <div className="idea-content">
        <h3 className={`idea-title ${isSelected ? "selected" : ""}`}>
          {idea.title}
        </h3>
        <div
          className="idea-status-badge"
          style={{
            backgroundColor: getStatusLabelBgColor(idea.status),
            color: "#000",
          }}
        >
          {getStatusLabel(idea.status)}
        </div>
      </div>
    </div>
  );
}
