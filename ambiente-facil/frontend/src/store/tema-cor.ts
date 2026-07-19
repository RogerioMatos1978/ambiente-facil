"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";

export type TemaCor = "combinado" | "sesi" | "senai" | "iel" | "fieg";

export interface OpcaoTemaCor {
  id: TemaCor;
  label: string;
  descricao: string;
  corPrincipal: string; // hex — usado só para desenhar a bolinha de amostra no menu
  corDetalhe: string;
}

export const OPCOES_TEMA_COR: OpcaoTemaCor[] = [
  {
    id: "combinado",
    label: "SESI SENAI (padrão)",
    descricao: "Unidade Integrada — azul, verde e laranja",
    corPrincipal: "#164194",
    corDetalhe: "#52AE32",
  },
  {
    id: "sesi",
    label: "SESI",
    descricao: "Verde institucional do SESI",
    corPrincipal: "#3E9422",
    corDetalhe: "#3E9422",
  },
  {
    id: "senai",
    label: "SENAI",
    descricao: "Laranja institucional do SENAI",
    corPrincipal: "#D1430C",
    corDetalhe: "#D1430C",
  },
  {
    id: "iel",
    label: "IEL",
    descricao: "Verde-água institucional do IEL",
    corPrincipal: "#2E8577",
    corDetalhe: "#2E8577",
  },
  {
    id: "fieg",
    label: "Sistema FIEG",
    descricao: "Azul claro do Sistema FIEG",
    corPrincipal: "#007AB8",
    corDetalhe: "#007AB8",
  },
];

interface TemaCorState {
  tema: TemaCor;
  setTema: (tema: TemaCor) => void;
}

export const useTemaCorStore = create<TemaCorState>()(
  persist(
    (set) => ({
      tema: "combinado",
      setTema: (tema) => set({ tema }),
    }),
    { name: "ambiente-facil-tema-cor" }
  )
);
