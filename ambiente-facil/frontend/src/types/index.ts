export type Papel = "admin" | "user" | "vigilante";

export interface Usuario {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  papel: Papel;
  telefone: string;
  departamento: string;
  ativo_institucional: boolean;
  is_active: boolean;
  date_joined: string;
}

export type TipoAmbiente = "sala_aula" | "auditorio" | "laboratorio" | "sala_reuniao" | "outro";

export interface ReservaResumoAmbiente {
  id: number;
  numero_controle: string;
  titulo: string;
  solicitante_nome: string;
  reservado_para_categoria_display: string;
  reservado_para_nome: string;
  reservado_para_telefone: string;
  data_inicio: string;
  data_fim: string;
  duracao_display: string;
}

export interface Ambiente {
  id: number;
  nome: string;
  tipo: TipoAmbiente;
  localizacao: string;
  capacidade: number;
  recursos: string[];
  descricao: string;
  foto: string | null;
  ativo: boolean;
  exige_checkin: boolean;
  tolerancia_checkin_minutos: number;
  status_atual: "livre" | "ocupado";
  reserva_atual: ReservaResumoAmbiente | null;
  criado_em: string;
  atualizado_em: string;
}

export type StatusReserva = "pendente" | "confirmada" | "cancelada" | "concluida" | "expirada";

export type ReservadoParaCategoria = "professor" | "instrutor" | "cliente" | "limpeza" | "manutencao";

export interface Reserva {
  id: number;
  numero_controle: string;
  duracao_horas: number;
  duracao_display: string;
  ambiente: number;
  ambiente_detalhe: Ambiente;
  solicitante: number;
  solicitante_nome: string;
  titulo: string;
  descricao: string;
  reservado_para_categoria: ReservadoParaCategoria | "";
  reservado_para_categoria_display: string;
  reservado_para_nome: string;
  reservado_para_telefone: string;
  mensagem_guarita: string;
  chave_status: StatusChave | null;
  chave_status_display: string;
  chave_atrasada: boolean;
  data_inicio: string;
  data_fim: string;
  status: StatusReserva;
  status_display: string;
  motivo_cancelamento: string;
  cancelado_por: number | null;
  cancelado_em: string | null;
  checkin_confirmado_em: string | null;
  precisa_checkin: boolean;
  prazo_checkin: string;
  criado_em: string;
  atualizado_em: string;
}

export interface LogAuditoria {
  id: number;
  usuario: number | null;
  usuario_nome: string;
  acao: string;
  entidade: string;
  entidade_id: string | null;
  descricao: string;
  detalhes: Record<string, unknown>;
  endereco_ip: string | null;
  criado_em: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ResumoRelatorio {
  total: number;
  confirmadas: number;
  canceladas: number;
  concluidas: number;
  pendentes: number;
  expiradas: number;
  taxa_no_show: number;
  duracao_media_minutos: number;
}

export interface RelatorioPorDia {
  dia: string;
  total: number;
}

export interface RelatorioPorStatus {
  status: StatusReserva;
  status_display: string;
  total: number;
}

export interface RelatorioPorAmbiente {
  ambiente_id: number;
  ambiente_nome: string;
  total: number;
}

export interface RelatorioPorSolicitante {
  solicitante_id: number;
  solicitante_nome: string;
  total: number;
}

export interface RelatorioReservas {
  resumo: ResumoRelatorio;
  por_status: RelatorioPorStatus[];
  por_dia: RelatorioPorDia[];
  por_ambiente: RelatorioPorAmbiente[];
  por_solicitante: RelatorioPorSolicitante[];
}

export type EstiloIcone = "padrao" | "contornado" | "preenchido";

export interface ConfiguracaoSistema {
  estilo_icone: EstiloIcone;
  atualizado_em: string;
}

export type StatusChave = "disponivel" | "ocupada" | "devolvida";

export interface ReservaResumoGuarita {
  id: number;
  numero_controle: string;
  titulo: string;
  solicitante_nome: string;
  data_inicio: string;
  data_fim: string;
  duracao_display: string;
  status: StatusReserva;
  status_display: string;
  reservado_para_categoria: ReservadoParaCategoria | "";
  reservado_para_categoria_display: string;
  reservado_para_nome: string;
  reservado_para_telefone: string;
}

export interface Chave {
  id: number;
  ambiente: number;
  ambiente_nome: string;
  ambiente_localizacao: string;
  status: StatusChave;
  status_display: string;
  reserva_atual: number | null;
  reserva_atual_detalhe: ReservaResumoGuarita | null;
  retirada_em: string | null;
  retirada_por: number | null;
  retirada_por_nome: string | null;
  devolvida_em: string | null;
  reservas_hoje: ReservaResumoGuarita[];
  atualizado_em: string;
}
