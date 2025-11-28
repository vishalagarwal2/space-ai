"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
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
import axiosInstance from "@/lib/axios";
import "./business-login.css";
import { SpaceButton } from "@/components/base/SpaceButton";

const businessLoginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
});

function BusinessLogin() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const form = useForm({
    resolver: zodResolver(businessLoginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (values: z.infer<typeof businessLoginSchema>) => {
    setError("");
    setLoading(true);

    try {
      const response = await axiosInstance.post(
        "/api/business/auth/login/",
        values
      );

      if (response.data.status !== "success") {
        throw new Error(
          response.data.error || response.data.message || "Login failed"
        );
      }

      toast.success("Login successful!");
      router.push("/dashboard");
    } catch (err: unknown) {
      const error = err as any;
      const message =
        error?.response?.data?.error ||
        error?.response?.data?.message ||
        error?.message ||
        "Login failed. Please try again.";
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="business-login-container">
      <div className="business-login-content">
        <div
          className="business-login-header"
          style={{ cursor: "pointer" }}
          onClick={() => router.push("/")}
        >
          <SpaceIcon fill="#FF2E01" height={32} />
          <span className="business-login-brand">Space AI</span>
        </div>

        <div className="business-login-form-wrapper">
          <h1 className="business-login-title">Login</h1>

          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="business-login-form"
            >
              {error && <div className="business-login-error">{error}</div>}

              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem className="business-login-field">
                    <FormLabel className="business-login-label">
                      Email:
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder=""
                        className="business-login-input"
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
                  <FormItem className="business-login-field">
                    <FormLabel className="business-login-label">
                      Password:
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder=""
                        className="business-login-input"
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
                <SpaceButton type="submit" disabled={loading}>
                  {loading ? "Signing in..." : "Continue"}
                </SpaceButton>
              </div>
            </form>
          </Form>

          <p className="business-login-footer">
            Don&apos;t have an account?{" "}
            <Link href="/business-signup" className="business-login-link">
              Sign up for free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default BusinessLogin;
