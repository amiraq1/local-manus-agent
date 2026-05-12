import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Local Manus Agent",
  description: "AI-powered local development agent",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-dark-950 text-dark-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
