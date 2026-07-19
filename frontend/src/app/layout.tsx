import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/providers/theme-provider";
import { ColorThemeProvider } from "@/providers/color-theme-provider";
import { Toaster } from "@/components/ui/toaster";

export const metadata: Metadata = {
  title: "Ambiente Fácil",
  description: "Gerenciamento e agendamento de ambientes institucionais",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-br" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <ColorThemeProvider>
            {children}
            <Toaster />
          </ColorThemeProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
