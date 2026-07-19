"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { Check, LayoutDashboard, CalendarDays, ClipboardList, Monitor, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import { useTemaCorStore, OPCOES_TEMA_COR } from "@/store/tema-cor";
import { useConfiguracaoSistemaStore } from "@/store/configuracao-sistema";
import { NavIcon } from "@/components/layout/nav-icon";
import { useToast } from "@/hooks/use-toast";
import type { EstiloIcone } from "@/types";

const OPCOES_ESTILO_ICONE: { id: EstiloIcone; label: string; descricao: string }[] = [
  { id: "padrao", label: "Padrão", descricao: "Ícone sozinho, sem moldura (visual atual)" },
  { id: "contornado", label: "Contornado", descricao: "Ícone dentro de um quadrado com borda" },
  { id: "preenchido", label: "Preenchido", descricao: "Ícone dentro de um quadrado com fundo colorido" },
];

const ICONES_PREVIA = [LayoutDashboard, CalendarDays, ClipboardList];

/**
 * Página de configurações administrativas: só altera aparência/layout — nenhuma outra
 * regra do sistema. Duas seções:
 * - "Aparência": mesmos controles de tema claro/escuro e cor institucional já disponíveis
 *   no menu da barra superior (continuam lá também) — preferência pessoal, salva no
 *   navegador de quem está logado.
 * - "Ícones do sistema": estilo visual dos ícones do menu de navegação — configuração
 *   global (backend), vale para todos os usuários, só administrador pode alterar.
 */
export default function ConfiguracoesPage() {
  const router = useRouter();
  const { toast } = useToast();
  const isAdmin = useAuthStore((s) => s.isAdmin());

  const { theme, setTheme } = useTheme();
  const temaCor = useTemaCorStore((s) => s.tema);
  const setTemaCor = useTemaCorStore((s) => s.setTema);

  const estiloIcone = useConfiguracaoSistemaStore((s) => s.estiloIcone);
  const atualizarEstiloIcone = useConfiguracaoSistemaStore((s) => s.atualizar);
  const [salvando, setSalvando] = useState<EstiloIcone | null>(null);

  useEffect(() => {
    if (!isAdmin) router.replace("/dashboard");
  }, [isAdmin, router]);

  if (!isAdmin) {
    return <div className="flex min-h-[50vh] items-center justify-center text-muted-foreground">Redirecionando...</div>;
  }

  async function escolherEstiloIcone(estilo: EstiloIcone) {
    if (estilo === estiloIcone) return;
    setSalvando(estilo);
    try {
      await atualizarEstiloIcone(estilo);
      toast({ title: "Estilo de ícones atualizado", description: "Vale para todos os usuários do sistema." });
    } catch {
      toast({ variant: "destructive", title: "Erro", description: "Não foi possível salvar o estilo de ícones." });
    } finally {
      setSalvando(null);
    }
  }

  return (
    <div className="max-w-3xl space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Aparência</CardTitle>
          <CardDescription>
            Preferência pessoal, salva neste navegador — também disponível a qualquer momento
            no ícone de tema e no ícone de paleta da barra superior.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <p className="text-sm font-medium">Tema</p>
            <div className="flex flex-wrap gap-2">
              {[
                { id: "light", label: "Claro", Icone: Sun },
                { id: "dark", label: "Escuro", Icone: Moon },
                { id: "system", label: "Sistema", Icone: Monitor },
              ].map((opcao) => (
                <Button
                  key={opcao.id}
                  type="button"
                  variant={theme === opcao.id ? "default" : "outline"}
                  size="sm"
                  onClick={() => setTheme(opcao.id)}
                  className="gap-2"
                >
                  <opcao.Icone className="h-4 w-4" />
                  {opcao.label}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium">Cor institucional</p>
            <div className="grid gap-2 sm:grid-cols-2">
              {OPCOES_TEMA_COR.map((opcao) => (
                <button
                  key={opcao.id}
                  type="button"
                  onClick={() => setTemaCor(opcao.id)}
                  className={cn(
                    "flex items-center gap-3 rounded-md border p-3 text-left transition-colors hover:bg-accent",
                    temaCor === opcao.id && "border-primary bg-accent"
                  )}
                >
                  <span
                    className="flex h-6 w-6 shrink-0 overflow-hidden rounded-full border"
                    style={{ background: `linear-gradient(135deg, ${opcao.corPrincipal} 50%, ${opcao.corDetalhe} 50%)` }}
                    aria-hidden
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-medium leading-none">{opcao.label}</span>
                    <span className="mt-1 block text-xs text-muted-foreground">{opcao.descricao}</span>
                  </span>
                  {temaCor === opcao.id && <Check className="h-4 w-4 shrink-0 text-primary" />}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Ícones do sistema</CardTitle>
          <CardDescription>
            Configuração global: o estilo escolhido aqui vale para o menu de navegação de
            todos os usuários (eles veem o novo estilo no próximo carregamento da página).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2 sm:grid-cols-3">
            {OPCOES_ESTILO_ICONE.map((opcao) => (
              <button
                key={opcao.id}
                type="button"
                disabled={salvando !== null}
                onClick={() => escolherEstiloIcone(opcao.id)}
                className={cn(
                  "flex flex-col items-start gap-2 rounded-md border p-3 text-left transition-colors hover:bg-accent disabled:opacity-60",
                  estiloIcone === opcao.id && "border-primary bg-accent"
                )}
              >
                <div className="flex w-full items-center justify-between">
                  <span className="text-sm font-medium">{opcao.label}</span>
                  {estiloIcone === opcao.id && <Check className="h-4 w-4 text-primary" />}
                </div>
                <span className="text-xs text-muted-foreground">{opcao.descricao}</span>
              </button>
            ))}
          </div>

          <div className="space-y-2 rounded-md border bg-muted/30 p-3">
            <p className="text-xs font-medium text-muted-foreground">Prévia (com o estilo salvo)</p>
            <div className="flex gap-4">
              {ICONES_PREVIA.map((Icone, i) => (
                <div key={i} className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm text-muted-foreground">
                  <NavIcon icone={Icone} />
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
