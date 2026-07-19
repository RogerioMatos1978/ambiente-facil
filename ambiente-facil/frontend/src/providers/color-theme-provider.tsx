"use client";
import { useEffect } from "react";
import { useTemaCorStore } from "@/store/tema-cor";

/**
 * Aplica o tema de cor escolhido (SESI, SENAI, IEL, Sistema FIEG ou
 * combinado) como atributo `data-tema` no <html>, para que as regras em
 * globals.css (`:root[data-tema="..."]`) entrem em vigor. Funciona em
 * conjunto com o ThemeProvider (next-themes) que cuida do claro/escuro.
 */
export function ColorThemeProvider({ children }: { children: React.ReactNode }) {
  const tema = useTemaCorStore((s) => s.tema);

  useEffect(() => {
    document.documentElement.setAttribute("data-tema", tema);
  }, [tema]);

  return <>{children}</>;
}
