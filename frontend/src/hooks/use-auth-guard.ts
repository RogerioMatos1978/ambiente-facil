"use client";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";

/**
 * Garante que a rota só renderize para usuários autenticados; redireciona para /login
 * caso contrário.
 *
 * Duas armadilhas de hidratação em sequência, as duas já causaram redirecionamento
 * indevido pro /login mesmo com sessão válida salva:
 *
 * 1) O token fica salvo no localStorage via zustand/persist, mas essa leitura só existe
 *    no navegador: durante o build/prerender do Next.js (sem window/localStorage) a store
 *    fica com os valores padrão (accessToken null). Por isso esperamos
 *    `useAuthStore.persist.hasHydrated()` antes de decidir qualquer coisa.
 *
 * 2) Mesmo depois de "hidratado", o valor de `accessToken` obtido via
 *    `useAuthStore((s) => s.accessToken)` (hook reativo, baseado em useSyncExternalStore)
 *    é OBRIGADO pelo React a usar o snapshot do servidor (sem token) na primeira
 *    renderização de hidratação — mesmo que a store já tenha o token de verdade guardado
 *    internamente. Esse valor só se corrige numa re-renderização logo em seguida. Se o
 *    efeito abaixo decidisse com base nesse valor reativo, ele via "accessToken null" nessa
 *    janela de alguns milissegundos e mandava pro /login por engano — e como o React Router
 *    do Next.js já dispara a navegação nesse mesmo instante, a correção posterior chega
 *    tarde demais para desfazer. Por isso a decisão usa `useAuthStore.getState().accessToken`
 *    (leitura direta e sempre atual da store, sem essa limitação de snapshot), e o valor
 *    reativo serve só de gatilho para reavaliar o efeito quando o token realmente mudar.
 */
export function useAuthGuard() {
  const router = useRouter();
  const pathname = usePathname();
  const accessTokenReativo = useAuthStore((s) => s.accessToken);
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
    const accessToken = useAuthStore.getState().accessToken;
    if (!accessToken) {
      const next = pathname ? `?next=${encodeURIComponent(pathname)}` : "";
      router.replace(`/login${next}`);
    } else {
      setPronto(true);
    }
    // accessTokenReativo não é usado diretamente na decisão (ver comentário acima) — está
    // aqui só para o efeito reavaliar quando o token mudar de verdade (login, logout,
    // falha de refresh).
  }, [hidratado, accessTokenReativo, pathname, router]);

  return pronto;
}
