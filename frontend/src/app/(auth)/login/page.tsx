"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export default function LoginPage() {
  const router = useRouter();
  const { toast } = useToast();
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUsuario = useAuthStore((s) => s.setUsuario);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [carregando, setCarregando] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setCarregando(true);
    try {
      const { data } = await api.post("/auth/login/", { username, password });
      setTokens(data.access, data.refresh);
      setUsuario(data.usuario);
      router.push("/dashboard");
    } catch {
      toast({
        variant: "destructive",
        title: "Falha no login",
        description: "Usuário ou senha inválidos. Tente novamente.",
      });
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary/10 via-background to-background px-4">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader className="space-y-1 text-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground text-xl font-bold">
            AF
          </div>
          <CardTitle className="text-2xl">Ambiente Fácil</CardTitle>
          <CardDescription>Entre com sua conta institucional</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Usuário</Label>
              <Input id="username" value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Senha</Label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <Button type="submit" className="w-full" disabled={carregando}>
              {carregando ? "Entrando..." : "Entrar"}
            </Button>
          </form>
          <p className="mt-4 text-center text-xs text-muted-foreground">
            Demonstração: admin / Admin@123 (administrador) ou professor / Usuario@123 (usuário)
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
