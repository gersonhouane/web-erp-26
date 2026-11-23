'use client';

import { useQuery } from '@tanstack/react-query';
import { useSession } from 'next-auth/react';

import { apiFetch } from 'api/http';

export interface CompanyBrief {
  id: string;
  name: string;
  role: string;
}

export interface Me {
  id: string;
  name: string;
  email: string;
  tenant_id: string;
  company_id: string | null;
  companies: CompanyBrief[];
  permissions: string[];
}

/** Utilizador actual, empresa activa e permissões, vindos de GET /auth/me. */
export function useCurrentUser() {
  const { data: session } = useSession();
  const query = useQuery({
    queryKey: ['me', session?.companyId],
    queryFn: () => apiFetch<Me>('/auth/me', { accessToken: session?.accessToken }),
    enabled: !!session?.accessToken,
    staleTime: 60_000
  });
  const permissions = new Set(query.data?.permissions ?? []);
  return {
    ...query,
    me: query.data,
    can: (code: string) => permissions.has(code)
  };
}
