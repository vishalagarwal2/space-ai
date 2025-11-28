import { z } from "zod";

export const loginSchema = z.object({
    username: z.string()
        .min(2, { message: "Username must be at least 2 characters" })
        .nonempty({ message: "Username is required" }),
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
