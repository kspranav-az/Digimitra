import type { Metadata } from "next";
import { Inter } from "next/font/google";
import AIAgentPanel from "../components/ai-agent";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Police AI Dashboard",
  description: "AI-powered surveillance for law enforcement",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={inter.className}>
        {children}
        <AIAgentPanel />
      </body>
    </html>
  );
}
