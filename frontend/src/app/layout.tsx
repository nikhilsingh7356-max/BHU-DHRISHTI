import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "Bhu-Drishti | National Land Acquisition & Management System",
  description: "Integrated platform for land acquisition and management across India",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <AuthProvider>
          {children}
          <Toaster position="top-right" />
        </AuthProvider>
      </body>
    </html>
  );
}
