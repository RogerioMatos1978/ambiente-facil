"use client";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ReservationDetailsDialog } from "@/components/reservations/reservation-details-dialog";
import { ReservationFormDialog } from "@/components/reservations/reservation-form-dialog";
import { api, API_BASE_URL } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { usePainelTempoReal } from "@/hooks/use-painel-tempo-real";
import { cn } from "@/lib/utils";
import type { Ambiente, Reserva, StatusReserva } from "@/types";
import { FileSpreadsheet, FileText, FileDown, Plus, Search, X } from "lucide-react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "livre" | "outline"> = {
  confirmada: "livre",
  pendente: "secondary",
  cancelada: "destructive",
  concluida: "default",
  expirada: "outline",
};

const chaveVariant: Record<string, "livre" | "ocupado" | "secondary" | "outline"> = {
  disponivel: "livre",
  ocupada: "ocupado",
  devolvida: "secondary",
};

const STATUS_OPCOES: { value: StatusReserva; label: string }[] = [
  { value: "pendente", label: "Pendente" },
  { value: "confirmada", label: "Confirmada" },
  { value: "cancelada", label: "Cancelada" },
  { value: "concluida", label: "Concluída" },
  { value: "expirada", label: "Expirada (no-show)" },
];

interface Filtros {
  busca: string;
  ambiente: string;
  status: string;
  data_de: string;
  data_ate: string;
}

// A lista abre já filtrada por Confirmada (o que costuma interessar no dia a dia);
// "Todos os status" limpa esse filtro.
const FILTROS_PADRAO: Filtros = { busca: "", ambiente: "", status: "confirmada", data_de: "", data_ate: "" };

function filtrosParaParams(filtros: Filtros) {
  const params: Record<string, string> = { ordering: "-id" };
  if (filtros.busca) params.search = filtros.busca;
  if (filtros.ambiente) params.ambiente = filtros.ambiente;
  if (filtros.status) params.status = filtros.status;
  if (filtros.data_de) params.data_de = filtros.data_de;
  if (filtros.data_ate) params.data_ate = filtros.data_ate;
  return params;
}

