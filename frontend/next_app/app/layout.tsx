import type { Metadata } from "next";
import "./globals.css";
import "katex/dist/katex.min.css";
import ThemeProvider from "../lib/ThemeProvider";

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
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem("theme");document.documentElement.dataset.theme=t==="dark"?"dark":"light"}catch(e){}})()`,
          }}
        />
      </head>
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
