"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { useChatConversation } from "@/hooks/useChatConversation";
import { useChatInput } from "@/hooks/useChatInput";
import { useChatMessages, type Message } from "@/hooks/useChatMessages";
import { useRenderingHandlers } from "@/hooks/useRenderingHandlers";
import { usePublishPost } from "@/hooks/usePublishPost";
import ChatBubble from "./ChatBubble";
import SocialMediaPostWrapper from "./SocialMediaPostWrapper";
import PostRenderer from "./PostRenderer";
import {
  HeartIcon,
  CommentIcon,
  ShareIcon,
  BookmarkIcon,
  ArrowUpIcon,
} from "./icons";
import { useBusinessProfile } from "@/contexts/BusinessProfileContext";
import {
  DEFAULT_TEMPLATE,
  getTemplatesForBusiness,
  type TemplateId,
  TemplateType as ConfigTemplateType,
} from "@/config/templates";
import type { BusinessProfile } from "@/constants/mockBusinessProfiles";
import { DEFAULT_BUSINESS_PROFILE } from "@/constants/mockBusinessProfiles";
import type { UnifiedBusinessProfile } from "@/hooks/useBusinessProfile";
import "./SocialMediaChat.css";

// Helper function to convert UnifiedBusinessProfile to BusinessProfile
function convertToBusinessProfile(
  profile: UnifiedBusinessProfile | null
): BusinessProfile | null {
  if (!profile) return null;
  return {
    ...profile,
    designComponents:
      profile.designComponents || DEFAULT_BUSINESS_PROFILE.designComponents,
  };
}

interface SocialMediaChatProps {
  onBack: () => void;
}

