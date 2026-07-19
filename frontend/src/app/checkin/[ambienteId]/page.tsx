"use client";
import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useAuthGuard } from "@/hooks/use-auth-guard";
import { useToast } from "@/hooks/use-toast";
import { usePainelTempoReal } from "@/hooks/use-painel-tempo-real";
import type { Ambiente, Reserva } from "@/types";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { CheckCircle2, Clock, MapPin, Users, ArrowLeft } from "lucide-react";

const DURACOES = [
  { minutos: 15, rotulo: "15 min" },
  { minutos: 30, rotulo: "30 min" },
  { minutos: 60, rotulo: "1 hora" },
];

/**
 * Página de destino do QR code colado na porta da sala. Pensada para uso
 * rápido pelo celular: mostra se o ambiente está livre/ocupado, permite
 * check-in de quem já reservou e reserva rápida de quem chegou sem reserva.
 */
export default function CheckinAmbientePage() {
  const pronto = useAuthGuard();
  const params = useParams<{ ambienteId: string }>();
  const router = useRouter();
  const { toast } = useToast();
  const usuario = useAuthStore((s) => s.usuario);
  const { ultimoEvento } = usePainelTempoReal();

  const [ambiente, setAmbiente] = useState<Ambiente | null>(null);
  const [reservaAtual, setReservaAtual] = useState<Reserva | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [enviando, setEnviando] = useState(false);

  const ambienteId = Number(params.ambienteId);

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const [ambienteRes, reservasRes] = await Promise.all([
        api.get(`/environments/${ambienteId}/`),
        api.get("/reservations/", {
          params: { ambiente: ambienteId, status: "confirmada", ordering: "data_inicio", page_size: 5 },
        }),
      ]);
      setAmbiente(ambienteRes.data);
      const agora = new Date();
      const proxima = (reservasRes.data.results as Reserva[]).find((r) => new Date(r.data_fim) >= agora);
      setReservaAtual(proxima ?? null);
    } catch {
      toast({ variant: "destructive", title: "Erro", description: "Não foi possível carregar este ambiente." });
    } finally {
      setCarregando(false);
    }
  }, [ambienteId, toast]);

  useEffect(() => {
    if (pronto && ambienteId) carregar();
  }, [pronto, ambienteId, carregar]);

  useEffect(() => {
    if (ultimoEvento?.ambiente_id === ambienteId) carregar();
  }, [ultimoEvento, ambienteId, carregar]);

  async function reservarAgora(duracaoMinutos: number) {
    setEnviando(true);
    try {
      await api.post("/reservations/rapida/", { ambiente: ambienteId, duracao_minutos: duracaoMinutos });
      toast({ title: "Sala reservada!", description: `Reservada por ${duracaoMinutos} minutos a partir de agora.` });
      carregar();
    } catch {
      toast({
        variant: "destructive",
        title: "Não foi possível reservar",
        description: "Alguém pode ter reservado essa sala agora mesmo.",
      });
    } finally {
      setEnviando(false);
    }
  }

  async function confirmarCheckin() {
    if (!reservaAtual) return;
    setEnviando(true);
    try {
      await api.post(`/reservations/${reservaAtual.id}/checkin/`);
      toast({ title: "Check-in confirmado", description: "Presença registrada com sucesso." });
      carregar();
    } catch {
      toast({ variant: "destructive", title: "Erro", description: "Não foi possível confirmar o check-in." });
    } finally {
      setEnviando(false);
    }
  }

  if (!pronto || carregando || !ambiente) {
    return <div className="flex min-h-screen items-center justify-center text-muted-foreground">Carregando...</div>;
  }

  const livre = ambiente.status_atual === "livre";
  const ehMinhaReserva = reservaAtual?.solicitante === usuario?.id;
  const aguardandoCheckin = Boolean(reservaAtual?.precisa_checkin) && ehMinhaReserva;

  return (
    <div className="mx-auto min-h-screen max-w-md space-y-4 p-4">
      <Button variant="ghost" size="sm" onClick={() => router.push("/dashboard")}>
        <ArrowLeft className="mr-2 h-4 w-4" /> Painel completo
      </Button>

      <Card>
        <CardHeader className="space-y-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl">{ambiente.nome}</CardTitle>
            <Badge variant={livre ? "livre" : "ocupado"} className="text-sm">
              {livre ? "Livre" : "Ocupado"}
            </Badge>
          </div>
          <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
            {ambiente.localizacao && (
              <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> {ambiente.localizacao}</span>
            )}
            <span className="flex items-center gap-1"><Users className="h-3.5 w-3.5" /> {ambiente.capacidade} lugares</span>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {!livre && reservaAtual && (
            <div className="space-y-2 rounded-md border p-3 text-sm">
              <p className="font-medium">{reservaAtual.titulo}</p>
              <p className="text-muted-foreground">{reservaAtual.solicitante_nome}</p>
              <p className="text-muted-foreground">
                {format(new Date(reservaAtual.data_inicio), "dd/MM HH:mm", { locale: ptBR })} —{" "}
                {format(new Date(reservaAtual.data_fim), "dd/MM HH:mm", { locale: ptBR })} ({reservaAtual.duracao_display})
              </p>

              {reservaAtual.checkin_confirmado_em && (
                <p className="flex items-center gap-1 text-livre-foreground">
                  <CheckCircle2 className="h-4 w-4" /> Check-in confirmado
                </p>
              )}

              {aguardandoCheckin && (
                <Button className="w-full" onClick={confirmarCheckin} disabled={enviando}>
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  {enviando ? "Confirmando..." : "Confirmar check-in"}
                </Button>
              )}

              {!ehMinhaReserva && reservaAtual.precisa_checkin && (
                <p className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3.5 w-3.5" /> Aguardando check-in de quem reservou —
                  prazo até {format(new Date(reservaAtual.prazo_checkin), "HH:mm", { locale: ptBR })}.
                </p>
              )}
            </div>
          )}

          {livre && (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Sala livre agora. Reservar por quanto tempo?</p>
              <div className="flex gap-2">
                {DURACOES.map((d) => (
                  <Button key={d.minutos} className="flex-1" disabled={enviando} onClick={() => reservarAgora(d.minutos)}>
                    {d.rotulo}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
