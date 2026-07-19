"use client";
import type { Reserva } from "@/types";
import { Badge } from "@/components/ui/badge";
import { format, compareAsc } from "date-fns";
import { ptBR } from "date-fns/locale";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "livre" | "outline"> = {
  confirmada: "livre",
  pendente: "secondary",
  cancelada: "destructive",
  concluida: "default",
  expirada: "outline",
};

export function AgendaView({ reservas, aoClicarReserva }: { reservas: Reserva[]; aoClicarReserva: (r: Reserva) => void }) {
  const ordenadas = [...reservas].sort((a, b) => compareAsc(new Date(a.data_inicio), new Date(b.data_inicio)));

  if (ordenadas.length === 0) {
    return <p className="rounded-lg border p-6 text-center text-sm text-muted-foreground">Nenhuma reserva no período selecionado.</p>;
  }

  return (
    <div className="divide-y rounded-lg border">
      {ordenadas.map((r) => (
        <button
          key={r.id}
          onClick={() => aoClicarReserva(r)}
          className="flex w-full flex-wrap items-center justify-between gap-2 p-4 text-left hover:bg-accent/40 sm:flex-nowrap sm:gap-4"
        >
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{r.titulo}</p>
            <p className="truncate text-xs text-muted-foreground">
              {format(new Date(r.data_inicio), "EEEE, dd/MM/yyyy HH:mm", { locale: ptBR })} · {r.ambiente_detalhe?.nome} ·{" "}
              {r.duracao_display}
            </p>
          </div>
          <Badge variant={statusVariant[r.status] ?? "default"}>{r.status_display}</Badge>
        </button>
      ))}
    </div>
  );
}
