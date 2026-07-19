"use client";
import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * Botão de "Atualizar site" visível em todas as páginas, para qualquer usuário.
 * Faz um reload completo da página (equivalente a F5/Ctrl+R), mas dentro do próprio
 * sistema — não depende do usuário lembrar do atalho do navegador. Com o refresh token
 * agora sendo renovado corretamente a cada uso (ver lib/api.ts), atualizar a página não
 * derruba mais para o login enquanto a sessão ainda for válida.
 */
export function RefreshButton() {
  const [atualizando, setAtualizando] = useState(false);

  function atualizar() {
    setAtualizando(true);
    window.location.reload();
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label="Atualizar site"
      title="Atualizar site"
      onClick={atualizar}
      disabled={atualizando}
    >
      <RefreshCw className={`h-5 w-5 ${atualizando ? "animate-spin" : ""}`} />
    </Button>
  );
}
