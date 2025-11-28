import type { ContentIdea } from "@/types/ContentCalendar";
import ContentIdeaCard from "./ContentIdeaCard";
import "./ContentIdeasList.css";

interface ContentIdeasListProps {
  ideas: ContentIdea[];
  selectedIdeaId: string | null;
  onIdeaClick: (idea: ContentIdea) => void;
  onAddIdea: () => void;
}

export default function ContentIdeasList({
  ideas,
  selectedIdeaId,
  onIdeaClick,
  onAddIdea,
}: ContentIdeasListProps) {
  return (
    <div className="content-ideas-list">
      {ideas.length === 0 ? (
        <div className="no-ideas">
          <p>No content ideas yet. Click Generate to create some!</p>
        </div>
      ) : (
        ideas.map(idea => (
          <ContentIdeaCard
            key={idea.id}
            idea={idea}
            isSelected={selectedIdeaId === idea.id}
            onClick={onIdeaClick}
          />
        ))
      )}

      <button className="add-content-button" onClick={onAddIdea}>
        Click here to add a content idea
      </button>
    </div>
  );
}
