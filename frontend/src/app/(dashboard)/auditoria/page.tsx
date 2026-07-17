"use client";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { LogAuditoria } from "@/types";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";

export default function AuditoriaPage() {
  const [logs, setLogs] = useState<LogAuditoria[]>([]);

  useEffect(() => {
    api.get("/audit-logs/", { params: { page_size: 100 } }).then((res) => setLogs(res.data.results));
  }, []);

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">{logs.length} evento(s) de auditoria registrados</p>
      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50 text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="p-3">Data/Hora</th>
                <th className="p-3">Usuário</th>
                <th className="p-3">Ação</th>
                <th className="p-3">Entidade</th>
                <th className="p-3">Descrição</th>
                <th className="p-3">IP</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-b last:border-0">
                  <td className="p-3">{format(new Date(log.criado_em), "dd/MM/yyyy HH:mm:ss", { locale: ptBR })}</td>
                  <td className="p-3">{log.usuario_nome || "—"}</td>
                  <td className="p-3"><Badge variant="secondary">{log.acao}</Badge></td>
                  <td className="p-3">{log.entidade}{log.entidade_id ? ` #${log.entidade_id}` : ""}</td>
                  <td className="p-3">{log.descricao}</td>
                  <td className="p-3 text-xs text-muted-foreground">{log.endereco_ip}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr><td colSpan={6} className="p-6 text-center text-muted-foreground">Nenhum evento registrado ainda.</td></tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
