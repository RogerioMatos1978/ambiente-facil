"use client";
import { useState } from "react";
import { MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

/** Busca telefone/mensagem prontos no backend e abre o WhatsApp Web/App via wa.me com o texto preenchido. */
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
      window.open(data.link, "_blank", "noopener,noreferrer");
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
