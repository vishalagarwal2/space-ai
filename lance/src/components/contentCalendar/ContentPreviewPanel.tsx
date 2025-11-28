import { useState, useMemo, useEffect } from "react";
import type { ContentIdea } from "@/types/ContentCalendar";
import type { SocialMediaPost } from "@/lib/api/socialMediaPosts";
import {
  getTemplatesByContentType,
  getRandomTemplateForContentType,
  type TemplateId,
} from "@/config/templates";
import { useBusinessProfile } from "@/contexts/BusinessProfileContext";
import { updateContentIdea } from "@/lib/api/contentCalendar";
import EditableField from "./EditableField";
import SocialMediaPostWrapper from "../SocialMediaPostWrapper";
import "./ContentPreviewPanel.css";
import { SpaceButton } from "../base/SpaceButton";
import { TabTitle } from "../base/TabTitle";

interface ContentPreviewPanelProps {
  idea: ContentIdea;
  generatedPost: SocialMediaPost | null;
  editingField: "title" | "description" | null;
  editValues: { title: string; description: string };
  isUpdating: boolean;
  isGeneratingPost: boolean;
  isApproving: boolean;
  onStartEdit: (field: "title" | "description") => void;
  onCancelEdit: () => void;
  onSaveEdit: () => void;
  onUpdateEditValue: (field: "title" | "description", value: string) => void;
  onGeneratePost: (
    selectedTemplate?: string,
    postFormat?: "single" | "carousel"
  ) => void;
  onApprove: () => void;
  onSaveDraft?: (postId: string) => void;
  onPublish?: (postId: string) => void;
  onIdeaUpdate?: (updatedIdea: ContentIdea) => void;
  showTemplateDropdown?: boolean;
}

