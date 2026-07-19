"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api, API_BASE_URL } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useToast } from "@/hooks/use-toast";
import { ReservationFormDialog } from "@/components/reservations/reservation-form-dialog";
import type { Ambiente, TipoAmbiente } from "@/types";
import { Plus, Pencil, QrCode, CalendarPlus } from "lucide-react";

const tipos: { valor: TipoAmbiente; rotulo: string }[] = [
  { valor: "sala_aula", rotulo: "Sala de Aula" },
  { valor: "auditorio", rotulo: "Auditório" },
  { valor: "laboratorio", rotulo: "Laboratório" },
  { valor: "sala_reuniao", rotulo: "Sala de Reunião" },
  { valor: "outro", rotulo: "Outro" },
];

const vazio = {
  id: 0,
  nome: "",
  tipo: "sala_aula" as TipoAmbiente,
  localizacao: "",
  capacidade: 10,
  descricao: "",
  exige_checkin: false,
  tolerancia_checkin_minutos: 15,
};

export default function AmbientesPage() {
  const isAdmin = useAuthStore((s) => s.isAdmin());
  const { toast } = useToast();
  const [ambientes, setAmbientes] = useState<Ambiente[]>([]);
  const [dialogAberto, setDialogAberto] = useState(false);
  const [form, setForm] = useState(vazio);
  const [ambienteParaReservar, setAmbienteParaReservar] = useState<Ambiente | null>(null);

  async function carregar() {
    const { data } = await api.get("/environments/", { params: { page_size: 100 } });
    setAmbientes(data.results);
  }

  useEffect(() => {
    carregar();
  }, []);

  function abrirNovo() {
    setForm(vazio);
    setDialogAberto(true);
  }

  function abrirEdicao(a: Ambiente) {
    setForm({
      id: a.id,
      nome: a.nome,
      tipo: a.tipo,
      localizacao: a.localizacao,
      capacidade: a.capacidade,
      descricao: a.descricao,
      exige_checkin: a.exige_checkin,
      tolerancia_checkin_minutos: a.tolerancia_checkin_minutos,
    });
    setDialogAberto(true);
  }

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    try {
      if (form.id) {
        await api.patch(`/environments/${form.id}/`, form);
      } else {
        await api.post("/environments/", form);
      }
      toast({ title: "Ambiente salvo com sucesso" });
      setDialogAberto(false);
      carregar();
    } catch {
      toast({ variant: "destructive", title: "Erro ao salvar ambiente" });
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{ambientes.length} ambiente(s) cadastrado(s)</p>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link href="/ambientes/qrcodes">
              <QrCode className="mr-2 h-4 w-4" /> QR codes para impressão
            </Link>
          </Button>
          {isAdmin && (
            <Button onClick={abrirNovo}>
              <Plus className="mr-2 h-4 w-4" /> Novo ambiente
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {ambientes.map((a) => {
          const livre = a.status_atual === "livre";
          return (
            <Card
              key={a.id}
              role={livre ? "button" : undefined}
              tabIndex={livre ? 0 : undefined}
              onClick={() => livre && setAmbienteParaReservar(a)}
              onKeyDown={(e) => {
                if (livre && (e.key === "Enter" || e.key === " ")) setAmbienteParaReservar(a);
              }}
              title={livre ? "Clique para reservar este ambiente" : undefined}
              className={livre ? "cursor-pointer transition-colors hover:border-primary hover:bg-accent/30" : ""}
            >
              <CardHeader className="flex flex-row items-start justify-between">
                <div className="min-w-0">
                  <CardTitle className="truncate text-base">{a.nome}</CardTitle>
                  <p className="truncate text-xs text-muted-foreground">{a.localizacao}</p>
                </div>
                <Badge variant={livre ? "livre" : "ocupado"}>{livre ? "Livre" : "Ocupado"}</Badge>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>Capacidade: {a.capacidade} pessoas</p>
                <p>Tipo: {tipos.find((t) => t.valor === a.tipo)?.rotulo}</p>
                {a.exige_checkin && (
                  <p className="text-xs text-muted-foreground">
                    Exige check-in (tolerância: {a.tolerancia_checkin_minutos} min)
                  </p>
                )}
                <div className="flex flex-wrap gap-2 pt-1">
                  {livre && (
                    <Button size="sm" onClick={(e) => { e.stopPropagation(); setAmbienteParaReservar(a); }}>
                      <CalendarPlus className="mr-2 h-3 w-3" /> Reservar
                    </Button>
                  )}
                  <Button variant="outline" size="sm" asChild onClick={(e) => e.stopPropagation()}>
                    <a href={`${API_BASE_URL}/api/v1/environments/${a.id}/qrcode/`} target="_blank" rel="noreferrer">
                      <QrCode className="mr-2 h-3 w-3" /> QR code
                    </a>
                  </Button>
                  {isAdmin && (
                    <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); abrirEdicao(a); }}>
                      <Pencil className="mr-2 h-3 w-3" /> Editar
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <ReservationFormDialog
        aberto={ambienteParaReservar !== null}
        aoFechar={() => setAmbienteParaReservar(null)}
        aoCriar={() => {
          carregar();
          setAmbienteParaReservar(null);
        }}
        ambienteIdPadrao={ambienteParaReservar?.id}
      />

      <Dialog open={dialogAberto} onOpenChange={setDialogAberto}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{form.id ? "Editar ambiente" : "Novo ambiente"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={salvar} className="space-y-4">
            <div className="space-y-2">
              <Label>Nome</Label>
              <Input required value={form.nome} onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))} />
            </div>
            <div className="space-y-2">
              <Label>Tipo</Label>
              <Select value={form.tipo} onValueChange={(v) => setForm((f) => ({ ...f, tipo: v as TipoAmbiente }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {tipos.map((t) => (
                    <SelectItem key={t.valor} value={t.valor}>{t.rotulo}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Localização</Label>
                <Input value={form.localizacao} onChange={(e) => setForm((f) => ({ ...f, localizacao: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label>Capacidade</Label>
                <Input
                  type="number" min={1} value={form.capacidade}
                  onChange={(e) => setForm((f) => ({ ...f, capacidade: Number(e.target.value) }))}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Descrição</Label>
              <Textarea value={form.descricao} onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))} />
            </div>

            <div className="flex items-center justify-between rounded-md border p-3">
              <div>
                <Label>Exige check-in</Label>
                <p className="text-xs text-muted-foreground">
                  Libera a reserva automaticamente se ninguém confirmar presença (evita sala reservada e vazia).
                </p>
              </div>
              <Switch
                checked={form.exige_checkin}
                onCheckedChange={(v) => setForm((f) => ({ ...f, exige_checkin: v }))}
              />
            </div>

            {form.exige_checkin && (
              <div className="space-y-2">
                <Label>Tolerância de check-in (minutos)</Label>
                <Input
                  type="number" min={1} max={120}
                  value={form.tolerancia_checkin_minutos}
                  onChange={(e) => setForm((f) => ({ ...f, tolerancia_checkin_minutos: Number(e.target.value) }))}
                />
              </div>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogAberto(false)}>Cancelar</Button>
              <Button type="submit">Salvar</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
