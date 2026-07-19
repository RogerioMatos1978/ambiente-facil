"use client";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ReservationDetailsDialog } from "@/components/reservations/reservation-details-dialog";
import { ReservationFormDialog } from "@/components/reservations/reservation-form-dialog";
import { api, API_BASE_URL } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import type { Reserva } from "@/types";
import { FileSpreadsheet, FileText, FileDown, Plus } from "lucide-react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "livre" | "outline"> = {
  confirmada: "livre",
  pendente: "secondary",
  cancelada: "destructive",
  concluida: "default",
  expirada: "outline",
};

export default function ReservasPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [reservas, setReservas] = useState<Reserva[]>([]);
  const [selecionada, setSelecionada] = useState<Reserva | null>(null);
  const [novaAberta, setNovaAberta] = useState(false);

  async function carregar() {
    const { data } = await api.get("/reservations/", { params: { page_size: 200, ordering: "-data_inicio" } });
    setReservas(data.results);
  }

  useEffect(() => {
    carregar();
  }, []);

  async function exportar(formato: "csv" | "xlsx" | "pdf") {
    const resposta = await fetch(`${API_BASE_URL}/api/v1/reservations/exportar/${formato}/`, {
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
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50 text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="p-3">Título</th>
                <th className="p-3">Ambiente</th>
                <th className="p-3">Solicitante</th>
                <th className="p-3">Início</th>
                <th className="p-3">Fim</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {reservas.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => setSelecionada(r)}
                  className="cursor-pointer border-b last:border-0 hover:bg-accent/40"
                >
                  <td className="p-3 font-medium">{r.titulo}</td>
                  <td className="p-3">{r.ambiente_detalhe?.nome}</td>
                  <td className="p-3">{r.solicitante_nome}</td>
                  <td className="p-3">{format(new Date(r.data_inicio), "dd/MM/yyyy HH:mm", { locale: ptBR })}</td>
                  <td className="p-3">{format(new Date(r.data_fim), "dd/MM/yyyy HH:mm", { locale: ptBR })}</td>
                  <td className="p-3">
                    <Badge variant={statusVariant[r.status] ?? "default"}>{r.status_display}</Badge>
                  </td>
                </tr>
              ))}
              {reservas.length === 0 && (
                <tr><td colSpan={6} className="p-6 text-center text-muted-foreground">Nenhuma reserva encontrada.</td></tr>
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
