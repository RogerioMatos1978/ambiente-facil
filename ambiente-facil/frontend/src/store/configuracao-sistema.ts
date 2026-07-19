"use client";
import { create } from "zustand";
import { api } from "@/lib/api";
import type { EstiloIcone } from "@/types";

/**
 * Diferente de tema-cor.ts (preferência pessoal, salva no localStorage de cada
 * navegador), esta é uma configuração GLOBAL do sistema — o estilo dos ícones do
 * menu é o mesmo para todos os usuários, guardado no backend
 * (GET/PATCH /configuracao-sistema/, só admin altera). Por isso não usa o
 * middleware `persist`: é buscada do servidor a cada carregamento do painel.
 */
interface ConfiguracaoSistemaState {
  estiloIcone: EstiloIcone;
  carregado: boolean;
  carregar: () => Promise<void>;
  atualizar: (estilo: EstiloIcone) => Promise<void>;
}

export const useConfiguracaoSistemaStore = create<ConfiguracaoSistemaState>((set) => ({
  estiloIcone: "padrao",
  carregado: false,
  carregar: async () => {
    try {
      const { data } = await api.get("/configuracao-sistema/");
      set({ estiloIcone: data.estilo_icone, carregado: true });
    } catch {
      set({ carregado: true });
    }
  },
  atualizar: async (estilo) => {
    const { data } = await api.patch("/configuracao-sistema/", { estilo_icone: estilo });
    set({ estiloIcone: data.estilo_icone });
  },
}));
