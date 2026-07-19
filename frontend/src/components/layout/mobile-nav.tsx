"use client";
import { useState } from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import { itensNavegacao } from "./nav-items";
import { NavIcon } from "./nav-icon";

/**
 * Navegação para telas pequenas: botão de menu (hambúrguer) que abre uma
 * gaveta lateral com os mesmos links da Sidebar. A Sidebar em si fica
 * escondida abaixo do breakpoint `md` — sem este componente o app ficaria
 * sem nenhuma forma de navegar no celular.
 */
export function MobileNav() {
  const [aberto, setAberto] = useState(false);
  const pathname = usePathname();
  const isAdmin = useAuthStore((s) => s.isAdmin());

  return (
    <DialogPrimitive.Root open={aberto} onOpenChange={setAberto}>
      <DialogPrimitive.Trigger asChild>
        <button
          type="button"
          aria-label="Abrir menu"
          className="flex h-9 w-9 items-center justify-center rounded-md hover:bg-accent md:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>
      </DialogPrimitive.Trigger>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 md:hidden" />
        <DialogPrimitive.Content
          className="fixed inset-y-0 left-0 z-50 flex h-full w-72 max-w-[80vw] flex-col border-r bg-card p-0 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left md:hidden"
        >
          <DialogPrimitive.Title className="sr-only">Menu de navegação</DialogPrimitive.Title>
          <div className="flex h-16 items-center justify-between gap-2 border-b px-6">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
                AF
              </div>
              <span className="font-semibold">Ambiente Fácil</span>
            </div>
            <DialogPrimitive.Close asChild>
              <button type="button" aria-label="Fechar menu" className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-accent">
                <X className="h-4 w-4" />
              </button>
            </DialogPrimitive.Close>
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
                    onClick={() => setAberto(false)}
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
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
