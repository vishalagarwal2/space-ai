"use client";

import { useState, useEffect } from "react";
import "./BusinessProfile.css";
import {
  useBusinessProfile,
  useUpdateBusinessProfile,
  businessProfileKeys,
  type UnifiedBusinessProfile,
} from "@/hooks/useBusinessProfile";
import { FileIcon } from "./icons";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Form } from "@/components/ui/form";
import { SpaceFormField } from "@/components/forms/SpaceFormField";
import { SpaceColorField } from "@/components/forms/SpaceColorField";
import { SpaceTextareaField } from "@/components/forms/SpaceTextareaField";
import { SpaceButton } from "@/components/base/SpaceButton";
import { TabTitle } from "@/components/base/TabTitle";
import "@/components/forms/SpaceFormField.css";
import { useQueryClient } from "@tanstack/react-query";

interface BusinessProfileProps {
  user: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
  };
}

interface BusinessBrand {
  business_name: string;
  logo_url: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_family: string;
  website_url: string;
  instagram_handle: string;
  brand_mission: string;
  brand_values: string;
  business_basic_details: string;
  business_services: string;
  business_additional_details: string;
}

const businessProfileSchema = z.object({
  business_name: z.string().min(1, "Business name is required"),
  website_url: z.string().optional(),
  instagram_handle: z.string().optional(),
  business_basic_details: z
    .string()
    .min(1, "Business basic details are required"),
  primary_color: z.string().optional(),
  secondary_color: z.string().optional(),
  accent_color: z.string().optional(),
  font_family: z.string().optional(),
  brand_mission: z.string().optional(),
  brand_values: z.string().optional(),
  business_services: z.string().optional(),
  business_additional_details: z.string().optional(),
});

