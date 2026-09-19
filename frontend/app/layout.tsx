import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/Providers";
import SmoothScroll from "@/components/providers/SmoothScroll";

export const metadata: Metadata = {
  title: "Fear-Free Family Truth Companion",
  description: "Understand your loan. Involve your family. Decide with confidence.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900 selection:bg-teal-100 selection:text-teal-900">
        <SmoothScroll>
          <Providers>
            <div className="flex-1 flex flex-col">{children}</div>
            <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
              <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-1">
                <p className="font-medium text-slate-700">
                  Fear-Free Family Truth Companion — Neutral, Consent-First Financial Clarity
                </p>
                <p>
                  We do not sell loans, rank sponsored products, or guarantee lender safety. Designed for Indian home loan borrowers.
                </p>
              </div>
            </footer>
          </Providers>
        </SmoothScroll>
      </body>
    </html>
  );
}
