import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GEOS Agent",
  description: "AI assistant for GEOS multiphysics simulations",
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
