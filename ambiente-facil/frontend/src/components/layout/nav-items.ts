import {
  LayoutDashboard, CalendarDays, Building2, ClipboardList, Users, ShieldCheck, BarChart3, Settings, KeyRound,
  type LucideIcon,
} from "lucide-react";
import type { Papel } from "@/types";

export interface ItemNavegacao {
  href: string;
  label: string;
  icone: LucideIcon;
  /** Quais papéis enxergam este item — allowlist explícita (em vez de um simples
   * "adminOnly") porque o perfil Vigilante tem acesso restrito só à Guarita de
   * Chaves, diferente de usuário comum (vê tudo que não é admin-only) e admin
   * (vê tudo). */
  visivelPara: Papel[];
}

export const itensNavegacao: ItemNavegacao[] = [
  { href: "/dashboard", label: "Dashboard", icone: LayoutDashboard, visivelPara: ["admin", "user"] },
  { href: "/calendario", label: "Calendário", icone: CalendarDays, visivelPara: ["admin", "user"] },
  { href: "/reservas", label: "Reservas", icone: ClipboardList, visivelPara: ["admin", "user"] },
  { href: "/relatorios", label: "Relatórios", icone: BarChart3, visivelPara: ["admin", "user"] },
  { href: "/ambientes", label: "Ambientes", icone: Building2, visivelPara: ["admin", "user"] },
  { href: "/usuarios", label: "Usuários", icone: Users, visivelPara: ["admin"] },
  { href: "/auditoria", label: "Auditoria", icone: ShieldCheck, visivelPara: ["admin"] },
  { href: "/configuracoes", label: "Configurações", icone: Settings, visivelPara: ["admin"] },
  { href: "/guarita-chaves", label: "Guarita de Chaves", icone: KeyRound, visivelPara: ["admin", "vigilante"] },
];
