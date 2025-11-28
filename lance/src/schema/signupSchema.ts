import { z } from "zod";

export const signupSchema = z.object({
    username: z.string()
        .min(2, { message: "Username must be at least 2 characters" })
        .max(30, { message: "Username cannot exceed 30 characters" })
        .nonempty({ message: "Username is required" }),
    first_name: z.string()
        .min(2, { message: "First name must be at least 2 characters" })
        .max(30, { message: "First name cannot exceed 30 characters" })
        .nonempty({ message: "First name is required" }),
    last_name: z.string()
        .min(2, { message: "Last name must be at least 2 characters" })
        .max(30, { message: "Last name cannot exceed 30 characters" })
        .nonempty({ message: "Last name is required" }),
    email: z.string()
        .email({ message: "Invalid email format" })
        .nonempty({ message: "Email is required" }),
    password: z.string()
        .min(8, { message: "Password must be at least 8 characters" })
        .regex(/[A-Z]/, {
            message: "Password must contain at least one uppercase letter",
        })
        .regex(/[a-z]/, {
            message: "Password must contain at least one lowercase letter",
        })
        .regex(/[0-9]/, {
            message: "Password must contain at least one number",
        })
        .regex(/[\W_]/, {
            message: "Password must contain at least one special character",
        })
        .nonempty({ message: "Password is required" }),
})