export default function ContentPreviewPanel({
  idea,
  generatedPost,
  editingField,
  editValues,
  isUpdating,
  isGeneratingPost,
  isApproving,
  onStartEdit,
  onCancelEdit,
  onSaveEdit,
  onUpdateEditValue,
  onGeneratePost,
  onApprove,
  onSaveDraft,
  onPublish,
  onIdeaUpdate,
  showTemplateDropdown = true,
}: ContentPreviewPanelProps) {
  const { selectedBusinessProfile } = useBusinessProfile();

  const [isHoveringScheduleButton, setIsHoveringScheduleButton] =
    useState(false);
  const [isSavingChanges, setIsSavingChanges] = useState(false);

  const availableTemplatesForContentType = getTemplatesByContentType(
    idea.content_type,
    selectedBusinessProfile?.id
  );

  const savedTemplate = useMemo(() => {
    if (idea.selected_template) {
      return idea.selected_template as TemplateId;
    }
    return getRandomTemplateForContentType(
      idea.content_type,
      selectedBusinessProfile?.id
    );
  }, [idea.selected_template, idea.content_type, selectedBusinessProfile?.id]);

  const [selectedTemplate, setSelectedTemplate] =
    useState<TemplateId>(savedTemplate);
  const [selectedPostFormat, setSelectedPostFormat] = useState<
    "single" | "carousel"
  >(idea.post_format);

  useEffect(() => {
    setSelectedTemplate(savedTemplate);
  }, [savedTemplate]);

  useEffect(() => {
    setSelectedPostFormat(idea.post_format);
  }, [idea.post_format]);

  const hasUnsavedChanges =
    selectedTemplate !== savedTemplate ||
    selectedPostFormat !== idea.post_format;

  const handleTemplateChange = (newTemplate: TemplateId) => {
    setSelectedTemplate(newTemplate);
  };

  const handlePostFormatChange = (newFormat: "single" | "carousel") => {
    setSelectedPostFormat(newFormat);
  };

  const handleSaveChanges = async () => {
    if (!hasUnsavedChanges) return;

    setIsSavingChanges(true);
    try {
      const updates: {
        selected_template?: string;
        post_format?: "single" | "carousel";
      } = {};

      if (selectedTemplate !== savedTemplate) {
        updates.selected_template = selectedTemplate;
      }

      if (selectedPostFormat !== idea.post_format) {
        updates.post_format = selectedPostFormat;
      }

      const response = await updateContentIdea(idea.id, updates);

      if (response.success && response.data && onIdeaUpdate) {
        onIdeaUpdate(response.data);
      }
    } catch (error) {
      console.error("Failed to save changes:", error);
    } finally {
      setIsSavingChanges(false);
    }
  };

  return (
    <div className="content-preview-panel">
      <div className="preview-card">
        <div style={{ marginBottom: "1rem" }}>
          <TabTitle fontSize="1.6rem">Post Preview</TabTitle>
        </div>

        <div className="preview-content">
          <EditableField
            label="Topic:"
            value={idea.title}
            isEditing={editingField === "title"}
            editValue={editValues.title}
            onStartEdit={() => onStartEdit("title")}
            onCancelEdit={onCancelEdit}
            onSaveEdit={onSaveEdit}
            onChange={value => onUpdateEditValue("title", value)}
            isSaving={isUpdating}
          />

          <EditableField
            label="Description:"
            value={idea.description}
            isEditing={editingField === "description"}
            editValue={editValues.description}
            onStartEdit={() => onStartEdit("description")}
            onCancelEdit={onCancelEdit}
            onSaveEdit={onSaveEdit}
            onChange={value => onUpdateEditValue("description", value)}
            isSaving={isUpdating}
            multiline
          />

          <div className="post-format-selector">
            <label htmlFor="post-format-select" className="post-format-label">
              Format:
            </label>
            <select
              id="post-format-select"
              value={selectedPostFormat}
              onChange={e => {
                const newFormat = e.target.value as "single" | "carousel";
                handlePostFormatChange(newFormat);
              }}
              className="post-format-dropdown"
            >
              <option value="single">📄 Single Post</option>
              <option value="carousel">🎠 Carousel</option>
            </select>
          </div>

          {generatedPost && (
            <>
              {showTemplateDropdown && (
                <div className="template-selector">
                  <label htmlFor="template-select" className="template-label">
                    Template:
                  </label>
                  <select
                    id="template-select"
                    value={selectedTemplate}
                    onChange={e =>
                      handleTemplateChange(e.target.value as TemplateId)
                    }
                    className="template-dropdown"
                  >
                    {availableTemplatesForContentType.map(template => (
                      <option key={template.id} value={template.id}>
                        {template.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              {hasUnsavedChanges && (
                <div className="template-save-section">
                  <span className="unsaved-indicator">Unsaved changes</span>
                  <button
                    onClick={handleSaveChanges}
                    className="save-template-button"
                    disabled={isSavingChanges}
                  >
                    {isSavingChanges ? "Saving..." : "Save Changes"}
                  </button>
                </div>
              )}
              <SocialMediaPostWrapper
                key={`post-${idea.id}-${generatedPost.id}-${selectedTemplate}-${selectedPostFormat}`}
                post={generatedPost}
                onSaveDraft={
                  onSaveDraft ? () => onSaveDraft(generatedPost.id) : undefined
                }
                onPublish={
                  onPublish ? () => onPublish(generatedPost.id) : undefined
                }
                isPublishing={isApproving}
                businessProfile={selectedBusinessProfile as any}
                showActions={false}
                template={selectedTemplate}
              />
            </>
          )}
        </div>

        <div className="preview-actions">
          <SpaceButton
            onClick={() => onGeneratePost(selectedTemplate, selectedPostFormat)}
            disabled={isGeneratingPost}
          >
            {isGeneratingPost
              ? "Generating..."
              : generatedPost
                ? "Regenerate post"
                : "Generate post"}
          </SpaceButton>
          {generatedPost && (
            <SpaceButton
              variant="approve"
              onClick={onApprove}
              onMouseEnter={() => setIsHoveringScheduleButton(true)}
              onMouseLeave={() => setIsHoveringScheduleButton(false)}
              disabled={isApproving || idea.status === "published"}
            >
              {idea.status === "published"
                ? "Published"
                : idea.status === "scheduled"
                  ? isHoveringScheduleButton
                    ? "Unschedule"
                    : "Scheduled"
                  : "Approve"}
            </SpaceButton>
          )}
        </div>
      </div>
    </div>
  );
}
