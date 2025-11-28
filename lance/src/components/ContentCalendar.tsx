"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import {
  useContentCalendars,
  useGenerateContentCalendar,
  useApproveContentIdea,
  useUnscheduleContentIdea,
  useUpdateContentIdea,
  useDeleteContentCalendar,
} from "@/hooks/useContentCalendar";
import type { ContentIdea, ContentIdeaStatus } from "@/types/ContentCalendar";
import { transformBusinessProfileToRequest } from "./contentCalendar/helpers";
import {
  useContentCalendarState,
  usePostGeneration,
} from "./contentCalendar/hooks";
import { useBusinessProfile } from "@/contexts/BusinessProfileContext";
import LoadingState from "./contentCalendar/LoadingState";
import ErrorState from "./contentCalendar/ErrorState";
import EmptyState from "./contentCalendar/EmptyState";
import CalendarHeader from "./contentCalendar/CalendarHeader";
import ContentIdeasList from "./contentCalendar/ContentIdeasList";
import ContentPreviewPanel from "./contentCalendar/ContentPreviewPanel";
import AddIdeaModal from "./contentCalendar/AddIdeaModal";
import "./ContentCalendar.css";
import { useQueryClient } from "@tanstack/react-query";
import { contentCalendarKeys } from "@/hooks/useContentCalendar";
import type { ContentCalendar } from "@/types/ContentCalendar";

interface ContentCalendarProps {
  onContentIdeaClick?: (idea: ContentIdea) => void;
  onGeneratePost?: (idea: ContentIdea) => void;
}

