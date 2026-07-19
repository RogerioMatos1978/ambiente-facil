"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { usePainelTempoReal } from "@/hooks/use-painel-tempo-real";
import { ReservationFormDialog } from "@/components/reservations/reservation-form-dialog";
import type { Ambiente } from "@/types";
import { Wifi, WifiOff } from "lucide-react";

export function PainelAmbientes() {
  const [ambientes, setAmbientes] = useState<Ambiente[]>([]);
  const [ambienteParaReservar, setAmbienteParaReservar] = useState<Ambiente | null>(null);
  const { ultimoEvento, conectado } = usePainelTempoReal();

  function carregar() {
    api.get("/environments/", { params: { page_size: 50 } }).then((res) => setAmbientes(res.data.results));
  }

  useEffect(() => {
    carregar();
  }, []);

  // Quando um evento em tempo real chega, refaz a consulta do ambiente afetado
  // (mantém o painel sincronizado sem precisar recarregar a página).
  useEffect(() => {
    if (!ultimoEvento?.ambiente_id) return;
    api.get(`/environments/${ultimoEvento.ambiente_id}/`).then((res) => {
      setAmbientes((prev) => prev.map((a) => (a.id === res.data.id ? res.data : a)));
    });
  }, [ultimoEvento]);

  function aoClicarCard(ambiente: Ambiente) {
    if (ambiente.status_atual !== "livre") return;
    setAmbienteParaReservar(ambiente);
  }

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Painel em tempo real</CardTitle>
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            {conectado ? <Wifi className="h-4 w-4 text-livre-foreground" /> : <WifiOff className="h-4 w-4" />}
            {conectado ? "Ao vivo" : "Desconectado"}
          </span>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {ambientes.map((ambiente) => {
            const livre = ambiente.status_atual === "livre";
            return (
              <button
                key={ambiente.id}
                type="button"
                onClick={() => aoClicarCard(ambiente)}
                disabled={!livre}
                title={livre ? "Clique para reservar este ambiente" : "Ambiente ocupado no momento"}
                className={`flex items-center justify-between rounded-md border p-3 text-left transition-colors ${
                  livre ? "cursor-pointer hover:border-primary hover:bg-accent/40" : "cursor-not-allowed opacity-90"
                }`}
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{ambiente.nome}</p>
                  <p className="truncate text-xs text-muted-foreground">{ambiente.localizacao}</p>
                </div>
                <Badge variant={livre ? "livre" : "ocupado"}>{livre ? "Livre" : "Ocupado"}</Badge>
              </button>
            );
          })}
          {ambientes.length === 0 && <p className="text-sm text-muted-foreground">Nenhum ambiente cadastrado.</p>}
        </CardContent>
      </Card>

      <ReservationFormDialog
        aberto={ambienteParaReservar !== null}
        aoFechar={() => setAmbienteParaReservar(null)}
        aoCriar={() => {
          carregar();
          setAmbienteParaReservar(null);
        }}
        ambienteIdPadrao={ambienteParaReservar?.id}
      />
    </>
  );
}
