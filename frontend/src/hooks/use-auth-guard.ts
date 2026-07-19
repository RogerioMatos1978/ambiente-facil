"use client";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";

/**
 * Garante que a rota só renderize para usuários autenticados; redireciona para /login
 * caso contrário.
 *
 * O token fica salvo no localStorage via zustand/persist, mas essa leitura é assíncrona:
 * no primeiro render depois de um F5, a store ainda está com os valores padrão (accessToken
 * null) até a reidratação terminar. Sem esperar isso, o guard via "sem token" e mandava para
 * o /login mesmo com uma sessão válida salva — por isso é preciso aguardar
 * `useAuthStore.persist.hasHydrated()` antes de decidir se redireciona.
 */
export function useAuthGuard() {
  const router = useRouter();
  const pathname = usePathname();
  const accessToken = useAuthStore((s) => s.accessToken);
  // useAuthStore.persist só existe em ambiente de navegador (durante o build/prerender
  // do Next.js, sem window/localStorage, o middleware persist não o expõe) — por isso o
  // encadeamento opcional abaixo, tanto no valor inicial quanto dentro do efeito.
  const [hidratado, setHidratado] = useState(() => useAuthStore.persist?.hasHydrated() ?? false);
  const [pronto, setPronto] = useState(false);

  useEffect(() => {
    if (!useAuthStore.persist || useAuthStore.persist.hasHydrated()) {
      setHidratado(true);
      return;
    }
    const cancelarInscricao = useAuthStore.persist.onFinishHydration(() => setHidratado(true));
    return cancelarInscricao;
  }, []);

  useEffect(() => {
    if (!hidratado) return;
    if (!accessToken) {
      const next = pathname ? `?next=${encodeURIComponent(pathname)}` : "";
      router.replace(`/login${next}`);
    } else {
      setPronto(true);
    }
  }, [hidratado, accessToken, pathname, router]);

  return pronto;
}
