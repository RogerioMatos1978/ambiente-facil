"use client";
import { useState } from "react";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { BotaoWhatsApp } from "./whatsapp-button";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import type { Reserva } from "@/types";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "livre"> = {
  confirmada: "livre",
  pendente: "secondary",
  cancelada: "destructive",
  concluida: "default",
};

export function ReservationDetailsDialog({
  reserva, aberto, aoFechar, aoAtualizar,
}: { reserva: Reserva | null; aberto: boolean; aoFechar: () => void; aoAtualizar: () => void }) {
  const { toast } = useToast();
  const [motivo, setMotivo] = useState("");
  const [cancelando, setCancelando] = useState(false);

  if (!reserva) return null;

  async function cancelar() {
    setCancelando(true);
    try {
      await api.post(`/reservations/${reserva!.id}/cancelar/`, { motivo });
      toast({ title: "Reserva cancelada", description: "A reserva foi cancelada com sucesso." });
      aoAtualizar();
      aoFechar();
    } catch {
      toast({ variant: "destructive", title: "Erro", description: "Não foi possível cancelar a reserva." });
    } finally {
      setCancelando(false);
    }
  }

  const podeCancel = reserva.status === "confirmada" || reserva.status === "pendente";

  return (
    <Dialog open={aberto} onOpenChange={(v) => !v && aoFechar()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <DialogTitle>{reserva.titulo}</DialogTitle>
            <Badge variant={statusVariant[reserva.status] ?? "default"}>{reserva.status}</Badge>
          </div>
        </DialogHeader>

        <div className="space-y-2 text-sm">
          <p><span className="text-muted-foreground">Ambiente: </span>{reserva.ambiente_detalhe?.nome}</p>
          <p><span className="text-muted-foreground">Solicitante: </span>{reserva.solicitante_nome}</p>
          <p>
            <span className="text-muted-foreground">Início: </span>
            {format(new Date(reserva.data_inicio), "dd/MM/yyyy HH:mm", { locale: ptBR })}
          </p>
          <p>
            <span className="text-muted-foreground">Fim: </span>
            {format(new Date(reserva.data_fim), "dd/MM/yyyy HH:mm", { locale: ptBR })}
          </p>
          {reserva.descricao && <p><span className="text-muted-foreground">Descrição: </span>{reserva.descricao}</p>}
        </div>

        {podeCancel && (
          <div className="space-y-2">
            <Label htmlFor="motivo">Motivo do cancelamento (opcional)</Label>
            <Textarea id="motivo" value={motivo} onChange={(e) => setMotivo(e.target.value)} />
          </div>
        )}

        <DialogFooter className="flex-wrap gap-2 sm:justify-between">
          <BotaoWhatsApp reservaId={reserva.id} />
          {podeCancel && (
            <Button variant="destructive" onClick={cancelar} disabled={cancelando}>
              {cancelando ? "Cancelando..." : "Cancelar reserva"}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
