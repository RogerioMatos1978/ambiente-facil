"use client";
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { useAuthGuard } from "@/hooks/use-auth-guard";
import { useAuthStore } from "@/store/auth";
import { useConfiguracaoSistemaStore } from "@/store/configuracao-sistema";

const titulos: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/calendario": "Calendário de Reservas",
  "/reservas": "Reservas",
  "/relatorios": "Relatórios",
  "/ambientes": "Ambientes",
  "/usuarios": "Usuários",
  "/auditoria": "Auditoria",
  "/configuracoes": "Configurações",
  "/guarita-chaves": "Guarita de Chaves",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pronto = useAuthGuard();
  const router = useRouter();
  const pathname = usePathname();
  const titulo = Object.entries(titulos).find(([rota]) => pathname?.startsWith(rota))?.[1] ?? "Ambiente Fácil";
  const carregarConfiguracaoSistema = useConfiguracaoSistemaStore((s) => s.carregar);
  const isAdmin = useAuthStore((s) => s.isAdmin());
  const isVigilante = useAuthStore((s) => s.isVigilante());

  useEffect(() => {
    if (pronto) carregarConfiguracaoSistema();
  }, [pronto, carregarConfiguracaoSistema]);

  // O vigilante só enxerga a Guarita de Chaves (o backend já bloqueia o resto via
  // NaoEhVigilante, isto aqui é só para não deixá-lo numa tela quebrada/vazia).
  // Usuário comum não chega na Guarita de Chaves.
  useEffect(() => {
    if (!pronto) return;
    if (isVigilante && pathname !== "/guarita-chaves") {
      router.replace("/guarita-chaves");
    } else if (!isVigilante && !isAdmin && pathname?.startsWith("/guarita-chaves")) {
      router.replace("/dashboard");
    }
  }, [pronto, isVigilante, isAdmin, pathname, router]);

  if (!pronto) {
    return <div className="flex min-h-screen items-center justify-center text-muted-foreground">Carregando...</div>;
  }

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar titulo={titulo} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6">{children}</main>
      </div>
    </div>
  );
}
