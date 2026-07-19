"use client";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChevronLeft, ChevronRight, Plus } from "lucide-react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";

export type VisaoCalendario = "mes" | "semana" | "dia" | "agenda";

export function CalendarToolbar({
  dataAtual, visao, aoMudarVisao, aoNavegar, aoHoje, aoNovaReserva,
}: {
  dataAtual: Date;
  visao: VisaoCalendario;
  aoMudarVisao: (v: VisaoCalendario) => void;
  aoNavegar: (direcao: -1 | 1) => void;
  aoHoje: () => void;
  aoNovaReserva: () => void;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-2">
        <Button variant="outline" size="icon" onClick={() => aoNavegar(-1)}>
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button variant="outline" size="sm" onClick={aoHoje}>Hoje</Button>
        <Button variant="outline" size="icon" onClick={() => aoNavegar(1)}>
          <ChevronRight className="h-4 w-4" />
        </Button>
        <h2 className="ml-2 text-lg font-semibold capitalize">
          {format(dataAtual, visao === "mes" ? "MMMM yyyy" : "dd 'de' MMMM, yyyy", { locale: ptBR })}
        </h2>
      </div>
      <div className="flex items-center gap-3">
        <Tabs value={visao} onValueChange={(v) => aoMudarVisao(v as VisaoCalendario)}>
          <TabsList>
            <TabsTrigger value="dia">Dia</TabsTrigger>
            <TabsTrigger value="semana">Semana</TabsTrigger>
            <TabsTrigger value="mes">Mês</TabsTrigger>
            <TabsTrigger value="agenda">Agenda</TabsTrigger>
          </TabsList>
        </Tabs>
        <Button onClick={aoNovaReserva}>
          <Plus className="mr-2 h-4 w-4" /> Nova reserva
        </Button>
      </div>
    </div>
  );
}
