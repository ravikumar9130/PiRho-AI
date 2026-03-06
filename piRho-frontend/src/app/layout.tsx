import type { Metadata, Viewport } from "next";
import { Space_Grotesk, Orbitron, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const orbitron = Orbitron({
  subsets: ["latin"],
  variable: "--font-orbitron",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "piRho - AI-Powered Crypto Trading",
    template: "%s | piRho",
  },
  description: "Institutional-grade automated trading for crypto futures with LSTM neural networks and 11 battle-tested strategies.",
  keywords: ["crypto", "trading", "bot", "automated", "AI", "LSTM", "futures", "bybit"],
  authors: [{ name: "piRho" }],
  creator: "piRho",
  publisher: "piRho",
  robots: {
    index: true,
    follow: true,
  },
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
    ],
    apple: [
      { url: "/apple-touch-icon.svg", type: "image/svg+xml" },
    ],
    shortcut: "/favicon.svg",
  },
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "piRho",
  },
  formatDetection: {
    telephone: false,
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "piRho",
    title: "piRho - AI-Powered Crypto Trading",
    description: "Institutional-grade automated trading for crypto futures",
  },
  twitter: {
    card: "summary_large_image",
    title: "piRho - AI-Powered Crypto Trading",
    description: "Institutional-grade automated trading for crypto futures",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#030712" },
    { media: "(prefers-color-scheme: light)", color: "#00FFFF" },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="application-name" content="piRho" />
        <meta name="apple-mobile-web-app-title" content="piRho" />
        <meta name="msapplication-TileColor" content="#00FFFF" />
        <meta name="msapplication-tap-highlight" content="no" />
      </head>
      <body
        className={`${spaceGrotesk.variable} ${orbitron.variable} ${jetbrainsMono.variable} font-sans antialiased bg-surface-950 text-white`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
