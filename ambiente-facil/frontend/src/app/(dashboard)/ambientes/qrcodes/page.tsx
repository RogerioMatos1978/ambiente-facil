"use client";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, API_BASE_URL } from "@/lib/api";
import type { Ambiente } from "@/types";
import { Printer } from "lucide-react";

/**
 * Grade de QR codes de todos os ambientes ativos, pronta para impressão e
 * para colar na porta de cada sala. Cada QR code leva para /checkin/<id>.
 */
export default function QrCodesAmbientesPage() {
  const [ambientes, setAmbientes] = useState<Ambiente[]>([]);

  useEffect(() => {
    api.get("/environments/", { params: { page_size: 200, ativo: true } }).then((res) => setAmbientes(res.data.results));
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between print:hidden">
        <div>
          <h2 className="text-lg font-semibold">QR codes para impressão</h2>
          <p className="text-sm text-muted-foreground">
            Imprima e cole na porta de cada sala. Ao escanear, abre a página de check-in/reserva rápida do ambiente.
          </p>
        </div>
        <Button onClick={() => window.print()}>
          <Printer className="mr-2 h-4 w-4" /> Imprimir
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 print:grid-cols-2">
        {ambientes.map((a) => (
          <Card key={a.id} className="break-inside-avoid text-center">
            <CardHeader>
              <CardTitle className="text-base">{a.nome}</CardTitle>
              <p className="text-xs text-muted-foreground">{a.localizacao}</p>
            </CardHeader>
            <CardContent>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`${API_BASE_URL}/api/v1/environments/${a.id}/qrcode/`}
                alt={`QR code de check-in do ambiente ${a.nome}`}
                width={200}
                height={200}
                className="mx-auto"
              />
            </CardContent>
          </Card>
        ))}
        {ambientes.length === 0 && <p className="text-sm text-muted-foreground">Nenhum ambiente cadastrado.</p>}
      </div>
    </div>
  );
}
