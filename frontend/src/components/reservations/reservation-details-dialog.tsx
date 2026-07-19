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
import { useAuthStore } from "@/store/auth";
import type { Reserva } from "@/types";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { CheckCircle2, Clock, KeyRound } from "lucide-react";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "livre" | "outline"> = {
  confirmada: "livre",
  pendente: "secondary",
  cancelada: "destructive",
  concluida: "default",
  expirada: "outline",
};

export function ReservationDetailsDialog({
  reserva, aberto, aoFechar, aoAtualizar,
}: { reserva: Reserva | null; aberto: boolean; aoFechar: () => void; aoAtualizar: () => void }) {
  const { toast } = useToast();
  const isAdmin = useAuthStore((s) => s.isAdmin());
  const [motivo, setMotivo] = useState("");
  const [cancelando, setCancelando] = useState(false);
  const [confirmandoCheckin, setConfirmandoCheckin] = useState(false);

  if (!reserva) return null;

  async function cancelar() {
    setCancelando(true);
    try {
      await api.post(`/reservations/${reserva!.id}/cancelar/`, { motivo });
      toast({ title: "Reserva cancelada", description: "A reserva foi cancelada com sucesso." });
      aoAtualizar();
      aoFechar();
    } catch (err: unknown) {
      interface ErroApi {
        response?: { data?: { detail?: string } };
      }
      const detalhe = (err as ErroApi)?.response?.data?.detail;
      toast({
        variant: "destructive",
        title: "Erro",
        description: detalhe || "Não foi possível cancelar a reserva.",
      });
    } finally {
      setCancelando(false);
    }
  }

  async function confirmarCheckin() {
    setConfirmandoCheckin(true);
    try {
      await api.post(`/reservations/${reserva!.id}/checkin/`);
      toast({ title: "Check-in confirmado", description: "Presença registrada. A sala continua reservada para você." });
      aoAtualizar();
    } catch {
      toast({ variant: "destructive", title: "Erro", description: "Não foi possível confirmar o check-in." });
    } finally {
      setConfirmandoCheckin(false);
    }
  }

  // Cancelar é privilégio de administrador e só é possível enquanto a reserva ainda
  // está dentro do período vigente (backend aplica a mesma regra em /cancelar/).
  const dentroDoPeriodo = new Date(reserva.data_fim).getTime() > Date.now();
  const podeCancel =
    isAdmin && dentroDoPeriodo && (reserva.status === "confirmada" || reserva.status === "pendente");
  const aguardandoCheckin = reserva.precisa_checkin;
  const checkinConfirmado = Boolean(reserva.checkin_confirmado_em);

  return (
    <Dialog open={aberto} onOpenChange={(v) => !v && aoFechar()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <div className="flex flex-wrap items-center gap-2">
            <DialogTitle>{reserva.titulo}</DialogTitle>
            <Badge variant={statusVariant[reserva.status] ?? "default"}>{reserva.status_display}</Badge>
          </div>
          <p className="text-xs text-muted-foreground">Nº de controle: {reserva.numero_controle}</p>
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
          <p><span className="text-muted-foreground">Duração: </span>{reserva.duracao_display}</p>
          {reserva.reservado_para_categoria && (
            <p>
              <span className="text-muted-foreground">Reservado para: </span>
              {reserva.reservado_para_categoria_display} — {reserva.reservado_para_nome} ({reserva.reservado_para_telefone})
            </p>
          )}
          {reserva.descricao && <p><span className="text-muted-foreground">Descrição: </span>{reserva.descricao}</p>}

          {reserva.mensagem_guarita && (
            <div className="flex gap-2 rounded-md border border-primary/30 bg-primary/5 p-3 text-xs">
              <KeyRound className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
              <p>{reserva.mensagem_guarita}</p>
            </div>
          )}

          {reserva.ambiente_detalhe?.exige_checkin && (
            <div className="flex items-center gap-2 rounded-md border p-2 text-xs">
              {checkinConfirmado ? (
                <>
                  <CheckCircle2 className="h-4 w-4 text-livre-foreground" />
                  <span>
                    Check-in confirmado em{" "}
                    {format(new Date(reserva.checkin_confirmado_em as string), "dd/MM HH:mm", { locale: ptBR })}
                  </span>
                </>
              ) : (
                <>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span>
                    Este ambiente exige check-in. Prazo:{" "}
                    {format(new Date(reserva.prazo_checkin), "dd/MM HH:mm", { locale: ptBR })} — depois disso a
                    sala é liberada automaticamente.
                  </span>
                </>
              )}
            </div>
          )}
        </div>

        {podeCancel && (
          <div className="space-y-2">
            <Label htmlFor="motivo">Motivo do cancelamento (opcional)</Label>
            <Textarea id="motivo" value={motivo} onChange={(e) => setMotivo(e.target.value)} />
          </div>
        )}

        <DialogFooter className="flex-wrap gap-2 sm:justify-between">
          <BotaoWhatsApp reservaId={reserva.id} />
          <div className="flex gap-2">
            {aguardandoCheckin && (
              <Button onClick={confirmarCheckin} disabled={confirmandoCheckin}>
                <CheckCircle2 className="mr-2 h-4 w-4" />
                {confirmandoCheckin ? "Confirmando..." : "Confirmar check-in"}
              </Button>
            )}
            {podeCancel && (
              <Button variant="destructive" onClick={cancelar} disabled={cancelando}>
                {cancelando ? "Cancelando..." : "Cancelar reserva"}
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
