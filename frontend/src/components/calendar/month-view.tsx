"use client";
import { cn } from "@/lib/utils";
import type { Reserva } from "@/types";
import {
  startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval,
  isSameMonth, isSameDay, isToday, format,
} from "date-fns";

const diasSemana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

export function MonthView({
  dataAtual, reservas, aoClicarDia, aoClicarReserva,
}: {
  dataAtual: Date;
  reservas: Reserva[];
  aoClicarDia: (dia: Date) => void;
  aoClicarReserva: (reserva: Reserva) => void;
}) {
  const inicio = startOfWeek(startOfMonth(dataAtual), { weekStartsOn: 1 });
  const fim = endOfWeek(endOfMonth(dataAtual), { weekStartsOn: 1 });
  const dias = eachDayOfInterval({ start: inicio, end: fim });

  return (
    <div className="overflow-hidden rounded-lg border">
      <div className="grid grid-cols-7 border-b bg-muted/50 text-center text-xs font-medium text-muted-foreground">
        {diasSemana.map((d) => (
          <div key={d} className="py-2">{d}</div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {dias.map((dia) => {
          const reservasDoDia = reservas.filter(
            (r) => isSameDay(new Date(r.data_inicio), dia) && r.status !== "cancelada"
          );
          return (
            <button
              key={dia.toISOString()}
              onClick={() => aoClicarDia(dia)}
              className={cn(
                "flex min-h-[100px] flex-col items-start gap-1 border-b border-r p-2 text-left align-top hover:bg-accent/50",
                !isSameMonth(dia, dataAtual) && "bg-muted/30 text-muted-foreground"
              )}
            >
              <span className={cn("flex h-6 w-6 items-center justify-center rounded-full text-xs", isToday(dia) && "bg-primary text-primary-foreground")}>
                {format(dia, "d")}
              </span>
              <div className="flex w-full flex-col gap-0.5">
                {reservasDoDia.slice(0, 3).map((r) => (
                  <span
                    key={r.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      aoClicarReserva(r);
                    }}
                    className="truncate rounded bg-primary/10 px-1 py-0.5 text-[11px] text-primary hover:bg-primary/20"
                    title={r.titulo}
                  >
                    {format(new Date(r.data_inicio), "HH:mm")} {r.titulo}
                  </span>
                ))}
                {reservasDoDia.length > 3 && (
                  <span className="text-[11px] text-muted-foreground">+{reservasDoDia.length - 3} mais</span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
