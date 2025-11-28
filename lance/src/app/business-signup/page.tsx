"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { SpaceButton } from "@/components/base/SpaceButton";
import { Input } from "@/components/ui/input";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { toast } from "sonner";
import Link from "next/link";
import { SpaceIcon } from "@/components/icons/SpaceIcon";
import "./business-signup.css";
import { API_URL } from "@/lib/axios";

const businessSignupSchema = z.object({
  first_name: z.string().min(1, "First name is required"),
  last_name: z.string().min(1, "Last name is required"),
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

function BusinessSignup() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const form = useForm({
    resolver: zodResolver(businessSignupSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      email: "",
      password: "",
    },
  });

  const onSubmit = async (values: z.infer<typeof businessSignupSchema>) => {
    setError("");
    setLoading(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || API_URL}/api/business/auth/register/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify(values),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || data.message || "Signup failed");
      }

      toast.success("Account created successfully!");
      router.push("/business-onboarding");
    } catch (err: unknown) {
      const error = err as Error;
      const message = error?.message || "Signup failed. Please try again.";
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="business-signup-container">
      <div className="business-signup-content">
        <div
          onClick={() => router.push("/")}
          style={{ cursor: "pointer" }}
          className="business-signup-header"
        >
          <SpaceIcon fill="#FF2E01" height={32} />
          <span className="business-signup-brand">Space AI</span>
        </div>

        <div className="business-signup-form-wrapper">
          <h1 className="business-signup-title">Sign up</h1>
          <p className="business-signup-subtitle">
            Create your account to get started
          </p>

          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="business-signup-form"
            >
              {error && <div className="business-signup-error">{error}</div>}

              <FormField
                control={form.control}
                name="first_name"
                render={({ field }) => (
                  <FormItem className="business-signup-field">
                    <FormLabel className="business-signup-label">
                      First Name:
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder=""
                        className="business-signup-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="last_name"
                render={({ field }) => (
                  <FormItem className="business-signup-field">
                    <FormLabel className="business-signup-label">
                      Last Name:
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder=""
                        className="business-signup-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem className="business-signup-field">
                    <FormLabel className="business-signup-label">
                      Email:
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder=""
                        className="business-signup-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem className="business-signup-field">
                    <FormLabel className="business-signup-label">
                      Password:
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder=""
                        className="business-signup-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  width: "100%",
                }}
              >
                <SpaceButton
                  type="submit"
                  disabled={loading}
                  className="business-signup-button"
                >
                  {loading ? "Creating account..." : "Continue"}
                </SpaceButton>
              </div>
            </form>
          </Form>

          <p className="business-signup-footer">
            Already have an account?{" "}
            <Link href="/business-login" className="business-signup-link">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default BusinessSignup;
