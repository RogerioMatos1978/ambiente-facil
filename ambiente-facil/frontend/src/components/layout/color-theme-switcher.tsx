"use client";
import { Check, Palette } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { OPCOES_TEMA_COR, useTemaCorStore } from "@/store/tema-cor";

export function ColorThemeSwitcher() {
  const tema = useTemaCorStore((s) => s.tema);
  const setTema = useTemaCorStore((s) => s.setTema);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Escolher cor do sistema">
          <Palette className="h-5 w-5" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel>Cor do sistema</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {OPCOES_TEMA_COR.map((opcao) => (
          <DropdownMenuItem
            key={opcao.id}
            className="flex items-center gap-3 py-2"
            onClick={() => setTema(opcao.id)}
          >
            <span
              className="flex h-6 w-6 shrink-0 overflow-hidden rounded-full border"
              style={{
                background: `linear-gradient(135deg, ${opcao.corPrincipal} 50%, ${opcao.corDetalhe} 50%)`,
              }}
              aria-hidden
            />
            <span className="flex-1">
              <span className="block text-sm font-medium leading-none">{opcao.label}</span>
              <span className="mt-1 block text-xs text-muted-foreground">{opcao.descricao}</span>
            </span>
            {tema === opcao.id && <Check className="h-4 w-4 shrink-0 text-primary" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
