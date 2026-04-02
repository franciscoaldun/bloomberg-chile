import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BLOOMBERG CHILE",
  description: "Panel de datos economicos de Chile — Fuente: Banco Central de Chile",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="h-full">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans+Condensed:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="h-screen w-screen overflow-hidden">{children}</body>
    </html>
  );
}
