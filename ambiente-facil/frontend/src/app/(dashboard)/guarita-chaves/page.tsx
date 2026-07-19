"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { usePainelTempoReal } from "@/hooks/use-painel-tempo-real";
import type { Chave } from "@/types";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { KeyRound, MapPin, UserRound } from "lucide-react";

const STATUS_BADGE: Record<Chave["status"], "livre" | "ocupado"> = {
  disponivel: "livre",
  ocupada: "ocupado",
};

/**
 * Painel da guarita: uma chave por ambiente, amarrada às reservas do dia. Acesso
 * restrito a administrador e vigilante (ver (dashboard)/layout.tsx e NaoEhVigilante
 * no backend) — usuário comum não chega aqui.
 */
export default function GuaritaChavesPage() {
  const { toast } = useToast();
  const { ultimoEvento } = usePainelTempoReal();
  const [chaves, setChaves] = useState<Chave[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [processando, setProcessando] = useState<number | null>(null);
  const ultimoAlertaTratadoRef = useRef<string | null>(null);

  const carregar = useCallback(async () => {
    try {
      const { data } = await api.get("/guarita/chaves/");
      setChaves(data.results ?? data);
    } catch {
      toast({ variant: "destructive", title: "Erro", description: "Não foi possível carregar a guarita de chaves." });
    } finally {
      setCarregando(false);
    }
  }, [toast]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  // Alerta em tempo real: assim que o job de fundo detecta uma chave não devolvida
  // 10 min após o fim da reserva (ver apps/keys/management/commands/
  // alertar_chaves_atrasadas.py), o vigilante com esta página aberta recebe o aviso na
  // hora, sem precisar recarregar.
  useEffect(() => {
    if (!ultimoEvento || ultimoEvento.tipo !== "chave_atrasada") return;
    const chaveDoAlerta = `${ultimoEvento.ambiente_id}-${ultimoEvento.reserva_id}`;
    if (ultimoAlertaTratadoRef.current === chaveDoAlerta) return;
    ultimoAlertaTratadoRef.current = chaveDoAlerta;

    toast({
      variant: "destructive",
      title: "Chave não devolvida",
      description: typeof ultimoEvento.mensagem === "string" ? ultimoEvento.mensagem : "Uma chave passou do horário de devolução.",
    });
    carregar();
  }, [ultimoEvento, toast, carregar]);

  async function retirar(ambienteId: number, reservaId: number) {
    setProcessando(ambienteId);
    try {
      await api.post(`/guarita/chaves/${ambienteId}/retirar/`, { reserva: reservaId });
      toast({ title: "Chave retirada" });
      carregar();
    } catch {
      toast({ variant: "destructive", title: "Erro", description: "Não foi possível retirar a chave." });
    } finally {
      setProcessando(null);
    }
  }

  async function devolver(ambienteId: number) {
    setProcessando(ambienteId);
    try {
      await api.post(`/guarita/chaves/${ambienteId}/devolver/`, {});
      toast({ title: "Chave devolvida" });
      carregar();
    } catch {
      toast({ variant: "destructive", title: "Erro", description: "Não foi possível registrar a devolução." });
    } finally {
      setProcessando(null);
    }
  }

  if (carregando) {
    return <div className="flex min-h-[50vh] items-center justify-center text-muted-foreground">Carregando...</div>;
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Retire a chave amarrando-a à reserva do dia correspondente. Ao devolver, a reserva é encerrada
        e a sala e a chave já ficam disponíveis na hora, para qualquer ambiente — não existe um passo
        extra de conferência manual. Se a chave não for devolvida até 10 minutos depois do fim da
        reserva, um alerta chega aqui automaticamente.
      </p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {chaves.map((chave) => (
          <Card key={chave.id}>
            <CardHeader className="space-y-1">
              <div className="flex items-center justify-between gap-2">
                <CardTitle className="text-base">{chave.ambiente_nome}</CardTitle>
                <Badge variant={STATUS_BADGE[chave.status]}>{chave.status_display}</Badge>
              </div>
              {chave.ambiente_localizacao && (
                <p className="flex items-center gap-1 text-xs text-muted-foreground">
                  <MapPin className="h-3.5 w-3.5" /> {chave.ambiente_localizacao}
                </p>
              )}
            </CardHeader>
            <CardContent className="space-y-3">
              {chave.status === "ocupada" && chave.reserva_atual_detalhe && (
                <div className="space-y-1 rounded-md border p-2 text-xs">
                  <p className="font-medium">{chave.reserva_atual_detalhe.numero_controle} — {chave.reserva_atual_detalhe.titulo}</p>
                  <p className="flex items-center gap-1 text-muted-foreground">
                    <UserRound className="h-3.5 w-3.5" />
                    {chave.reserva_atual_detalhe.reservado_para_categoria_display}: {chave.reserva_atual_detalhe.reservado_para_nome} ({chave.reserva_atual_detalhe.reservado_para_telefone})
                  </p>
                  <p className="text-muted-foreground">
                    {format(new Date(chave.reserva_atual_detalhe.data_inicio), "HH:mm", { locale: ptBR })} –{" "}
                    {format(new Date(chave.reserva_atual_detalhe.data_fim), "HH:mm", { locale: ptBR })}
                    {" · "}{chave.reserva_atual_detalhe.duracao_display}
                  </p>
                  {chave.retirada_por_nome && (
                    <p className="text-muted-foreground">Retirada por {chave.retirada_por_nome}</p>
                  )}
                </div>
              )}

              {chave.status === "disponivel" && (
                <div className="space-y-2">
                  {chave.reservas_hoje.length === 0 && (
                    <p className="text-xs text-muted-foreground">Nenhuma reserva para hoje.</p>
                  )}
                  {chave.reservas_hoje.map((reserva) => (
                    <div key={reserva.id} className="flex items-center justify-between gap-2 rounded-md border p-2 text-xs">
                      <div className="min-w-0">
                        <p className="truncate font-medium">{reserva.numero_controle} — {reserva.titulo}</p>
                        <p className="text-muted-foreground">
                          {format(new Date(reserva.data_inicio), "HH:mm", { locale: ptBR })}–
                          {format(new Date(reserva.data_fim), "HH:mm", { locale: ptBR })} ·{" "}
                          {reserva.reservado_para_nome}
                        </p>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={processando === chave.ambiente}
                        onClick={() => retirar(chave.ambiente, reserva.id)}
                      >
                        <KeyRound className="mr-1 h-3.5 w-3.5" /> Retirar
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              {chave.status === "ocupada" && (
                <Button
                  size="sm"
                  className="w-full"
                  disabled={processando === chave.ambiente}
                  onClick={() => devolver(chave.ambiente)}
                >
                  Devolver chave
                </Button>
              )}

            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
