"use client";
import { useEffect, useState, useCallback } from "react";
import { CalendarToolbar, type VisaoCalendario } from "@/components/calendar/toolbar";
import { MonthView } from "@/components/calendar/month-view";
import { WeekView } from "@/components/calendar/week-view";
import { DayView } from "@/components/calendar/day-view";
import { AgendaView } from "@/components/calendar/agenda-view";
import { ReservationFormDialog } from "@/components/reservations/reservation-form-dialog";
import { ReservationDetailsDialog } from "@/components/reservations/reservation-details-dialog";
import { api } from "@/lib/api";
import type { Reserva } from "@/types";
import {
  addMonths, addWeeks, addDays, startOfMonth, endOfMonth, startOfWeek, endOfWeek, startOfDay, endOfDay,
} from "date-fns";

export default function CalendarioPage() {
  const [dataAtual, setDataAtual] = useState(new Date());
  const [visao, setVisao] = useState<VisaoCalendario>("mes");
  const [reservas, setReservas] = useState<Reserva[]>([]);
  const [dialogAberto, setDialogAberto] = useState(false);
  const [slotSelecionado, setSlotSelecionado] = useState<Date | undefined>();
  const [reservaSelecionada, setReservaSelecionada] = useState<Reserva | null>(null);

  const carregarReservas = useCallback(async () => {
    // Sempre normaliza para início/fim do dia: dataAtual pode conter a hora exata do
    // momento em que a página foi aberta (new Date(), botão "Hoje"), e sem isso a janela
    // filtrada começava "agora" em vez de meia-noite — escondendo reservas mais cedo no
    // mesmo dia (ex.: abrir a agenda às 15h ocultava tudo que já tinha acontecido antes).
    let dataDe: Date, dataAte: Date;
    if (visao === "mes") {
      dataDe = startOfWeek(startOfMonth(dataAtual), { weekStartsOn: 1 });
      dataAte = endOfWeek(endOfMonth(dataAtual), { weekStartsOn: 1 });
    } else if (visao === "semana") {
      dataDe = startOfWeek(dataAtual, { weekStartsOn: 1 });
      dataAte = endOfWeek(dataAtual, { weekStartsOn: 1 });
    } else if (visao === "agenda") {
      dataDe = startOfDay(dataAtual);
      dataAte = endOfDay(addMonths(dataAtual, 1));
    } else {
      dataDe = startOfDay(dataAtual);
      dataAte = endOfDay(dataAtual);
    }
    const { data } = await api.get("/reservations/", {
      params: { data_de: dataDe.toISOString(), data_ate: dataAte.toISOString(), page_size: 300, ordering: "data_inicio" },
    });
    setReservas(data.results);
  }, [dataAtual, visao]);

  useEffect(() => {
    carregarReservas();
  }, [carregarReservas]);

  function navegar(direcao: -1 | 1) {
    if (visao === "mes") setDataAtual((d) => addMonths(d, direcao));
    else if (visao === "semana") setDataAtual((d) => addWeeks(d, direcao));
    else setDataAtual((d) => addDays(d, direcao));
  }

  function abrirNovaReserva(slot?: Date) {
    setSlotSelecionado(slot);
    setDialogAberto(true);
  }

  return (
    <div>
      <CalendarToolbar
        dataAtual={dataAtual}
        visao={visao}
        aoMudarVisao={setVisao}
        aoNavegar={navegar}
        aoHoje={() => setDataAtual(new Date())}
        aoNovaReserva={() => abrirNovaReserva(undefined)}
      />

      {visao === "mes" && (
        <MonthView
          dataAtual={dataAtual}
          reservas={reservas}
          aoClicarDia={(dia) => {
            setDataAtual(dia);
            setVisao("dia");
          }}
          aoClicarReserva={setReservaSelecionada}
        />
      )}
      {visao === "semana" && (
        <WeekView
          dataAtual={dataAtual}
          reservas={reservas}
          aoClicarReserva={setReservaSelecionada}
          aoClicarSlot={abrirNovaReserva}
        />
      )}
      {visao === "dia" && (
        <DayView
          dataAtual={dataAtual}
          reservas={reservas}
          aoClicarReserva={setReservaSelecionada}
          aoClicarSlot={abrirNovaReserva}
        />
      )}
      {visao === "agenda" && <AgendaView reservas={reservas} aoClicarReserva={setReservaSelecionada} />}

      <ReservationFormDialog
        aberto={dialogAberto}
        aoFechar={() => setDialogAberto(false)}
        aoCriar={carregarReservas}
        inicioPadrao={slotSelecionado?.toISOString()}
        fimPadrao={slotSelecionado ? new Date(slotSelecionado.getTime() + 60 * 60 * 1000).toISOString() : undefined}
      />

      <ReservationDetailsDialog
        reserva={reservaSelecionada}
        aberto={!!reservaSelecionada}
        aoFechar={() => setReservaSelecionada(null)}
        aoAtualizar={carregarReservas}
      />
    </div>
  );
}
