import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "@/components/Providers";
import { BottomNav } from "@/components/BottomNav";
import { LocaleHtmlLang } from "@/components/LocaleHtmlLang";
import { ServiceWorkerRegistrar } from "@/components/ServiceWorkerRegistrar";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || "https://hustle-coach.renu-01.cranecloud.io"),
  title: "HustleScale — The National Youth Micro-Enterprise Accelerator",
  description:
    "Empowering Uganda's youth (18-30) to turn business ideas into sustainable, scalable micro-enterprises. " +
    "AI-powered business plans, funding matching, progress tracking, and mentorship — in your language.",
  manifest: "/manifest.json",
  openGraph: {
    title: "HustleScale — Youth Micro-Enterprise Accelerator",
    description:
      "AI-powered business plans, funding matching, market prices, and mentorship for Uganda's youth entrepreneurs. 27 business models. 13 funding sources.",
    siteName: "HustleScale",
    locale: "en_UG",
    type: "website",
    url: "/",
    images: [
      { url: "/og-image.svg", width: 1200, height: 630, alt: "HustleScale — Youth Micro-Enterprise Accelerator for Uganda", type: "image/svg+xml" },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "HustleScale — Youth Micro-Enterprise Accelerator",
    description:
      "AI-powered business plans, funding matching, market prices & coaching for Uganda's youth entrepreneurs.",
    images: ["/og-image.svg"],
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "HustleScale",
  },
  other: {
    "mobile-web-app-capable": "yes",
  },
};

export const viewport: Viewport = {
  themeColor: "#2D6A4F",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/icons/icon-192.png" />
        <link rel="apple-touch-icon" href="/icons/icon-192.png" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){var t=localStorage.getItem('hustle-scale-theme');if(t==='dark'||t==='light')document.documentElement.setAttribute('data-theme',t);})();`,
          }}
        />
      </head>
      <body>
        <LocaleHtmlLang />
        <ServiceWorkerRegistrar />
        <a href="#main" className="skip-link">
          Skip to main content
        </a>
        <Providers>
          {children}
          <BottomNav />
        </Providers>
      </body>
    </html>
  );
}
