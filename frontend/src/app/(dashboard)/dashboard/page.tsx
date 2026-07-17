"use client";
import { useEffect, useMemo, useState } from "react";
import { Building2, CalendarCheck2, ClipboardList, Percent } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { PainelAmbientes } from "@/components/dashboard/painel-ambientes";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { Ambiente, Reserva } from "@/types";
import { format, isToday, startOfWeek, addDays } from "date-fns";
import { ptBR } from "date-fns/locale";

export default function DashboardPage() {
  const [ambientes, setAmbientes] = useState<Ambiente[]>([]);
  const [reservas, setReservas] = useState<Reserva[]>([]);

  useEffect(() => {
    api.get("/environments/", { params: { page_size: 100 } }).then((res) => setAmbientes(res.data.results));
    api.get("/reservations/", { params: { page_size: 200, ordering: "-data_inicio" } }).then((res) =>
      setReservas(res.data.results)
    );
  }, []);

  const reservasHoje = useMemo(() => reservas.filter((r) => isToday(new Date(r.data_inicio))), [reservas]);
  const ambientesOcupadosAgora = ambientes.filter((a) => a.status_atual === "ocupado").length;
  const taxaOcupacao = ambientes.length ? Math.round((ambientesOcupadosAgora / ambientes.length) * 100) : 0;

  const dadosSemana = useMemo(() => {
    const inicioSemana = startOfWeek(new Date(), { weekStartsOn: 1 });
    return Array.from({ length: 7 }).map((_, i) => {
      const dia = addDays(inicioSemana, i);
      const total = reservas.filter(
        (r) => new Date(r.data_inicio).toDateString() === dia.toDateString() && r.status !== "cancelada"
      ).length;
      return { dia: format(dia, "EEE", { locale: ptBR }), total };
    });
  }, [reservas]);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard titulo="Ambientes cadastrados" valor={ambientes.length} icone={Building2} />
        <KpiCard titulo="Reservas hoje" valor={reservasHoje.length} icone={CalendarCheck2} corIcone="text-livre-foreground" />
        <KpiCard titulo="Total de reservas" valor={reservas.length} icone={ClipboardList} />
        <KpiCard titulo="Taxa de ocupação agora" valor={`${taxaOcupacao}%`} icone={Percent} corIcone="text-ocupado-foreground" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Reservas na semana</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dadosSemana}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="dia" tickLine={false} axisLine={false} fontSize={12} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={12} />
                <Tooltip cursor={{ fill: "hsl(var(--accent))" }} />
                <Bar dataKey="total" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <PainelAmbientes />
      </div>
    </div>
  );
}
