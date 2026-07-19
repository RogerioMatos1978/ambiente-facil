"use client";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useConfiguracaoSistemaStore } from "@/store/configuracao-sistema";

/**
 * Renderiza o ícone de um item de navegação (Sidebar/MobileNav) de acordo com o
 * estilo global escolhido em /configuracoes (admin). "padrao" mantém o
 * comportamento original (ícone puro, sem moldura).
 */
export function NavIcon({ icone: Icone, ativo }: { icone: LucideIcon; ativo?: boolean }) {
  const estilo = useConfiguracaoSistemaStore((s) => s.estiloIcone);

  if (estilo === "contornado") {
    return (
      <span
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-md border",
          ativo ? "border-primary-foreground/40" : "border-border"
        )}
      >
        <Icone className="h-4 w-4" />
      </span>
    );
  }

  if (estilo === "preenchido") {
    return (
      <span
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-md",
          ativo ? "bg-primary-foreground/20" : "bg-primary/10 text-primary"
        )}
      >
        <Icone className="h-4 w-4" />
      </span>
    );
  }

  return <Icone className="h-4 w-4 shrink-0" />;
}
