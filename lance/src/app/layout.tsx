import type { Metadata } from "next";
import { Geist, Geist_Mono, Aleo } from "next/font/google";
import "./globals.css";
import QueryProvider from "@/lib/providers/QueryProvider";
import { BusinessProfileProvider } from "@/contexts/BusinessProfileContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const aleo = Aleo({
  variable: "--font-aleo",
  subsets: ["latin"],
  weight: ["300", "400", "700"],
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "Space AI",
  description: "Space AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${aleo.variable}`}
      >
        <QueryProvider>
          <BusinessProfileProvider>{children}</BusinessProfileProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