export default function ContentCalendar({
  onContentIdeaClick,
  onGeneratePost,
}: ContentCalendarProps) {
  const {
    selectedBusinessProfile,
    onProfileChange,
    isLoading: profileLoading,
  } = useBusinessProfile();

  const {
    data: calendars,
    isLoading,
    error,
    refetch,
  } = useContentCalendars(selectedBusinessProfile?.id || "");
  const { mutate: generateCalendar, isPending: isGenerating } =
    useGenerateContentCalendar();
  const { mutate: updateIdea, isPending: isUpdating } = useUpdateContentIdea();
  const { mutate: deleteCalendar, isPending: isDeleting } =
    useDeleteContentCalendar();
  const queryClient = useQueryClient();

  const [showAddIdeaModal, setShowAddIdeaModal] = useState(false);

  const {
    selectedCalendar,
    selectedContentIdea,
    setSelectedContentIdea,
    generatedPost,
    setGeneratedPost,
    editingField,
    editValues,
    handleContentIdeaClick,
    handleStartEdit,
    handleCancelEdit,
    clearSelectedStates,
    setEditValues,
  } = useContentCalendarState(calendars);

  const { mutate: approveIdea, isPending: isApproving } = useApproveContentIdea(
    setSelectedContentIdea
  );
  const { mutate: unscheduleIdea, isPending: isUnscheduling } =
    useUnscheduleContentIdea(setSelectedContentIdea);

  const { isGeneratingPostForIdea, handleGeneratePost } = usePostGeneration(
    selectedContentIdea,
    setSelectedContentIdea,
    setGeneratedPost
  );

  useEffect(() => {
    const unsubscribe = onProfileChange(newProfile => {
      queryClient.invalidateQueries({
        queryKey: contentCalendarKeys.all,
      });
      clearSelectedStates();
    });

    return unsubscribe;
  }, [onProfileChange, queryClient, clearSelectedStates]);

  const handleGenerateCalendar = useCallback(() => {
    if (!selectedBusinessProfile) return;

    clearSelectedStates();

    generateCalendar({
      business_profile: transformBusinessProfileToRequest(
        selectedBusinessProfile
      ),
      business_profile_id: selectedBusinessProfile.id,
    });
  }, [clearSelectedStates, generateCalendar, selectedBusinessProfile]);

  const handleDeleteCalendar = useCallback(
    (calendarId: string) => {
      if (
        confirm(
          "Are you sure you want to delete this content calendar? This action cannot be undone."
        )
      ) {
        clearSelectedStates();

        deleteCalendar(calendarId, {
          onSuccess: () => {
            setTimeout(() => {
              refetch();
            }, 100);
          },
          onError: error => {
            console.error("Failed to delete calendar:", error);
          },
        });
      }
    },
    [clearSelectedStates, deleteCalendar, refetch]
  );

  const handleToggleScheduleIdea = useCallback(
    (ideaId: string) => {
      if (!selectedContentIdea || selectedContentIdea.id !== ideaId) return;

      const isCurrentlyScheduled = selectedContentIdea.status === "scheduled";
      const newStatus: ContentIdeaStatus = isCurrentlyScheduled
        ? "pending_approval"
        : "scheduled";

      const optimisticUpdate = {
        ...selectedContentIdea,
        status: newStatus,
        approved_at: isCurrentlyScheduled
          ? undefined
          : new Date().toISOString(),
      };

      setSelectedContentIdea(optimisticUpdate);

      if (selectedBusinessProfile) {
        queryClient.setQueryData(
          contentCalendarKeys.calendars(selectedBusinessProfile.id),
          (oldData: ContentCalendar[] | undefined) => {
            if (!oldData) return oldData;
            return oldData.map((calendar: ContentCalendar) => ({
              ...calendar,
              content_ideas: calendar.content_ideas?.map(idea =>
                idea.id === ideaId ? optimisticUpdate : idea
              ),
            }));
          }
        );
      }

      if (isCurrentlyScheduled) {
        unscheduleIdea(ideaId, {
          onError: () => {
            setSelectedContentIdea(selectedContentIdea);
            refetch();
          },
        });
      } else {
        approveIdea(ideaId, {
          onError: () => {
            setSelectedContentIdea(selectedContentIdea);
            refetch();
          },
        });
      }
    },
    [
      selectedContentIdea,
      setSelectedContentIdea,
      queryClient,
      selectedBusinessProfile,
      unscheduleIdea,
      approveIdea,
      refetch,
    ]
  );

  const handleContentIdeaClickWithCallback = useCallback(
    (idea: ContentIdea) => {
      handleContentIdeaClick(idea);
      if (onContentIdeaClick) {
        onContentIdeaClick(idea);
      }
    },
    [handleContentIdeaClick, onContentIdeaClick]
  );

  const handleSaveEdit = useCallback(() => {
    if (!selectedContentIdea || !editingField) return;

    const updates: { title?: string; description?: string } = {};
    if (editingField === "title") {
      updates.title = editValues.title;
    } else if (editingField === "description") {
      updates.description = editValues.description;
    }

    updateIdea(
      {
        ideaId: selectedContentIdea.id,
        updates,
      },
      {
        onSuccess: updatedIdea => {
          if (updatedIdea && selectedContentIdea) {
            setSelectedContentIdea({
              ...selectedContentIdea,
              ...updatedIdea,
            });
          }
          handleCancelEdit();
        },
      }
    );
  }, [
    selectedContentIdea,
    editingField,
    editValues,
    updateIdea,
    setSelectedContentIdea,
    handleCancelEdit,
  ]);

  const handleUpdateEditValue = useCallback(
    (field: "title" | "description", value: string) => {
      setEditValues(prev => ({
        ...prev,
        [field]: value,
      }));
    },
    [setEditValues]
  );

  const handleGeneratePostForIdea = useCallback(
    (selectedTemplate?: string, postFormat?: "single" | "carousel") => {
      if (selectedContentIdea) {
        const ideaToGenerate = selectedContentIdea;
        handleGeneratePost(
          ideaToGenerate,
          onGeneratePost,
          selectedTemplate,
          postFormat
        );
      }
    },
    [selectedContentIdea, handleGeneratePost, onGeneratePost]
  );

  const currentCalendar = useMemo(
    () => selectedCalendar || calendars?.[0],
    [selectedCalendar, calendars]
  );
  const contentIdeas = useMemo(
    () => currentCalendar?.content_ideas || [],
    [currentCalendar?.content_ideas]
  );
  const selectedIdeaId = useMemo(
    () => selectedContentIdea?.id || null,
    [selectedContentIdea?.id]
  );
  const isGeneratingCurrentPost = useMemo(
    () => isGeneratingPostForIdea === selectedContentIdea?.id,
    [isGeneratingPostForIdea, selectedContentIdea?.id]
  );
  const isApprovingOrUnscheduling = useMemo(
    () => isApproving || isUnscheduling,
    [isApproving, isUnscheduling]
  );

  const handleDeleteCurrentCalendar = useCallback(() => {
    if (currentCalendar) {
      handleDeleteCalendar(currentCalendar.id);
    }
  }, [handleDeleteCalendar, currentCalendar]);

  const handleToggleAddIdeaModal = useCallback(
    () => setShowAddIdeaModal(true),
    []
  );
  const handleCloseAddIdeaModal = useCallback(
    () => setShowAddIdeaModal(false),
    []
  );

  const handleApproveCurrentIdea = useCallback(() => {
    if (selectedContentIdea) {
      handleToggleScheduleIdea(selectedContentIdea.id);
    }
  }, [handleToggleScheduleIdea, selectedContentIdea]);

  const handleAddIdeaSubmit = useCallback((data: unknown) => {
    // TODO: Implement add idea functionality
  }, []);

  // Show loading state if business profile is not yet loaded
  if (profileLoading || !selectedBusinessProfile) {
    return (
      <div className="content-calendar-container">
        <div className="content-calendar-header">
          <h1>Content Calendar</h1>
        </div>
        <div className="loading-state">
          <p>Loading business profile...</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState error={error} />;
  }

  if (!calendars || calendars.length === 0) {
    return (
      <EmptyState
        onGenerate={handleGenerateCalendar}
        isGenerating={isGenerating}
      />
    );
  }

  if (!currentCalendar) {
    return <LoadingState />;
  }

  return (
    <div className="content-calendar-container">
      <CalendarHeader
        onRefresh={handleGenerateCalendar}
        onDelete={handleDeleteCurrentCalendar}
        isGenerating={isGenerating}
        isDeleting={isDeleting}
      />

      <div className="content-calendar-layout">
        <ContentIdeasList
          ideas={contentIdeas}
          selectedIdeaId={selectedIdeaId}
          onIdeaClick={handleContentIdeaClickWithCallback}
          onAddIdea={handleToggleAddIdeaModal}
        />

        {selectedContentIdea ? (
          <ContentPreviewPanel
            idea={selectedContentIdea}
            generatedPost={generatedPost}
            editingField={editingField}
            editValues={editValues}
            isUpdating={isUpdating}
            isGeneratingPost={isGeneratingCurrentPost}
            isApproving={isApprovingOrUnscheduling}
            onStartEdit={handleStartEdit}
            onCancelEdit={handleCancelEdit}
            onSaveEdit={handleSaveEdit}
            onUpdateEditValue={handleUpdateEditValue}
            onGeneratePost={handleGeneratePostForIdea}
            onApprove={handleApproveCurrentIdea}
            onIdeaUpdate={setSelectedContentIdea}
            showTemplateDropdown={true}
          />
        ) : (
          <div className="content-preview-panel">
            <div className="preview-empty">
              <p>Select a content idea to preview</p>
            </div>
          </div>
        )}
      </div>

      <AddIdeaModal
        isOpen={showAddIdeaModal}
        onClose={handleCloseAddIdeaModal}
        onSubmit={handleAddIdeaSubmit}
      />
    </div>
  );
}
