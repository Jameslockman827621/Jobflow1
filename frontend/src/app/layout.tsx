import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "JobScale - AI Career Accelerator",
  description: "Find and land your dream job with AI-powered applications",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
