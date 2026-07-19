"use client";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import type { Usuario } from "@/types";
import { Plus } from "lucide-react";

const vazio = {
  username: "", first_name: "", last_name: "", email: "", papel: "user" as "admin" | "user",
  telefone: "", departamento: "", password: "",
};

export default function UsuariosPage() {
  const { toast } = useToast();
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [dialogAberto, setDialogAberto] = useState(false);
  const [form, setForm] = useState(vazio);

  async function carregar() {
    const { data } = await api.get("/users/", { params: { page_size: 100 } });
    setUsuarios(data.results);
  }

  useEffect(() => {
    carregar();
  }, []);

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post("/users/", form);
      toast({ title: "Usuário criado com sucesso" });
      setDialogAberto(false);
      setForm(vazio);
      carregar();
    } catch {
      toast({ variant: "destructive", title: "Erro ao criar usuário", description: "Verifique os dados (usuário/e-mail podem já existir)." });
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{usuarios.length} usuário(s)</p>
        <Button onClick={() => setDialogAberto(true)}>
          <Plus className="mr-2 h-4 w-4" /> Novo usuário
        </Button>
      </div>

      <Card>
        <CardContent className="overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50 text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="p-3">Nome</th>
                <th className="hidden p-3 sm:table-cell">Usuário</th>
                <th className="hidden p-3 md:table-cell">E-mail</th>
                <th className="hidden p-3 md:table-cell">Departamento</th>
                <th className="p-3">Papel</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((u) => (
                <tr key={u.id} className="border-b last:border-0">
                  <td className="p-3 font-medium">{u.first_name} {u.last_name}</td>
                  <td className="hidden p-3 sm:table-cell">{u.username}</td>
                  <td className="hidden p-3 md:table-cell">{u.email}</td>
                  <td className="hidden p-3 md:table-cell">{u.departamento}</td>
                  <td className="p-3"><Badge variant={u.papel === "admin" ? "default" : "secondary"}>{u.papel === "admin" ? "Administrador" : "Usuário"}</Badge></td>
                  <td className="p-3">{u.is_active ? <Badge variant="livre">Ativo</Badge> : <Badge variant="destructive">Inativo</Badge>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Dialog open={dialogAberto} onOpenChange={setDialogAberto}>
        <DialogContent>
          <DialogHeader><DialogTitle>Novo usuário</DialogTitle></DialogHeader>
          <form onSubmit={salvar} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2"><Label>Nome</Label><Input required value={form.first_name} onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))} /></div>
              <div className="space-y-2"><Label>Sobrenome</Label><Input value={form.last_name} onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))} /></div>
            </div>
            <div className="space-y-2"><Label>Usuário (login)</Label><Input required value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} /></div>
            <div className="space-y-2"><Label>E-mail</Label><Input type="email" required value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} /></div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2"><Label>Telefone (WhatsApp)</Label><Input placeholder="5511999999999" value={form.telefone} onChange={(e) => setForm((f) => ({ ...f, telefone: e.target.value }))} /></div>
              <div className="space-y-2"><Label>Departamento</Label><Input value={form.departamento} onChange={(e) => setForm((f) => ({ ...f, departamento: e.target.value }))} /></div>
            </div>
            <div className="space-y-2">
              <Label>Papel</Label>
              <Select value={form.papel} onValueChange={(v) => setForm((f) => ({ ...f, papel: v as "admin" | "user" }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">Usuário</SelectItem>
                  <SelectItem value="admin">Administrador</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2"><Label>Senha inicial</Label><Input type="password" required value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} /></div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogAberto(false)}>Cancelar</Button>
              <Button type="submit">Criar usuário</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
