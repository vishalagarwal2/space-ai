"use client";

import Image from "next/image";
import { useState, useRef } from "react";
import {
  useConnectedAccounts,
  useInstagramConnection,
  useDisconnectAccount,
  useIsInstagramConnected,
} from "@/hooks/useConnectedAccounts";
import {
  useInstagramPosts,
  useCreateInstagramPost,
  usePostToInstagram,
} from "@/hooks/useInstagramPosts";
import {
  InstagramIcon,
  LinkedInIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  CheckIcon,
  GenericIcon,
  ErrorIcon,
} from "./icons";
import { TabTitle } from "./base/TabTitle";
import "./ConnectedAccounts.css";

interface ConnectedAccountsProps {
  onBack: () => void;
}

export default function ConnectedAccounts({ onBack }: ConnectedAccountsProps) {
  const {
    data: accounts = [],
    isLoading,
    error: accountsError,
    refetch: refetchAccounts,
  } = useConnectedAccounts();

  const { mutate: connectInstagram, isPending: isConnecting } =
    useInstagramConnection();

  const { mutate: disconnectAccount, isPending: isDisconnecting } =
    useDisconnectAccount();

  const isInstagramConnected = useIsInstagramConnected();

  const { data: instagramPosts = [], isLoading: postsLoading } =
    useInstagramPosts();
  const { mutate: createPost, isPending: isCreatingPost } =
    useCreateInstagramPost();
  const { mutate: postToInstagram } = usePostToInstagram();

  const [showPostForm, setShowPostForm] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [caption, setCaption] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [postingId, setPostingId] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleConnectInstagram = () => {
    connectInstagram();
  };

  const handleDisconnectAccount = (accountId: string, platform: string) => {
    disconnectAccount({ accountId, platform });
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const handleCreatePost = () => {
    if (!selectedFile) return;

    createPost(
      { media: selectedFile, caption },
      {
        onSuccess: () => {
          setSelectedFile(null);
          setCaption("");
          setPreviewUrl(null);
          setShowPostForm(false);
          if (fileInputRef.current) {
            fileInputRef.current.value = "";
          }
        },
      }
    );
  };

  const handlePostToInstagram = (postId: number) => {
    setPostingId(postId);
    postToInstagram(postId, {
      onSuccess: () => {
        setPostingId(null);
      },
      onError: () => {
        setPostingId(null);
      },
    });
  };

  const resetPostForm = () => {
    setSelectedFile(null);
    setCaption("");
    setPreviewUrl(null);
    setShowPostForm(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case "instagram":
        return <InstagramIcon size={24} />;
      case "linkedin":
        return <LinkedInIcon size={24} />;
      default:
        return <GenericIcon size={24} />;
    }
  };

  if (isLoading) {
    return (
      <div className="connected-accounts">
        <div className="connected-accounts-header">
          <button className="back-button" onClick={onBack}>
            <ArrowLeftIcon size={20} />
          </button>
          <h2>Connected Accounts</h2>
        </div>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading connected accounts...</p>
        </div>
      </div>
    );
  }

  if (accountsError) {
    const axiosError = accountsError as {
      response?: { data?: { error?: string } };
      message?: string;
    };
    const errorMessage =
      axiosError?.response?.data?.error ||
      axiosError?.message ||
      "Unknown error";

    console.error("ConnectedAccounts error:", accountsError);
    console.error("Error message:", errorMessage);

    return (
      <div className="connected-accounts">
        <div className="connected-accounts-header">
          <button className="back-button" onClick={onBack}>
            <ArrowLeftIcon size={20} />
          </button>
          <h2>Connected Accounts</h2>
        </div>
        <div className="error-container">
          <div className="error-icon">
            <ErrorIcon size={48} />
          </div>
          <h4>Failed to load accounts</h4>
          <p>There was an error loading your connected accounts.</p>
          {process.env.NODE_ENV === "development" && (
            <p style={{ fontSize: "12px", color: "#666", marginTop: "8px" }}>
              Error: {errorMessage}
            </p>
          )}
          <button className="retry-button" onClick={() => refetchAccounts()}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="connected-accounts">
      <div className="connected-accounts-header">
        <TabTitle>Your Connected Accounts</TabTitle>
      </div>

      <div className="accounts-content">
        <div className="form-section">
          <h2 className="section-title">Connect New Account</h2>
          <div className="platform-options">
            <button
              className={`platform-button instagram ${isInstagramConnected ? "connected" : ""}`}
              onClick={
                isInstagramConnected ? undefined : handleConnectInstagram
              }
              disabled={isConnecting || isInstagramConnected}
            >
              <div className="platform-icon">
                {getPlatformIcon("instagram")}
              </div>
              <div className="platform-info">
                <h4>Instagram</h4>
                <p>
                  {isInstagramConnected
                    ? "Instagram account already connected"
                    : "Connect your Instagram Business account"}
                </p>
              </div>
              {isConnecting ? (
                <div className="loading-spinner small"></div>
              ) : isInstagramConnected ? (
                <CheckIcon size={20} />
              ) : (
                <ArrowRightIcon size={20} />
              )}
            </button>

            <button className="platform-button linkedin disabled">
              <div className="platform-icon">{getPlatformIcon("linkedin")}</div>
              <div className="platform-info">
                <h4>LinkedIn</h4>
                <p>Coming soon</p>
              </div>
              <ArrowRightIcon size={20} />
            </button>
          </div>
        </div>

        <div className="form-section">
          <h2 className="section-title">Connected Accounts</h2>
          {accounts.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">
                <GenericIcon size={48} />
              </div>
              <h4>No connected accounts</h4>
              <p>Connect your social media accounts to start posting content</p>
            </div>
          ) : (
            <div className="accounts-list">
              {accounts.map(account => {
                return (
                  <div key={account.id} className="account-card">
                    <div className="account-info">
                      <div className="account-avatar">
                        {account.profile_picture_url ? (
                          <Image
                            src={account.profile_picture_url}
                            alt={account.username}
                            width={40}
                            height={40}
                            className="rounded-full"
                            onError={e => {
                              console.error(
                                "Error loading profile picture:",
                                e
                              );
                            }}
                          />
                        ) : (
                          <div className="default-avatar">
                            {getPlatformIcon(account.platform)}
                          </div>
                        )}
                      </div>
                      <div className="account-details">
                        <h4>{account.display_name || account.username}</h4>
                        <p>@{account.username}</p>
                        <div className="account-status">
                          <span
                            className={`status-badge ${account.is_verified ? "verified" : "unverified"}`}
                          >
                            {account.is_verified ? "Verified" : "Unverified"}
                          </span>
                          <span className="platform-badge">
                            {account.platform.charAt(0).toUpperCase() +
                              account.platform.slice(1)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="account-actions">
                      <button
                        className="disconnect-button"
                        onClick={() =>
                          handleDisconnectAccount(account.id, account.platform)
                        }
                        disabled={isDisconnecting}
                      >
                        {isDisconnecting ? (
                          <>
                            <div className="loading-spinner small"></div>
                            Disconnecting...
                          </>
                        ) : (
                          "Disconnect"
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {isInstagramConnected && (
          <div className="form-section">
            <div className="section-header">
              <h2 className="section-title">Instagram Posts</h2>
              <button
                className="create-post-button"
                onClick={() => setShowPostForm(true)}
              >
                Create Post
              </button>
            </div>

            {showPostForm && (
              <div className="post-creation-form">
                <div className="form-header">
                  <h4>Create New Post</h4>
                  <button className="close-button" onClick={resetPostForm}>
                    ×
                  </button>
                </div>

                <div className="form-content">
                  <div className="file-upload-area">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*,video/*"
                      onChange={handleFileSelect}
                      className="file-input"
                      id="media-upload"
                    />
                    <label htmlFor="media-upload" className="file-upload-label">
                      {previewUrl ? (
                        <div className="media-preview">
                          {selectedFile?.type.startsWith("video/") ? (
                            <video
                              src={previewUrl}
                              controls
                              className="preview-media"
                            />
                          ) : (
                            <Image
                              src={previewUrl}
                              alt="Preview"
                              className="preview-media"
                              width={300}
                              height={300}
                            />
                          )}
                        </div>
                      ) : (
                        <div className="upload-placeholder">
                          <div className="upload-icon">📷</div>
                          <p>Click to upload image or video</p>
                          <span className="upload-hint">
                            Supports JPG, PNG, MP4, MOV
                          </span>
                        </div>
                      )}
                    </label>
                  </div>

                  <div className="caption-section">
                    <label htmlFor="caption" className="caption-label">
                      Caption (optional)
                    </label>
                    <textarea
                      id="caption"
                      value={caption}
                      onChange={e => setCaption(e.target.value)}
                      placeholder="Write a caption for your post..."
                      className="caption-input"
                      rows={3}
                    />
                  </div>

                  <div className="form-actions">
                    <button className="cancel-button" onClick={resetPostForm}>
                      Cancel
                    </button>
                    <button
                      className="create-button"
                      onClick={handleCreatePost}
                      disabled={!selectedFile || isCreatingPost}
                    >
                      {isCreatingPost ? (
                        <>
                          <div className="loading-spinner small"></div>
                          Creating...
                        </>
                      ) : (
                        "Create Post"
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="posts-list">
              {postsLoading ? (
                <div className="loading-container">
                  <div className="loading-spinner"></div>
                  <p>Loading posts...</p>
                </div>
              ) : instagramPosts.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">📝</div>
                  <h4>No posts yet</h4>
                  <p>Create your first Instagram post to get started</p>
                </div>
              ) : (
                instagramPosts.map(post => (
                  <div key={post.id} className="post-card">
                    <div className="post-media">
                      {post.media_type === "video" ? (
                        <video
                          src={post.media_url}
                          controls
                          className="post-media-content"
                        />
                      ) : (
                        <Image
                          src={post.media_url}
                          alt="Post media"
                          className="post-media-content"
                          width={120}
                          height={120}
                        />
                      )}
                    </div>
                    <div className="post-details">
                      <div className="post-caption">
                        {post.caption || <em>No caption</em>}
                      </div>
                      <div className="post-meta">
                        <span className={`status-badge ${post.status}`}>
                          {post.status.charAt(0).toUpperCase() +
                            post.status.slice(1)}
                        </span>
                        <span className="post-date">
                          {new Date(post.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <div className="post-actions">
                      {post.status === "draft" && (
                        <button
                          className="post-button"
                          onClick={() => handlePostToInstagram(post.id)}
                          disabled={postingId === post.id}
                        >
                          {postingId === post.id ? (
                            <>
                              <div className="loading-spinner small"></div>
                              Posting...
                            </>
                          ) : (
                            "Post to Instagram"
                          )}
                        </button>
                      )}
                      {post.status === "posted" && (
                        <div className="posted-indicator">
                          <CheckIcon size={16} />
                          Posted
                        </div>
                      )}
                      {post.status === "failed" && (
                        <div className="failed-indicator">
                          <ErrorIcon size={16} />
                          Failed
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
