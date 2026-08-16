import type { Metadata } from "next";
import { Manrope, Space_Grotesk } from "next/font/google";
import "./globals.css";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Melo-AI",
  description: "Your personal AI. Fully local. Fully yours.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className="h-full"
    >
      <body
        className={`${manrope.variable} ${spaceGrotesk.variable} min-h-full flex flex-col`}
      >
        {children}
      </body>
    </html>
  );
}