"use client";
import type { Reserva } from "@/types";
import { isSameDay } from "date-fns";

const HORAS = Array.from({ length: 14 }, (_, i) => i + 7); // 07h às 20h

export function DayView({
  dataAtual, reservas, aoClicarReserva, aoClicarSlot,
}: {
  dataAtual: Date;
  reservas: Reserva[];
  aoClicarReserva: (reserva: Reserva) => void;
  aoClicarSlot: (inicio: Date) => void;
}) {
  function reservasDaHora(hora: number) {
    return reservas.filter((r) => {
      const inicio = new Date(r.data_inicio);
      return isSameDay(inicio, dataAtual) && inicio.getHours() === hora && r.status !== "cancelada";
    });
  }

  return (
    <div className="overflow-hidden rounded-lg border">
      {HORAS.map((hora) => {
        const itens = reservasDaHora(hora);
        const slot = new Date(dataAtual);
        slot.setHours(hora, 0, 0, 0);
        return (
          <div key={hora} className="grid grid-cols-[64px_1fr] border-b last:border-b-0">
            <div className="border-r p-2 text-right text-xs text-muted-foreground">
              {String(hora).padStart(2, "0")}:00
            </div>
            <div
              onClick={() => itens.length === 0 && aoClicarSlot(slot)}
              className="min-h-[3.5rem] cursor-pointer space-y-1 p-2 hover:bg-accent/40"
            >
              {itens.map((r) => (
                <button
                  key={r.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    aoClicarReserva(r);
                  }}
                  className="block w-full rounded bg-primary/15 px-2 py-1 text-left text-sm text-primary hover:bg-primary/25"
                >
                  {r.titulo} — {r.ambiente_detalhe?.nome}
                </button>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
