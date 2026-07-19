"use client";
import { useState } from "react";
import { MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

/**
 * Busca telefone/mensagem prontos no backend e abre o link `https://wa.me/...` numa
 * nova aba — funciona tanto abrindo o app do WhatsApp (se instalado) quanto o
 * WhatsApp Web no navegador como alternativa. Só disponível para reservas com status
 * Confirmada (o backend recusa a chamada para os demais status).
 */
export function BotaoWhatsApp({ reservaId, statusReserva }: { reservaId: number; statusReserva: string }) {
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
          description: "Nem o responsável (\"Reservado para\") nem o solicitante têm telefone cadastrado.",
        });
        return;
      }
      window.open(data.link, "_blank", "noopener,noreferrer");
    } catch {
      toast({
        variant: "destructive",
        title: "Não foi possível enviar",
        description: "Só é possível enviar WhatsApp para reservas com status Confirmada.",
      });
    } finally {
      setCarregando(false);
    }
  }

  if (statusReserva !== "confirmada") return null;

  return (
    <Button type="button" variant="outline" size="sm" onClick={enviar} disabled={carregando}>
      <MessageCircle className="mr-2 h-4 w-4 text-livre-foreground" />
      Enviar WhatsApp
    </Button>
  );
}
