"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import RightCard from "@/components/RightCard";
import { login } from "@/lib/api/auth";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { loginSchema } from "@/schema/loginSchema";
import { toast } from "sonner";
import Link from "next/link";
import "./login.css";
import { SpaceIcon } from "@/components/icons/SpaceIcon";

function Login() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const form = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: "",
      password: "",
    },
  });

  const onSubmit = async (values: z.infer<typeof loginSchema>) => {
    setError("");
    setLoading(true);

    try {
      const response = await login(values);
      const data = response.data;

      if (data.message !== "Login successful") {
        throw new Error(data.message || "Login failed");
      }
      toast.success("Login Successfully.");
      router.push("/dashboard");
    } catch (error: any) {
      const message =
        error.response?.data?.message || error.message || "Login failed";
      toast.error(message);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-left-panel">
        <div className="login-header">
          <SpaceIcon fill="#1ec3c8" height={24} />
          <span className="login-brand">Space AI</span>
        </div>

        <div className="login-content">
          <h1 className="login-title">Welcome back</h1>
          <p className="login-subtitle">
            Welcome back! Please enter your details.
          </p>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="login-form">
              {error && <div className="login-error">{error}</div>}

              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem className="form-field">
                    <FormLabel className="form-label">Username</FormLabel>
                    <FormControl>
                      <Input
                        type="text"
                        placeholder="Enter your username"
                        className="form-input"
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
                  <FormItem className="form-field">
                    <FormLabel className="form-label">Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="••••••"
                        className="form-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="form-options">
                <div className="remember-section">
                  <input
                    type="checkbox"
                    id="remember"
                    className="remember-checkbox"
                  />
                  <label htmlFor="remember" className="remember-label">
                    Remember me
                  </label>
                </div>
                <Link href="/forgetpassword" className="forgot-link">
                  Forgot password?
                </Link>
              </div>

              <Button type="submit" disabled={loading} className="login-button">
                {loading ? "Signing in..." : "Sign in"}
              </Button>
            </form>
          </Form>

          <p className="login-footer">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="signup-link">
              Sign up for Free
            </Link>
          </p>
        </div>
      </div>

      <RightCard />
    </div>
  );
}

export default Login;
