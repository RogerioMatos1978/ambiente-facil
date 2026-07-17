"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { usePainelTempoReal } from "@/hooks/use-painel-tempo-real";
import type { Ambiente } from "@/types";
import { Wifi, WifiOff } from "lucide-react";

export function PainelAmbientes() {
  const [ambientes, setAmbientes] = useState<Ambiente[]>([]);
  const { ultimoEvento, conectado } = usePainelTempoReal();

  useEffect(() => {
    api.get("/environments/", { params: { page_size: 50 } }).then((res) => setAmbientes(res.data.results));
  }, []);

  // Quando um evento em tempo real chega, refaz a consulta do ambiente afetado
  // (mantém o painel sincronizado sem precisar recarregar a página).
  useEffect(() => {
    if (!ultimoEvento?.ambiente_id) return;
    api.get(`/environments/${ultimoEvento.ambiente_id}/`).then((res) => {
      setAmbientes((prev) => prev.map((a) => (a.id === res.data.id ? res.data : a)));
    });
  }, [ultimoEvento]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Painel em tempo real</CardTitle>
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          {conectado ? <Wifi className="h-4 w-4 text-livre-foreground" /> : <WifiOff className="h-4 w-4" />}
          {conectado ? "Ao vivo" : "Desconectado"}
        </span>
      </CardHeader>
      <CardContent className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {ambientes.map((ambiente) => (
          <div key={ambiente.id} className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="text-sm font-medium">{ambiente.nome}</p>
              <p className="text-xs text-muted-foreground">{ambiente.localizacao}</p>
            </div>
            <Badge variant={ambiente.status_atual === "livre" ? "livre" : "ocupado"}>
              {ambiente.status_atual === "livre" ? "Livre" : "Ocupado"}
            </Badge>
          </div>
        ))}
        {ambientes.length === 0 && <p className="text-sm text-muted-foreground">Nenhum ambiente cadastrado.</p>}
      </CardContent>
    </Card>
  );
}
