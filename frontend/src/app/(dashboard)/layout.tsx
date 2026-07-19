"use client";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { useAuthGuard } from "@/hooks/use-auth-guard";

const titulos: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/calendario": "Calendário de Reservas",
  "/reservas": "Reservas",
  "/ambientes": "Ambientes",
  "/usuarios": "Usuários",
  "/auditoria": "Auditoria",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pronto = useAuthGuard();
  const pathname = usePathname();
  const titulo = Object.entries(titulos).find(([rota]) => pathname?.startsWith(rota))?.[1] ?? "Ambiente Fácil";

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
