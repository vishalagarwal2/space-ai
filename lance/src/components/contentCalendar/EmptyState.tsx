import { useBusinessProfile } from "@/contexts/BusinessProfileContext";
import "./EmptyState.css";

interface EmptyStateProps {
  onGenerate: () => void;
  isGenerating: boolean;
}

export default function EmptyState({
  onGenerate,
  isGenerating,
}: EmptyStateProps) {
  const { selectedBusinessProfile } = useBusinessProfile();
  return (
    <div className="content-calendar-container">
      <div className="empty-state">
        <h2 className="empty-state-title">Content Calendar</h2>
        <p className="empty-state-description">
          Generate AI-powered content ideas for your Instagram that align with
          your brand&apos;s mission and values.
        </p>

        {selectedBusinessProfile && (
          <div className="current-profile-info">
            <p className="current-profile-text">
              Generating content for:{" "}
              <strong>{selectedBusinessProfile.name}</strong>
            </p>
          </div>
        )}

        <button
          onClick={onGenerate}
          disabled={isGenerating}
          className="generate-button"
        >
          {isGenerating ? "Generating..." : "Generate Content Calendar"}
        </button>
      </div>
    </div>
  );
}