export default function SocialMediaChat({}: SocialMediaChatProps) {
  const { conversationId, setConversationId, isInitializing } =
    useChatConversation();
  const { selectedBusinessProfile, onProfileChange } = useBusinessProfile();
  const [selectedTemplate, setSelectedTemplate] =
    useState<TemplateId>(DEFAULT_TEMPLATE);
  const {
    messages,
    setMessages,
    isLoading,
    isGeneratingPost,
    messagesEndRef,
    sendMessage,
  } = useChatMessages(
    conversationId,
    setConversationId,
    null,
    isInitializing,
    convertToBusinessProfile(selectedBusinessProfile) || undefined
  );
  const { inputValue, textareaRef, handleInputChange, resetInput } =
    useChatInput();
  const { handleRenderingComplete, handleRenderingError } =
    useRenderingHandlers(setMessages);
  const { mutate: publishPost, isPending: isPublishing } = usePublishPost();

  useEffect(() => {
    const unsubscribe = onProfileChange(newProfile => {
      setConversationId(null);
      setMessages([]);
    });

    return unsubscribe;
  }, [onProfileChange, setConversationId, setMessages]);

  const handlePublishPost = (message: Message) => {
    if (!message.postPreview?.id) {
      return;
    }

    publishPost(
      {
        postId: message.postPreview.id,
        renderedImageUrl: message.renderedImageUrl,
        postPreview: message.postPreview,
      },
      {
        onSuccess: () => {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === message.id ? { ...msg, isPublished: true } : msg
            )
          );
        },
      }
    );
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading || isInitializing || isGeneratingPost)
      return;

    const currentInput = inputValue;
    resetInput();
    await sendMessage(currentInput);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="social-media-chat">
      <div className="chat-messages">
        <div className="chat-header">
          <h3 className="chat-title">Instagram Post Creator</h3>
          <div className="template-selectors">
            <div className="selector-group">
              <label htmlFor="template-select" className="selector-label">
                Template:
              </label>
              <select
                id="template-select"
                value={selectedTemplate}
                onChange={e =>
                  setSelectedTemplate(e.target.value as TemplateId)
                }
                className="selector-dropdown"
              >
                {getTemplatesForBusiness(selectedBusinessProfile?.id).map(
                  template => (
                    <option key={template.id} value={template.id}>
                      {template.name}
                    </option>
                  )
                )}
              </select>
            </div>
          </div>
        </div>
        {messages.map(message => {
          return (
            <div key={message.id} className="message-wrapper">
              <ChatBubble role={message.role} content={message.content} />
              {message.layoutJson && selectedBusinessProfile && (
                <div style={{ width: "min-content" }}>
                  <div
                    style={{ width: "max-content" }}
                    className="instagram-post-preview-container mb-4"
                  >
                    <div className="instagram-post-mockup bg-white rounded-xl shadow-lg border max-w-md">
                      <div className="instagram-header flex items-center p-3 border-b">
                        <div className="relative w-8 h-8 flex-shrink-0">
                          {selectedBusinessProfile.logoUrl && (
                            <Image
                              src={selectedBusinessProfile.logoUrl}
                              alt={selectedBusinessProfile.name}
                              width={32}
                              height={32}
                              className="w-8 h-8 rounded-full object-cover"
                            />
                          )}
                        </div>
                        <div className="ml-3">
                          <p className="font-semibold text-sm text-gray-900">
                            {selectedBusinessProfile.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {selectedBusinessProfile.brandGuidelines.industry}
                          </p>
                        </div>
                      </div>
                      <div className="instagram-image-container">
                        <PostRenderer
                          layout={message.layoutJson}
                          onComplete={handleRenderingComplete(message.id)}
                          onError={(error: string) => handleRenderingError(message.id)(error, "")}
                          businessProfile={convertToBusinessProfile(selectedBusinessProfile)!}
                          selectedTemplate={
                            selectedTemplate as ConfigTemplateType
                          }
                        />
                      </div>
                      <div className="instagram-actions p-3">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-4">
                            <HeartIcon
                              size={24}
                              color="currentColor"
                              className="w-6 h-6 text-gray-700"
                            />
                            <CommentIcon
                              size={24}
                              color="currentColor"
                              className="w-6 h-6 text-gray-700"
                            />
                            <ShareIcon
                              size={24}
                              color="currentColor"
                              className="w-6 h-6 text-gray-700"
                            />
                          </div>
                          <BookmarkIcon
                            size={24}
                            color="currentColor"
                            className="w-6 h-6 text-gray-700"
                          />
                        </div>
                        <div className="text-sm">
                          <span className="font-semibold text-gray-900">
                            {selectedBusinessProfile?.name}
                          </span>
                          <span className="text-gray-900 ml-1">
                            {message.postPreview?.caption ||
                              message.layoutJson.textBlocks?.[0]?.text ||
                              "Check out our latest post!"}
                          </span>
                        </div>
                        <div className="text-sm text-blue-900 mt-2">
                          {message.postPreview?.hashtags ||
                            `#${selectedBusinessProfile?.brandGuidelines.industry.toLowerCase().replace(" ", "")} #business #instagram`}
                        </div>
                      </div>
                    </div>
                    <div />
                    <div className="post-actions-buttons flex gap-3 mt-4 justify-end">
                      <button
                        onClick={() => {
                          // TODO: Implement save draft functionality
                        }}
                        className="save-draft-btn px-6 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
                        style={{ width: "max-content" }}
                      >
                        Save as draft
                      </button>
                      <button
                        onClick={() => handlePublishPost(message)}
                        disabled={
                          isPublishing ||
                          !message.postPreview?.id ||
                          message.isPublished
                        }
                        className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                          message.isPublished
                            ? "bg-green-500 text-white cursor-not-allowed"
                            : "bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed"
                        }`}
                        style={{ width: "max-content" }}
                      >
                        {message.isPublished
                          ? "✓ Posted to Instagram"
                          : isPublishing
                            ? "Publishing..."
                            : "Post to Instagram"}
                      </button>
                    </div>
                  </div>
                </div>
              )}
              {message.postPreview && !message.layoutJson && (
                <SocialMediaPostWrapper
                  post={message.postPreview}
                  onRefine={() => {
                    // TODO: Implement refine functionality
                  }}
                  onPublish={() => {
                    // TODO: Implement publish functionality
                  }}
                  onSaveDraft={() => {
                    // TODO: Implement save draft functionality
                  }}
                  isRefining={false}
                  isPublishing={false}
                />
              )}
            </div>
          );
        })}
        {(isLoading || isInitializing || isGeneratingPost) && (
          <ChatBubble
            role="assistant"
            content={
              isGeneratingPost ? "Creating your social media post..." : ""
            }
            isTyping={true}
          />
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input">
        <div className="input-container">
          <textarea
            value={inputValue}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder={
              isInitializing
                ? "Initializing chat..."
                : "Share details about the kind of Instagram post you'd like to create..."
            }
            className="message-input"
            disabled={isLoading || isInitializing || isGeneratingPost}
            ref={textareaRef}
            rows={1}
          />
          <button
            onClick={handleSendMessage}
            disabled={
              !inputValue.trim() ||
              isLoading ||
              isInitializing ||
              isGeneratingPost
            }
            className="send-button"
          >
            <ArrowUpIcon fill="white" />
          </button>
        </div>
      </div>
    </div>
  );
}
