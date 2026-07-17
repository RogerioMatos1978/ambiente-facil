"use client";
import React from "react";
import { cn } from "@/lib/utils";
import type { Reserva } from "@/types";
import { startOfWeek, addDays, isSameDay, isToday, format } from "date-fns";
import { ptBR } from "date-fns/locale";

const HORAS = Array.from({ length: 14 }, (_, i) => i + 7); // 07h às 20h

export function WeekView({
  dataAtual, reservas, aoClicarReserva, aoClicarSlot,
}: {
  dataAtual: Date;
  reservas: Reserva[];
  aoClicarReserva: (reserva: Reserva) => void;
  aoClicarSlot: (inicio: Date) => void;
}) {
  const inicioSemana = startOfWeek(dataAtual, { weekStartsOn: 1 });
  const dias = Array.from({ length: 7 }, (_, i) => addDays(inicioSemana, i));

  function reservasDoDiaHora(dia: Date, hora: number) {
    return reservas.filter((r) => {
      const inicio = new Date(r.data_inicio);
      return isSameDay(inicio, dia) && inicio.getHours() === hora && r.status !== "cancelada";
    });
  }

  return (
    <div className="overflow-x-auto rounded-lg border">
      <div className="grid min-w-[700px]" style={{ gridTemplateColumns: "64px repeat(7, 1fr)" }}>
        <div className="border-b border-r bg-muted/50" />
        {dias.map((dia) => (
          <div key={dia.toISOString()} className="border-b border-r bg-muted/50 p-2 text-center text-xs font-medium">
            <div className="text-muted-foreground">{format(dia, "EEE", { locale: ptBR })}</div>
            <div className={cn("mx-auto flex h-6 w-6 items-center justify-center rounded-full", isToday(dia) && "bg-primary text-primary-foreground")}>
              {format(dia, "d")}
            </div>
          </div>
        ))}

        {HORAS.map((hora) => (
          <React.Fragment key={hora}>
            <div key={`h-${hora}`} className="border-r border-b p-1 text-right text-[11px] text-muted-foreground">
              {String(hora).padStart(2, "0")}:00
            </div>
            {dias.map((dia) => {
              const itens = reservasDoDiaHora(dia, hora);
              const slot = new Date(dia);
              slot.setHours(hora, 0, 0, 0);
              return (
                <div
                  key={`${dia.toISOString()}-${hora}`}
                  onClick={() => itens.length === 0 && aoClicarSlot(slot)}
                  className="min-h-[3rem] cursor-pointer border-r border-b p-1 hover:bg-accent/40"
                >
                  {itens.map((r) => (
                    <button
                      key={r.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        aoClicarReserva(r);
                      }}
                      className="w-full truncate rounded bg-primary/15 px-1 py-0.5 text-left text-[11px] text-primary hover:bg-primary/25"
                    >
                      {r.titulo}
                    </button>
                  ))}
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}
