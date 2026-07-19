"use client";
import { useEffect, useMemo, useState } from "react";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import {
  CalendarCheck2, ClipboardList, TimerOff, Timer, FileDown, FileSpreadsheet, FileText,
} from "lucide-react";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api, API_BASE_URL } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import type { Ambiente, RelatorioReservas, StatusReserva } from "@/types";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";

const STATUS_OPCOES: { value: StatusReserva; label: string }[] = [
  { value: "pendente", label: "Pendente" },
  { value: "confirmada", label: "Confirmada" },
  { value: "cancelada", label: "Cancelada" },
  { value: "concluida", label: "Concluída" },
  { value: "expirada", label: "Expirada (no-show)" },
];

interface Filtros {
  data_de: string;
  data_ate: string;
  ambiente: string;
  status: string;
}

function filtrosParaParams(filtros: Filtros) {
  const params: Record<string, string> = {};
  if (filtros.data_de) params.data_de = filtros.data_de;
  if (filtros.data_ate) params.data_ate = filtros.data_ate;
  if (filtros.ambiente) params.ambiente = filtros.ambiente;
  if (filtros.status) params.status = filtros.status;
  return params;
}

export default function RelatoriosPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [ambientes, setAmbientes] = useState<Ambiente[]>([]);
  const [dados, setDados] = useState<RelatorioReservas | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [filtros, setFiltros] = useState<Filtros>({ data_de: "", data_ate: "", ambiente: "", status: "" });

  useEffect(() => {
    api.get("/environments/", { params: { page_size: 100 } }).then((res) => setAmbientes(res.data.results));
  }, []);

  async function carregar() {
    setCarregando(true);
    try {
      const { data } = await api.get<RelatorioReservas>("/reservations/relatorio/", {
        params: filtrosParaParams(filtros),
      });
      setDados(data);
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtros]);

  async function exportar(formato: "csv" | "xlsx" | "pdf") {
    const params = new URLSearchParams(filtrosParaParams(filtros));
    const resposta = await fetch(`${API_BASE_URL}/api/v1/reservations/exportar/${formato}/?${params.toString()}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const blob = await resposta.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `relatorio-reservas.${formato}`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  const dadosPorDia = useMemo(
    () =>
      (dados?.por_dia ?? []).map((item) => ({
        dia: format(new Date(`${item.dia}T00:00:00`), "dd/MM", { locale: ptBR }),
        total: item.total,
      })),
    [dados]
  );

  const resumo = dados?.resumo;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold">Relatórios de reservas</h1>
        <p className="text-sm text-muted-foreground">Visão consolidada de uso dos ambientes, com filtros e exportação.</p>
      </div>

      <Card>
        <CardContent className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 lg:grid-cols-5">
          <div className="space-y-1">
            <Label>De</Label>
            <Input
              type="date"
              value={filtros.data_de}
              onChange={(e) => setFiltros((f) => ({ ...f, data_de: e.target.value }))}
            />
          </div>
          <div className="space-y-1">
            <Label>Até</Label>
            <Input
              type="date"
              value={filtros.data_ate}
              onChange={(e) => setFiltros((f) => ({ ...f, data_ate: e.target.value }))}
            />
          </div>
          <div className="space-y-1">
            <Label>Ambiente</Label>
            <Select
              value={filtros.ambiente || "todos"}
              onValueChange={(v) => setFiltros((f) => ({ ...f, ambiente: v === "todos" ? "" : v }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Todos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos</SelectItem>
                {ambientes.map((a) => (
                  <SelectItem key={a.id} value={String(a.id)}>
                    {a.nome}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label>Status</Label>
            <Select
              value={filtros.status || "todos"}
              onValueChange={(v) => setFiltros((f) => ({ ...f, status: v === "todos" ? "" : v }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Todos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos</SelectItem>
                {STATUS_OPCOES.map((s) => (
                  <SelectItem key={s.value} value={s.value}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-end gap-2">
            <Button variant="outline" size="sm" className="w-full" onClick={() => exportar("csv")}>
              <FileDown className="mr-2 h-4 w-4" /> CSV
            </Button>
            <Button variant="outline" size="sm" className="w-full" onClick={() => exportar("xlsx")}>
              <FileSpreadsheet className="mr-2 h-4 w-4" /> Excel
            </Button>
            <Button variant="outline" size="sm" className="w-full" onClick={() => exportar("pdf")}>
              <FileText className="mr-2 h-4 w-4" /> PDF
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard titulo="Total de reservas" valor={resumo?.total ?? 0} icone={ClipboardList} />
        <KpiCard
          titulo="Confirmadas"
          valor={resumo?.confirmadas ?? 0}
          icone={CalendarCheck2}
          corIcone="text-livre-foreground"
        />
        <KpiCard
          titulo="Taxa de no-show"
          valor={`${resumo?.taxa_no_show ?? 0}%`}
          icone={TimerOff}
          corIcone="text-ocupado-foreground"
        />
        <KpiCard titulo="Duração média" valor={`${resumo?.duracao_media_minutos ?? 0} min`} icone={Timer} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Reservas por dia</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dadosPorDia}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="dia" tickLine={false} axisLine={false} fontSize={11} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={11} width={24} />
                <Tooltip cursor={{ stroke: "hsl(var(--accent))" }} />
                <Line type="monotone" dataKey="total" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
            {dadosPorDia.length === 0 && !carregando && (
              <p className="pt-8 text-center text-sm text-muted-foreground">Nenhum dado no período.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Reservas por status</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dados?.por_status ?? []}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="status_display" tickLine={false} axisLine={false} fontSize={11} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={11} width={24} />
                <Tooltip cursor={{ fill: "hsl(var(--accent))" }} />
                <Bar dataKey="total" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Ambientes mais reservados</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="p-3">Ambiente</th>
                  <th className="p-3 text-right">Reservas</th>
                </tr>
              </thead>
              <tbody>
                {(dados?.por_ambiente ?? []).map((item) => (
                  <tr key={item.ambiente_id} className="border-b last:border-0">
                    <td className="p-3">{item.ambiente_nome}</td>
                    <td className="p-3 text-right font-medium">{item.total}</td>
                  </tr>
                ))}
                {(dados?.por_ambiente ?? []).length === 0 && (
                  <tr>
                    <td colSpan={2} className="p-6 text-center text-muted-foreground">
                      Nenhum dado no período.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </CardContent>
        </Card>

        {dados && dados.por_solicitante.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Quem mais reservou</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="p-3">Solicitante</th>
                    <th className="p-3 text-right">Reservas</th>
                  </tr>
                </thead>
                <tbody>
                  {dados.por_solicitante.map((item) => (
                    <tr key={item.solicitante_id} className="border-b last:border-0">
                      <td className="p-3">{item.solicitante_nome}</td>
                      <td className="p-3 text-right font-medium">{item.total}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
