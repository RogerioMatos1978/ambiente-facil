"use client";
import { useState } from "react";
import { MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

/**
 * Busca telefone/mensagem prontos no backend e abre o aplicativo do WhatsApp
 * instalado e logado no computador (esquema whatsapp://send, não o WhatsApp
 * Web). Usa location.href em vez de window.open: para esquemas de URL
 * personalizados o navegador só aciona o handler do sistema operacional de
 * forma confiável se a navegação acontecer na própria aba.
 */
export function BotaoWhatsApp({ reservaId }: { reservaId: number }) {
  const [carregando, setCarregando] = useState(false);
  const { toast } = useToast();

  async function enviar() {
    setCarregando(true);
    try {
      const { data } = await api.get(`/reservations/${reservaId}/whatsapp/`);
      if (!data.link) {
        toast({
          variant: "destructive",
          title: "Telefone não cadastrado",
          description: "O solicitante não possui telefone cadastrado para WhatsApp.",
        });
        return;
      }
      window.location.href = data.link;
    } finally {
      setCarregando(false);
    }
  }

  return (
    <Button type="button" variant="outline" size="sm" onClick={enviar} disabled={carregando}>
      <MessageCircle className="mr-2 h-4 w-4 text-livre-foreground" />
      Enviar WhatsApp
    </Button>
  );
}
