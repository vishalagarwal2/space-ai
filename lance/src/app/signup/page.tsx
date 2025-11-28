"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import RightCard from "../../components/RightCard";
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
import { signupSchema } from "@/schema/signupSchema";
import { toast } from "sonner";
import { signUp } from "@/lib/api/auth";
import Link from "next/link";
import "./signup.css";

function Signup() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const form = useForm({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      username: "",
      first_name: "",
      last_name: "",
      email: "",
      password: "",
    },
  });

  const onSubmit = async (values: z.infer<typeof signupSchema>) => {
    setError("");
    setLoading(true);

    try {
      const response = await signUp(values);
      const data = response.data;

      if (data.status !== "success") {
        throw new Error(data.error || data.message || "Signup failed");
      }

      toast.success(data.message || "User registered successfully");
      localStorage.setItem("email", data.user.email);
      router.push("/login");
    } catch (err: unknown) {
      const message =
        (err as any)?.response?.data?.error ||
        (err as any)?.response?.data?.message ||
        (err as any)?.message ||
        "Signup failed";

      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="signup-container">
      <div className="signup-left-panel">
        <Link href={"/login"}>
          <div className="signup-header">
            <Image
              src="/images/Vector.svg"
              alt="Corelia Logo"
              className="signup-logo"
              width={24}
              height={24}
            />
            <span className="signup-brand">Lance</span>
          </div>
        </Link>

        <div className="signup-content">
          <h1 className="signup-title">Create new account</h1>
          <p className="signup-subtitle">
            Give us some of your information to get free access to fieldly.
          </p>

          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="signup-form"
            >
              {error && <div className="signup-error">{error}</div>}

              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem className="signup-field">
                    <FormLabel className="signup-label">Username</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Enter your username"
                        className="signup-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="first_name"
                render={({ field }) => (
                  <FormItem className="signup-field">
                    <FormLabel className="signup-label">First Name</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Enter your first name"
                        className="signup-input"
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
                  <FormItem className="signup-field">
                    <FormLabel className="signup-label">Last Name</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Enter your last name"
                        className="signup-input"
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
                  <FormItem className="signup-field">
                    <FormLabel className="signup-label">Email</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Enter your email"
                        className="signup-input"
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
                  <FormItem className="signup-field">
                    <FormLabel className="signup-label">Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="••••••"
                        className="signup-input"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button
                type="submit"
                disabled={loading}
                className="signup-button"
              >
                {loading ? "Sending code..." : "Sign up"}
              </Button>
            </form>
          </Form>

          <p className="signup-footer">
            Already have an account?{" "}
            <Link href="/login" className="signup-link">
              Sign in
            </Link>
          </p>
        </div>
      </div>

      <RightCard />
    </div>
  );
}

export default Signup;
