"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import { itensNavegacao } from "./nav-items";
import { NavIcon } from "./nav-icon";

export function Sidebar() {
  const pathname = usePathname();
  const isAdmin = useAuthStore((s) => s.isAdmin());

  return (
    <aside className="hidden w-64 shrink-0 border-r bg-card md:flex md:flex-col print:hidden">
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
          AF
        </div>
        <span className="font-semibold">Ambiente Fácil</span>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {itensNavegacao
          .filter((item) => !item.adminOnly || isAdmin)
          .map((item) => {
            const ativo = pathname?.startsWith(item.href);
            const Icone = item.icone;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  ativo ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <NavIcon icone={Icone} ativo={ativo} />
                {item.label}
              </Link>
            );
          })}
      </nav>
    </aside>
  );
}
