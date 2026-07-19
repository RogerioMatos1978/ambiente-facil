"use client";
import { useEffect, useState } from "react";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import type { Ambiente, ReservadoParaCategoria } from "@/types";

const OPCOES_RESERVADO_PARA: { valor: ReservadoParaCategoria; rotulo: string }[] = [
  { valor: "professor", rotulo: "Professor" },
  { valor: "instrutor", rotulo: "Instrutor" },
  { valor: "cliente", rotulo: "Cliente" },
  { valor: "limpeza", rotulo: "Limpeza" },
  { valor: "manutencao", rotulo: "Manutenção" },
];

interface Props {
  aberto: boolean;
  aoFechar: () => void;
  aoCriar: () => void;
  ambienteIdPadrao?: number;
  inicioPadrao?: string;
  fimPadrao?: string;
}

function paraDatetimeLocal(iso?: string) {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function ReservationFormDialog({
  aberto, aoFechar, aoCriar, ambienteIdPadrao, inicioPadrao, fimPadrao,
}: Props) {
  const { toast } = useToast();
  const [ambientes, setAmbientes] = useState<Ambiente[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const [form, setForm] = useState({
    ambiente: ambienteIdPadrao ?? 0,
    titulo: "",
    descricao: "",
    data_inicio: paraDatetimeLocal(inicioPadrao),
    data_fim: paraDatetimeLocal(fimPadrao),
    reservado_para_categoria: "" as ReservadoParaCategoria | "",
    reservado_para_nome: "",
    reservado_para_telefone: "",
  });

  useEffect(() => {
    if (!aberto) return;
    api.get("/environments/", { params: { page_size: 100, ativo: true } }).then((res) => setAmbientes(res.data.results));
    setForm({
      ambiente: ambienteIdPadrao ?? 0,
      titulo: "",
      descricao: "",
      data_inicio: paraDatetimeLocal(inicioPadrao),
      data_fim: paraDatetimeLocal(fimPadrao),
      reservado_para_categoria: "",
      reservado_para_nome: "",
      reservado_para_telefone: "",
    });
    setErro(null);
  }, [aberto, ambienteIdPadrao, inicioPadrao, fimPadrao]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await api.post("/reservations/", {
        ambiente: form.ambiente,
        titulo: form.titulo,
        descricao: form.descricao,
        data_inicio: new Date(form.data_inicio).toISOString(),
        data_fim: new Date(form.data_fim).toISOString(),
        reservado_para_categoria: form.reservado_para_categoria,
        reservado_para_nome: form.reservado_para_nome,
        reservado_para_telefone: form.reservado_para_telefone,
      });
      toast({ title: "Reserva criada", description: "A reserva foi registrada com sucesso." });
      aoCriar();
      aoFechar();
    } catch (err: unknown) {
      interface ErroApi {
        response?: {
          data?: {
            detalhes?:
              | {
                  conflito?: string[];
                  non_field_errors?: string[];
                  reservado_para_categoria?: string[];
                  reservado_para_nome?: string[];
                  reservado_para_telefone?: string[];
                  data_inicio?: string[];
                  data_fim?: string[];
                }
              | string;
          };
        };
      };
      const detalhes = (err as ErroApi)?.response?.data?.detalhes;
      const mensagem =
        (typeof detalhes === "object" && detalhes?.conflito?.[0]) ||
        (typeof detalhes === "object" && detalhes?.non_field_errors?.[0]) ||
        (typeof detalhes === "object" && detalhes?.reservado_para_categoria?.[0]) ||
        (typeof detalhes === "object" && detalhes?.reservado_para_nome?.[0]) ||
        (typeof detalhes === "object" && detalhes?.reservado_para_telefone?.[0]) ||
        (typeof detalhes === "object" && detalhes?.data_inicio?.[0]) ||
        (typeof detalhes === "object" && detalhes?.data_fim?.[0]) ||
        (typeof detalhes === "string" ? detalhes : null) ||
        "Não foi possível criar a reserva. Verifique os dados informados.";
      setErro(mensagem);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Dialog open={aberto} onOpenChange={(v) => !v && aoFechar()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Nova reserva</DialogTitle>
          <DialogDescription>
            Preencha os dados abaixo. Conflitos de horário são detectados automaticamente.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Ambiente</Label>
            <Select
              value={form.ambiente ? String(form.ambiente) : undefined}
              onValueChange={(v) => setForm((f) => ({ ...f, ambiente: Number(v) }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecione um ambiente" />
              </SelectTrigger>
              <SelectContent>
                {ambientes.map((a) => (
                  <SelectItem key={a.id} value={String(a.id)}>
                    {a.nome} ({a.capacidade} lugares)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="titulo">Título</Label>
            <Input
              id="titulo"
              required
              value={form.titulo}
              onChange={(e) => setForm((f) => ({ ...f, titulo: e.target.value }))}
            />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="inicio">Início</Label>
              <Input
                id="inicio"
                type="datetime-local"
                required
                value={form.data_inicio}
                onChange={(e) => setForm((f) => ({ ...f, data_inicio: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="fim">Fim</Label>
              <Input
                id="fim"
                type="datetime-local"
                required
                value={form.data_fim}
                onChange={(e) => setForm((f) => ({ ...f, data_fim: e.target.value }))}
              />
            </div>
          </div>
          <p className="-mt-2 text-xs text-muted-foreground">
            Reservas só podem ser feitas entre 07:00 e 22:00, no mesmo dia.
          </p>

          <div className="space-y-2">
            <Label htmlFor="descricao">Descrição (opcional)</Label>
            <Textarea
              id="descricao"
              value={form.descricao}
              onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))}
            />
          </div>

          <div className="space-y-3 rounded-md border p-3">
            <p className="text-sm font-medium">Reservado para</p>
            <div className="space-y-2">
              <Label htmlFor="reservado_para_categoria">Categoria</Label>
              <Select
                value={form.reservado_para_categoria || undefined}
                onValueChange={(v) =>
                  setForm((f) => ({ ...f, reservado_para_categoria: v as ReservadoParaCategoria }))
                }
              >
                <SelectTrigger id="reservado_para_categoria">
                  <SelectValue placeholder="Selecione uma categoria" />
                </SelectTrigger>
                <SelectContent>
                  {OPCOES_RESERVADO_PARA.map((opcao) => (
                    <SelectItem key={opcao.valor} value={opcao.valor}>
                      {opcao.rotulo}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="reservado_para_nome">Nome</Label>
                <Input
                  id="reservado_para_nome"
                  required
                  placeholder="Nome de quem vai usar a sala"
                  value={form.reservado_para_nome}
                  onChange={(e) => setForm((f) => ({ ...f, reservado_para_nome: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reservado_para_telefone">Telefone</Label>
                <Input
                  id="reservado_para_telefone"
                  required
                  placeholder="Ex.: 62999990000"
                  value={form.reservado_para_telefone}
                  onChange={(e) => setForm((f) => ({ ...f, reservado_para_telefone: e.target.value }))}
                />
              </div>
            </div>
          </div>

          {erro && (
            <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
              {erro}
            </div>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={aoFechar}>Cancelar</Button>
            <Button
              type="submit"
              disabled={
                enviando ||
                !form.ambiente ||
                !form.reservado_para_categoria ||
                !form.reservado_para_nome ||
                !form.reservado_para_telefone
              }
            >
              {enviando ? "Salvando..." : "Criar reserva"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
