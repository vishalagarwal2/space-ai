"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Form } from "@/components/ui/form";
import { toast } from "sonner";
import { SpaceFormField } from "@/components/forms/SpaceFormField";
import { SpaceColorField } from "@/components/forms/SpaceColorField";
import { SpaceTextareaField } from "@/components/forms/SpaceTextareaField";
import { SpaceButton } from "@/components/base/SpaceButton";
import { TabTitle } from "@/components/base/TabTitle";
import { FileIcon } from "@/components/icons";
import { API_URL } from "@/lib/axios";
import "@/components/forms/SpaceFormField.css";
import "./business-onboarding.css";

const businessOnboardingSchema = z.object({
  business_name: z.string().optional(),
  website_url: z.string().optional(),
  instagram_handle: z.string().optional(),
  logo: z.instanceof(File).optional(),
  primary_color: z.string().optional(),
  secondary_color: z.string().optional(),
  accent_color: z.string().optional(),
  font_family: z.string().optional(),
  brand_mission: z.string().optional(),
  brand_values: z.string().optional(),
  business_basic_details: z.string().optional(),
  business_services: z.string().optional(),
  business_additional_details: z.string().optional(),
});

function BusinessOnboarding() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string>("");
  const [isDragOver, setIsDragOver] = useState(false);

  const form = useForm({
    resolver: zodResolver(businessOnboardingSchema),
    defaultValues: {
      business_name: "",
      website_url: "",
      instagram_handle: "",
      primary_color: "#3B82F6",
      secondary_color: "#10B981",
      accent_color: "#F59E0B",
      font_family: "",
      brand_mission: "",
      brand_values: "",
      business_basic_details: "",
      business_services: "",
      business_additional_details: "",
    },
  });

  const handleLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const processFile = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("Please select a valid image file (PNG, JPG, JPEG, GIF, WebP).");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError("File size must be less than 5MB.");
      return;
    }

    setLogoFile(file);
    const reader = new FileReader();
    reader.onload = event => {
      setLogoPreview(event.target?.result as string);
    };
    reader.readAsDataURL(file);
    setError("");
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
    // Simple error handling
  };

  const onSubmit = async (values: z.infer<typeof businessOnboardingSchema>) => {
    setError("");
    setLoading(true);

    try {
      // Create FormData for file upload
      const formData = new FormData();

      // Add all form fields
      Object.entries(values).forEach(([key, value]) => {
        if (value && key !== "logo") {
          formData.append(key, value as string);
        }
      });

      // Add logo file if present
      if (logoFile) {
        formData.append("logo", logoFile);
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || API_URL}/api/business/profile/update/`,
        {
          method: "POST",
          credentials: "include",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || data.message || "Failed to save profile");
      }

      toast.success("Business profile created successfully!");
      router.push("/dashboard");
    } catch (err: unknown) {
      const message =
        (err instanceof Error
          ? err.message
          : typeof err === "object" && err !== null && "message" in err
            ? String(err.message)
            : "Failed to save profile. Please try again.") ||
        "Failed to save profile. Please try again.";
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="business-onboarding-container">
      <div className="business-profile">
        <div className="business-profile-header">
          <TabTitle>Complete your business profile</TabTitle>
          <p className="business-profile-subtitle">
            Let us build a high-fidelity persona for your business, so we can
            start creating content for you.
          </p>
        </div>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="profile-form">
            {error && <div className={`submit-message error`}>{error}</div>}

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
              />
            </div>

            <div className="form-section">
              <h2 className="section-title">Brand Identity</h2>

              <div className="form-group">
                <label htmlFor="logo-upload" className="space-form-label">
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

            <div className="form-actions">
              <SpaceButton type="submit" disabled={loading}>
                {loading ? "Saving..." : "Finish"}
              </SpaceButton>
            </div>
          </form>
        </Form>
      </div>
    </div>
  );
}

export default BusinessOnboarding;