export default function BusinessProfile({}: BusinessProfileProps) {
  const { selectedBusinessProfile: profile, isLoading } = useBusinessProfile();
  const { mutate: updateProfile, isPending: isSubmitting } =
    useUpdateBusinessProfile();

  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string>("");
  const [isDragOver, setIsDragOver] = useState(false);
  const [submitMessage, setSubmitMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const form = useForm({
    resolver: zodResolver(businessProfileSchema),
    defaultValues: {
      business_name: "",
      website_url: "",
      instagram_handle: "",
      business_basic_details: "",
      primary_color: "#3b82f6",
      secondary_color: "#10b981",
      accent_color: "#f59e0b",
      font_family: "Roboto",
      brand_mission: "",
      brand_values: "",
      business_services: "",
      business_additional_details: "",
    },
  });

  const [lastProfileId, setLastProfileId] = useState<string | null>(null);

  useEffect(() => {
    if (profile && profile.id !== lastProfileId) {
      setTimeout(() => {
        form.reset({
          business_name: profile.companyName || "",
          primary_color: profile.colorPalette?.primary || "#3b82f6",
          secondary_color: profile.colorPalette?.secondary || "#10b981",
          accent_color: profile.colorPalette?.accent || "#f59e0b",
          font_family: profile.brandGuidelines?.fontFamily || "Roboto",
          website_url: profile.website_url || "",
          instagram_handle: profile.instagram_handle || "",
          brand_mission: profile.brand_mission || "",
          brand_values: profile.brand_values || "",
          business_basic_details: profile.business_basic_details || "",
          business_services: profile.business_services || "",
          business_additional_details:
            profile.business_additional_details || "",
        });

        if (profile.logoUrl) {
          setLogoPreview(profile.logoUrl);
        }

        setLastProfileId(profile.id);
      }, 0);
    }
  }, [profile, form, lastProfileId]);

  const onSubmit = async (values: z.infer<typeof businessProfileSchema>) => {
    setSubmitMessage(null);

    try {
      const profileData = {
        business_name: values.business_name || "",
        website_url: values.website_url || "",
        instagram_handle: values.instagram_handle || "",
        primary_color: values.primary_color || "#3b82f6",
        secondary_color: values.secondary_color || "#10b981",
        accent_color: values.accent_color || "#f59e0b",
        font_family: values.font_family || "Roboto",
        brand_mission: values.brand_mission || "",
        brand_values: values.brand_values || "",
        business_basic_details: values.business_basic_details || "",
        business_services: values.business_services || "",
        business_additional_details: values.business_additional_details || "",
        logo: logoFile || undefined,
      };

      updateProfile(profileData, {
        onSuccess: data => {
          setSubmitMessage({
            type: "success",
            text: "Business profile updated successfully!",
          });

          if (data?.data?.logo) {
            setLogoPreview(data.data.logo);
          }
        },
        onError: (error: unknown) => {
          console.error("Error updating business profile:", error);
          const apiError = error as {
            response?: { data?: { error?: string } };
            message?: string;
          };
          setSubmitMessage({
            type: "error",
            text:
              apiError.response?.data?.error ||
              apiError.message ||
              "Failed to update business profile. Please try again.",
          });
        },
      });
    } catch (error: unknown) {
      console.error("Error updating business profile:", error);
      const apiError = error as {
        response?: { data?: { error?: string } };
        message?: string;
      };
      setSubmitMessage({
        type: "error",
        text:
          apiError.response?.data?.error ||
          apiError.message ||
          "Failed to update business profile. Please try again.",
      });
    }
  };

  const handleLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const processFile = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setSubmitMessage({
        type: "error",
        text: "Please select a valid image file (PNG, JPG, JPEG, GIF, WebP).",
      });
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setSubmitMessage({
        type: "error",
        text: "File size must be less than 5MB.",
      });
      return;
    }

    setLogoFile(file);
    const reader = new FileReader();
    reader.onload = event => {
      setLogoPreview(event.target?.result as string);
    };
    reader.readAsDataURL(file);
    setSubmitMessage(null);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      processFile(files[0]);
    }
  };

  const handleImageError = () => {
    // Simple error handling - URLs are always fresh so this indicates a real issue
  };

  if (isLoading) {
    return (
      <div className="business-profile">
        <div className="business-profile-loading">
          <div className="business-profile-loading-content">
            <div className="business-profile-spinner"></div>
            <h3 className="business-profile-loading-title">
              Loading Business Profile
            </h3>
            <p className="business-profile-loading-text">
              Fetching your brand information...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="business-profile">
      <div className="business-profile-header">
        <TabTitle>Business Profile</TabTitle>
        <p className="business-profile-subtitle">
          Set up your brand identity to create consistent social media content
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="profile-form">
          <div className="form-section">
            <h2 className="section-title">Basic Information</h2>

            <SpaceFormField
              control={form.control}
              name="business_name"
              label="Business Name"
              placeholder="Enter your business name"
            />

            <SpaceFormField
              control={form.control}
              name="website_url"
              label="Website URL"
              type="url"
              placeholder="https://www.yourwebsite.com"
            />

            <SpaceFormField
              control={form.control}
              name="instagram_handle"
              label="Instagram Handle"
              placeholder="@yourbusiness"
            />

            <SpaceTextareaField
              control={form.control}
              name="business_basic_details"
              label="Business Basic Details"
              placeholder="Describe what your business does..."
              rows={4}
              required
            />
          </div>

          <div className="form-section">
            <h2 className="section-title">Brand Identity</h2>

            <div className="form-group">
              <label htmlFor="logo" className="space-form-label">
                Company Logo
              </label>
              <div className="logo-upload">
                <input
                  type="file"
                  id="logo-upload"
                  name="logo"
                  accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
                  onChange={handleLogoUpload}
                  className="logo-input"
                />
                <div
                  className={`logo-upload-area ${isDragOver ? "drag-over" : ""}`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() =>
                    document.getElementById("logo-upload")?.click()
                  }
                >
                  {logoPreview ? (
                    <div className="logo-preview-container">
                      {/* Use regular img tag for S3 signed URLs, Next.js Image for others */}
                      <img
                        src={logoPreview}
                        alt="Logo preview"
                        className="logo-preview"
                        style={{
                          width: "200px",
                          height: "120px",
                          objectFit: "contain",
                        }}
                        onError={handleImageError}
                      />
                      <div className="logo-overlay">
                        <span className="logo-change-text">
                          Click or drag to change
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="logo-placeholder">
                      <FileIcon size={48} />
                      <span className="logo-upload-text">
                        {isDragOver
                          ? "Drop your logo here"
                          : "Click or drag to upload logo"}
                      </span>
                      <span className="logo-upload-hint">
                        PNG, JPG, JPEG, GIF, WebP (max 5MB)
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="color-group">
              <SpaceColorField
                control={form.control}
                name="primary_color"
                label="Primary Color"
                placeholder="#3B82F6"
              />

              <SpaceColorField
                control={form.control}
                name="secondary_color"
                label="Secondary Color"
                placeholder="#10B981"
              />

              <SpaceColorField
                control={form.control}
                name="accent_color"
                label="Accent Color"
                placeholder="#F59E0B"
              />
            </div>

            <SpaceFormField
              control={form.control}
              name="font_family"
              label="Font Family"
              placeholder="Enter Google Font name (e.g., Roboto, Open Sans, Montserrat)"
            />
          </div>

          <div className="form-section">
            <h2 className="section-title">Brand Details</h2>

            <SpaceTextareaField
              control={form.control}
              name="brand_mission"
              label="Brand Mission"
              placeholder="What is your brand's mission and purpose?"
              rows={3}
            />

            <SpaceTextareaField
              control={form.control}
              name="brand_values"
              label="Brand Values"
              placeholder="What values does your brand stand for?"
              rows={3}
            />

            <SpaceTextareaField
              control={form.control}
              name="business_services"
              label="Business Services"
              placeholder="What services or products do you offer?"
              rows={4}
            />

            <SpaceTextareaField
              control={form.control}
              name="business_additional_details"
              label="Additional Details"
              placeholder="Any additional information about your business..."
              rows={4}
            />
          </div>

          {submitMessage && (
            <div className={`submit-message ${submitMessage.type}`}>
              {submitMessage.text}
            </div>
          )}

          <div className="form-actions">
            <SpaceButton type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Save Business Profile"}
            </SpaceButton>
          </div>
        </form>
      </Form>
    </div>
  );
}