export default function ReservasPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const { ultimoEvento } = usePainelTempoReal();
  const [reservas, setReservas] = useState<Reserva[]>([]);
  const [ambientes, setAmbientes] = useState<Ambiente[]>([]);
  const [selecionada, setSelecionada] = useState<Reserva | null>(null);
  const [novaAberta, setNovaAberta] = useState(false);
  const [filtros, setFiltros] = useState<Filtros>(FILTROS_PADRAO);

  async function carregar() {
    const { data } = await api.get("/reservations/", {
      params: { page_size: 200, ...filtrosParaParams(filtros) },
    });
    setReservas(data.results);
  }

  useEffect(() => {
    api.get("/environments/", { params: { page_size: 100, ativo: true } }).then((res) => setAmbientes(res.data.results));
  }, []);

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtros]);

  // Recarrega a lista ao chegar um alerta de chave atrasada, para a linha correspondente
  // já aparecer em amarelo sem precisar de F5 (ver Reserva.chave_atrasada e o comando
  // apps/keys/management/commands/alertar_chaves_atrasadas.py no backend).
  useEffect(() => {
    if (ultimoEvento?.tipo === "chave_atrasada") {
      carregar();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ultimoEvento]);

  async function exportar(formato: "csv" | "xlsx" | "pdf") {
    const params = new URLSearchParams(filtrosParaParams(filtros));
    const resposta = await fetch(`${API_BASE_URL}/api/v1/reservations/exportar/${formato}/?${params.toString()}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const blob = await resposta.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reservas.${formato}`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  const filtrosAlterados = JSON.stringify(filtros) !== JSON.stringify(FILTROS_PADRAO);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">{reservas.length} reserva(s)</p>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={() => exportar("csv")}>
            <FileDown className="mr-2 h-4 w-4" /> CSV
          </Button>
          <Button variant="outline" size="sm" onClick={() => exportar("xlsx")}>
            <FileSpreadsheet className="mr-2 h-4 w-4" /> Excel
          </Button>
          <Button variant="outline" size="sm" onClick={() => exportar("pdf")}>
            <FileText className="mr-2 h-4 w-4" /> PDF
          </Button>
          <Button size="sm" onClick={() => setNovaAberta(true)}>
            <Plus className="mr-2 h-4 w-4" /> Nova reserva
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 lg:grid-cols-5">
          <div className="space-y-1 lg:col-span-2">
            <Label className="text-xs">Buscar</Label>
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-8"
                placeholder="Título, descrição ou ambiente..."
                value={filtros.busca}
                onChange={(e) => setFiltros((f) => ({ ...f, busca: e.target.value }))}
              />
            </div>
          </div>
          <div className="space-y-1">
            <Label className="text-xs">Ambiente</Label>
            <Select
              value={filtros.ambiente || "todos"}
              onValueChange={(v) => setFiltros((f) => ({ ...f, ambiente: v === "todos" ? "" : v }))}
            >
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos os ambientes</SelectItem>
                {ambientes.map((a) => (
                  <SelectItem key={a.id} value={String(a.id)}>{a.nome}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label className="text-xs">Status</Label>
            <Select
              value={filtros.status || "todos"}
              onValueChange={(v) => setFiltros((f) => ({ ...f, status: v === "todos" ? "" : v }))}
            >
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos os status</SelectItem>
                {STATUS_OPCOES.map((s) => (
                  <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <Label className="text-xs">De</Label>
              <Input type="date" value={filtros.data_de} onChange={(e) => setFiltros((f) => ({ ...f, data_de: e.target.value }))} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Até</Label>
              <Input type="date" value={filtros.data_ate} onChange={(e) => setFiltros((f) => ({ ...f, data_ate: e.target.value }))} />
            </div>
          </div>
          {filtrosAlterados && (
            <div className="lg:col-span-5">
              <Button variant="ghost" size="sm" onClick={() => setFiltros(FILTROS_PADRAO)}>
                <X className="mr-2 h-4 w-4" /> Limpar filtros
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50 text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="hidden p-3 lg:table-cell">Nº Controle</th>
                <th className="p-3">Título</th>
                <th className="hidden p-3 md:table-cell">Ambiente</th>
                <th className="hidden p-3 lg:table-cell">Chave</th>
                <th className="hidden p-3 md:table-cell">Solicitante</th>
                <th className="p-3">Início</th>
                <th className="hidden p-3 sm:table-cell">Fim</th>
                <th className="hidden p-3 sm:table-cell">Duração</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {reservas.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => setSelecionada(r)}
                  className={cn(
                    "cursor-pointer border-b last:border-0 hover:bg-accent/40",
                    // Alerta visual: chave retirada e não devolvida até 10 min após o fim da
                    // reserva (ver Reserva.chave_atrasada no backend, recalculado a cada consulta).
                    r.chave_atrasada && "bg-yellow-100 hover:bg-yellow-200/80 dark:bg-yellow-900/40 dark:hover:bg-yellow-900/60"
                  )}
                >
                  <td className="hidden p-3 text-xs text-muted-foreground lg:table-cell">{r.numero_controle}</td>
                  <td className="p-3 font-medium">{r.titulo}</td>
                  <td className="hidden p-3 md:table-cell">{r.ambiente_detalhe?.nome}</td>
                  <td className="hidden p-3 lg:table-cell">
                    {r.chave_status ? (
                      <div className="flex items-center gap-1">
                        <Badge variant={chaveVariant[r.chave_status] ?? "outline"}>{r.chave_status_display}</Badge>
                        {r.chave_atrasada && (
                          <Badge variant="destructive" title="Chave não devolvida há mais de 10 min do fim da reserva">
                            Atrasada
                          </Badge>
                        )}
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="hidden p-3 md:table-cell">{r.solicitante_nome}</td>
                  <td className="whitespace-nowrap p-3">{format(new Date(r.data_inicio), "dd/MM/yyyy HH:mm", { locale: ptBR })}</td>
                  <td className="hidden whitespace-nowrap p-3 sm:table-cell">{format(new Date(r.data_fim), "dd/MM/yyyy HH:mm", { locale: ptBR })}</td>
                  <td className="hidden whitespace-nowrap p-3 sm:table-cell">{r.duracao_display}</td>
                  <td className="p-3">
                    <Badge variant={statusVariant[r.status] ?? "default"}>{r.status_display}</Badge>
                  </td>
                </tr>
              ))}
              {reservas.length === 0 && (
                <tr><td colSpan={9} className="p-6 text-center text-muted-foreground">Nenhuma reserva encontrada.</td></tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <ReservationDetailsDialog
        reserva={selecionada}
        aberto={!!selecionada}
        aoFechar={() => setSelecionada(null)}
        aoAtualizar={carregar}
      />
      <ReservationFormDialog aberto={novaAberta} aoFechar={() => setNovaAberta(false)} aoCriar={carregar} />
    </div>
  );
}
