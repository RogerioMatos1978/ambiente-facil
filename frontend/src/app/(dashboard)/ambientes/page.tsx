"use client";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { useToast } from "@/hooks/use-toast";
import type { Ambiente, TipoAmbiente } from "@/types";
import { Plus, Pencil } from "lucide-react";

const tipos: { valor: TipoAmbiente; rotulo: string }[] = [
  { valor: "sala_aula", rotulo: "Sala de Aula" },
  { valor: "auditorio", rotulo: "Auditório" },
  { valor: "laboratorio", rotulo: "Laboratório" },
  { valor: "sala_reuniao", rotulo: "Sala de Reunião" },
  { valor: "outro", rotulo: "Outro" },
];

const vazio = { id: 0, nome: "", tipo: "sala_aula" as TipoAmbiente, localizacao: "", capacidade: 10, descricao: "" };

export default function AmbientesPage() {
  const isAdmin = useAuthStore((s) => s.isAdmin());
  const { toast } = useToast();
  const [ambientes, setAmbientes] = useState<Ambiente[]>([]);
  const [dialogAberto, setDialogAberto] = useState(false);
  const [form, setForm] = useState(vazio);

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
    setForm({ id: a.id, nome: a.nome, tipo: a.tipo, localizacao: a.localizacao, capacidade: a.capacidade, descricao: a.descricao });
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
        {isAdmin && (
          <Button onClick={abrirNovo}>
            <Plus className="mr-2 h-4 w-4" /> Novo ambiente
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {ambientes.map((a) => (
          <Card key={a.id}>
            <CardHeader className="flex flex-row items-start justify-between">
              <div>
                <CardTitle className="text-base">{a.nome}</CardTitle>
                <p className="text-xs text-muted-foreground">{a.localizacao}</p>
              </div>
              <Badge variant={a.status_atual === "livre" ? "livre" : "ocupado"}>
                {a.status_atual === "livre" ? "Livre" : "Ocupado"}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>Capacidade: {a.capacidade} pessoas</p>
              <p>Tipo: {tipos.find((t) => t.valor === a.tipo)?.rotulo}</p>
              {isAdmin && (
                <Button variant="outline" size="sm" onClick={() => abrirEdicao(a)}>
                  <Pencil className="mr-2 h-3 w-3" /> Editar
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

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
            <div className="grid grid-cols-2 gap-4">
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
