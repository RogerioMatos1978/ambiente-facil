"use client";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import type { Ambiente } from "@/types";
import { Zap } from "lucide-react";

const DURACOES = [
  { minutos: 15, rotulo: "15 min" },
  { minutos: 30, rotulo: "30 min" },
  { minutos: 60, rotulo: "1 hora" },
];

/**
 * Atalho de 1 clique: reserva agora mesmo o ambiente livre escolhido, por
 * uma duração curta pré-definida. Pensado para o caso comum "preciso de
 * uma sala agora, entre uma aula e outra".
 */
export function ReservaRapida({ aoReservar }: { aoReservar: () => void }) {
  const { toast } = useToast();
  const [ambientes, setAmbientes] = useState<Ambiente[]>([]);
  const [ambienteId, setAmbienteId] = useState<number | undefined>(undefined);
  const [enviando, setEnviando] = useState(false);

  async function carregarLivres() {
    const res = await api.get("/environments/", { params: { page_size: 100, ativo: true } });
    const livres = (res.data.results as Ambiente[]).filter((a) => a.status_atual === "livre");
    setAmbientes(livres);
    setAmbienteId((atual) => (livres.some((a) => a.id === atual) ? atual : livres[0]?.id));
  }

  useEffect(() => {
    carregarLivres();
  }, []);

  async function reservar(duracaoMinutos: number) {
    if (!ambienteId) return;
    setEnviando(true);
    try {
      await api.post("/reservations/rapida/", { ambiente: ambienteId, duracao_minutos: duracaoMinutos });
      toast({ title: "Sala reservada!", description: `Reservada por ${duracaoMinutos} minutos a partir de agora.` });
      await carregarLivres();
      aoReservar();
    } catch {
      toast({
        variant: "destructive",
        title: "Não foi possível reservar",
        description: "Esse ambiente pode ter acabado de ser ocupado. Tente outro.",
      });
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2">
        <Zap className="h-4 w-4 text-primary" />
        <CardTitle className="text-base">Reservar agora</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {ambientes.length === 0 ? (
          <p className="text-sm text-muted-foreground">Nenhum ambiente livre no momento.</p>
        ) : (
          <>
            <Select value={ambienteId ? String(ambienteId) : undefined} onValueChange={(v) => setAmbienteId(Number(v))}>
              <SelectTrigger>
                <SelectValue placeholder="Escolha um ambiente livre" />
              </SelectTrigger>
              <SelectContent>
                {ambientes.map((a) => (
                  <SelectItem key={a.id} value={String(a.id)}>
                    {a.nome} — {a.localizacao || "sem localização"}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="flex flex-wrap gap-2">
              {DURACOES.map((d) => (
                <Button key={d.minutos} size="sm" variant="outline" disabled={enviando || !ambienteId} onClick={() => reservar(d.minutos)}>
                  {d.rotulo}
                </Button>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
