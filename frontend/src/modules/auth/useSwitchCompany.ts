'use client';

import { useQueryClient } from '@tanstack/react-query';
import { useSession } from 'next-auth/react';

import { apiFetch } from 'api/http';

/** Troca a empresa activa sem novo login e limpa os dados em cache da anterior. */
export function useSwitchCompany() {
  const { data: session, update } = useSession();
  const queryClient = useQueryClient();

  return async (companyId: string) => {
    const tokens = await apiFetch('/auth/switch-company', {
      method: 'POST',
      accessToken: session?.accessToken,
      body: { company_id: companyId }
    });
    await update({ tokens });
    queryClient.clear();
  };
}
