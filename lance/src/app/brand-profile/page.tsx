"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import Image from "next/image";
import RightCard from "../../components/RightCard";
import LoadingState from "@/components/contentCalendar/LoadingState";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import Link from "next/link";
import "./brand-profile.css";

// Brand profile schema
const brandProfileSchema = z.object({
  company_name: z.string().min(1, "Company name is required"),
  primary_color: z.string().min(1, "Primary color is required"),
  secondary_color: z.string().min(1, "Secondary color is required"),
  font_family: z.string().min(1, "Font family is required"),
  brand_voice: z.string().min(1, "Brand voice is required"),
  industry: z.string().min(1, "Industry is required"),
  target_audience: z.string().min(1, "Target audience is required"),
  business_description: z.string().min(1, "Business description is required"),
});

function BrandProfile() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);

  const form = useForm({
    resolver: zodResolver(brandProfileSchema),
    defaultValues: {
      company_name: "",
      primary_color: "#FF5733",
      secondary_color: "#33A1FF",
      font_family: "Arial",
      brand_voice: "",
      industry: "",
      target_audience: "",
      business_description: "",
    },
  });

  const handleLogoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = e => {
        setLogoPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  if (authLoading) {
    return <LoadingState />;
  }

  const onSubmit = async (values: z.infer<typeof brandProfileSchema>) => {
    setError("");
    setLoading(true);

    try {
      toast.success("Brand profile saved successfully");
      router.push("/dashboard");
    } catch (err: unknown) {
      const message =
        (err as any)?.response?.data?.error ||
        (err as any)?.response?.data?.message ||
        (err as any)?.message ||
        "Failed to save brand profile";

      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="brand-profile-container">
      <div className="brand-profile-left-panel">
        <Link href={"/dashboard"}>
          <div className="brand-profile-header">
            <Image
              src="/images/Vector.svg"
              alt="Corelia Logo"
              className="brand-profile-logo"
              width={24}
              height={24}
            />
            <span className="brand-profile-brand">Lance</span>
          </div>
        </Link>

        <div className="brand-profile-content">
          <h1 className="brand-profile-title">Set up your brand</h1>
          <p className="brand-profile-subtitle">
            Tell us about your business to create personalized social media
            content.
          </p>

          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="brand-profile-form"
            >
              {error && <div className="brand-profile-error">{error}</div>}

              <FormField
                control={form.control}
                name="company_name"
                render={({ field }) => (
                  <FormItem className="brand-profile-field">
                    <FormLabel className="brand-profile-label">
                      Company Name
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Enter your company name"
                        className="brand-profile-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="brand-profile-color-picker">
                <FormField
                  control={form.control}
                  name="primary_color"
                  render={({ field }) => (
                    <FormItem className="brand-profile-field">
                      <FormLabel className="brand-profile-label">
                        Primary Color
                      </FormLabel>
                      <FormControl>
                        <div className="brand-profile-color-row">
                          <input
                            type="color"
                            className="brand-profile-color-input"
                            {...field}
                          />
                          <Input
                            placeholder="#FF5733"
                            className="brand-profile-hex-input"
                            {...field}
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="secondary_color"
                  render={({ field }) => (
                    <FormItem className="brand-profile-field">
                      <FormLabel className="brand-profile-label">
                        Secondary Color
                      </FormLabel>
                      <FormControl>
                        <div className="brand-profile-color-row">
                          <input
                            type="color"
                            className="brand-profile-color-input"
                            {...field}
                          />
                          <Input
                            placeholder="#33A1FF"
                            className="brand-profile-hex-input"
                            {...field}
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="font_family"
                render={({ field }) => (
                  <FormItem className="brand-profile-field">
                    <FormLabel className="brand-profile-label">
                      Font Family
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Arial, Roboto, etc."
                        className="brand-profile-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="brand_voice"
                render={({ field }) => (
                  <FormItem className="brand-profile-field">
                    <FormLabel className="brand-profile-label">
                      Brand Voice
                    </FormLabel>
                    <FormControl>
                      <textarea
                        placeholder="Describe your brand's personality and tone..."
                        className="brand-profile-textarea"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="industry"
                render={({ field }) => (
                  <FormItem className="brand-profile-field">
                    <FormLabel className="brand-profile-label">
                      Industry
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Technology, Healthcare, etc."
                        className="brand-profile-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="target_audience"
                render={({ field }) => (
                  <FormItem className="brand-profile-field">
                    <FormLabel className="brand-profile-label">
                      Target Audience
                    </FormLabel>
                    <FormControl>
                      <textarea
                        placeholder="Who are your ideal customers?"
                        className="brand-profile-textarea"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="business_description"
                render={({ field }) => (
                  <FormItem className="brand-profile-field">
                    <FormLabel className="brand-profile-label">
                      Business Description
                    </FormLabel>
                    <FormControl>
                      <textarea
                        placeholder="What does your business do?"
                        className="brand-profile-textarea"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="brand-profile-file-upload">
                <FormLabel className="brand-profile-label">
                  Company Logo
                </FormLabel>
                <input
                  type="file"
                  accept="image/*"
                  className="brand-profile-file-input"
                  id="logo-upload"
                  onChange={handleLogoUpload}
                />
                <label
                  htmlFor="logo-upload"
                  className="brand-profile-file-label"
                >
                  {logoPreview ? "Change Logo" : "Upload Logo"}
                </label>
                {logoPreview && (
                  <img
                    src={logoPreview}
                    alt="Logo preview"
                    className="brand-profile-file-preview"
                  />
                )}
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="brand-profile-button"
              >
                {loading ? "Saving..." : "Save Brand Profile"}
              </Button>
            </form>
          </Form>

          <p className="brand-profile-footer">
            Skip for now?{" "}
            <Link href="/dashboard" className="brand-profile-link">
              Continue to Dashboard
            </Link>
          </p>
        </div>
      </div>

      <RightCard />
    </div>
  );
}

export default BrandProfile;
