export interface SignUpValues {
    username: string;
    email: string;
    password: string;
    first_name: string;
    last_name: string;
}

export interface LoginValues {
    username: string;
    password: string;
}

export interface VerifyOtpValues {
    email: string;
    otp: string;
}

export interface ForgotPassword {
    email: string
}

export interface ResetPassword {
    email: string | null,
    new_password: string,
    confirm_password: string
}

export interface User {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    is_staff: boolean;
    is_superuser: boolean;
    date_joined: string;
    last_login: string;
}

export interface ProfileResponse {
    message: string;
    status: string;
    user: User;
}
