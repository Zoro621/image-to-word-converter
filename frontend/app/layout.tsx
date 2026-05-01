import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "DocuVision — Agentic Document Intelligence",
  description:
    "AI-powered document extraction with a multi-agent pipeline. Upload handwritten notes, diagrams, and forms to get formatted Word documents in seconds.",
  keywords: "OCR, document extraction, AI, vision model, handwriting recognition",
  openGraph: {
    title: "DocuVision — Agentic Document Intelligence",
    description: "AI-powered document extraction with multi-agent reasoning.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="antialiased">{children}</body>
    </html>
  );
}
