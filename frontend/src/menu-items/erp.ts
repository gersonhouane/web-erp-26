/**
 * Menu do ERP. Cada entrada declara a permissão de que precisa; filterMenu() remove
 * o que o utilizador não pode ver. O formato segue o dos menu-items do Able Pro
 * (id, title, type, url, children); os ícones são associados no ficheiro do tema.
 */
export type NavItemType = 'group' | 'collapse' | 'item';

export interface ErpNavItem {
  id: string;
  title: string;
  type: NavItemType;
  url?: string;
  icon?: string;
  permission?: string;
  children?: ErpNavItem[];
}

export const erpMenu: ErpNavItem[] = [
  {
    id: 'group-geral',
    title: 'Geral',
    type: 'group',
    children: [{ id: 'painel', title: 'Painel', type: 'item', url: '/dashboard', icon: 'home' }]
  },
  {
    id: 'group-definicoes',
    title: 'Definições',
    type: 'group',
    children: [
      { id: 'empresa', title: 'Empresa', type: 'item', url: '/definicoes/empresa', icon: 'building', permission: 'core.empresa.ver' },
      { id: 'filiais', title: 'Filiais', type: 'item', url: '/definicoes/filiais', icon: 'shop', permission: 'core.filial.ver' },
      { id: 'utilizadores', title: 'Utilizadores', type: 'item', url: '/utilizadores', icon: 'profile-2user', permission: 'utilizadores.utilizador.ver' },
      { id: 'papeis', title: 'Papéis e permissões', type: 'item', url: '/utilizadores/papeis', icon: 'security-user', permission: 'utilizadores.papel.ver' },
      { id: 'auditoria', title: 'Auditoria', type: 'item', url: '/definicoes/auditoria', icon: 'document-text', permission: 'core.auditoria.ver' }
    ]
  }
];

export function filterMenu(items: ErpNavItem[], can: (code: string) => boolean): ErpNavItem[] {
  return items
    .filter((item) => !item.permission || can(item.permission))
    .map((item) => (item.children ? { ...item, children: filterMenu(item.children, can) } : item))
    .filter((item) => item.type === 'item' || (item.children?.length ?? 0) > 0);
}
