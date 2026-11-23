/**
 * Configuração do NextAuth (v4, a versão usada pelo Able Pro Next.js).
 *
 * O login é feito no FastAPI. Os tokens do FastAPI ficam dentro do JWT encriptado
 * do NextAuth (cookie httpOnly), e o access token é renovado quando expira.
 */
import type { NextAuthOptions } from 'next-auth';
import type { JWT } from 'next-auth/jwt';
import CredentialsProvider from 'next-auth/providers/credentials';

import { API_URL } from 'api/http';

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  company_id: string | null;
}

// Renova um pouco antes de expirar, para não falhar a meio de um pedido.
const REFRESH_MARGIN_MS = 30_000;

async function postJson(path: string, body: unknown): Promise<Response> {
  return fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    cache: 'no-store'
  });
}

function fromTokens(tokens: TokenResponse): Pick<JWT, 'accessToken' | 'refreshToken' | 'accessTokenExpires' | 'companyId'> {
  return {
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token,
    accessTokenExpires: Date.now() + tokens.expires_in * 1000,
    companyId: tokens.company_id
  };
}

async function refreshAccessToken(token: JWT): Promise<JWT> {
  const res = await postJson('/auth/refresh', { refresh_token: token.refreshToken });
  if (!res.ok) {
    return { ...token, error: 'RefreshAccessTokenError' };
  }
  return { ...token, ...fromTokens((await res.json()) as TokenResponse), error: undefined };
}

export const authOptions: NextAuthOptions = {
  session: { strategy: 'jwt' },
  pages: { signIn: '/login' },
  providers: [
    CredentialsProvider({
      id: 'weberp',
      name: 'Web ERP',
      credentials: {
        email: { label: 'E-mail', type: 'email' },
        password: { label: 'Senha', type: 'password' }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials.password) return null;
        const res = await postJson('/auth/login', { email: credentials.email, password: credentials.password });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          // O código (ex.: ACCOUNT_LOCKED) chega à página de login em ?error=
          throw new Error(body.code ?? 'INVALID_CREDENTIALS');
        }
        const tokens = (await res.json()) as TokenResponse;
        return { id: credentials.email, email: credentials.email, ...fromTokens(tokens) };
      }
    })
  ],
  callbacks: {
    async jwt({ token, user, trigger, session }) {
      if (user) {
        return { ...token, ...fromTokens({
          access_token: user.accessToken,
          refresh_token: user.refreshToken,
          expires_in: (user.accessTokenExpires - Date.now()) / 1000,
          company_id: user.companyId
        }) };
      }
      // Depois de trocar de empresa, o cliente chama update() com os novos tokens.
      if (trigger === 'update' && session?.tokens) {
        return { ...token, ...fromTokens(session.tokens as TokenResponse), error: undefined };
      }
      if (Date.now() < token.accessTokenExpires - REFRESH_MARGIN_MS) {
        return token;
      }
      return refreshAccessToken(token);
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      session.companyId = token.companyId;
      session.error = token.error;
      return session;
    }
  },
  events: {
    async signOut({ token }) {
      if (token?.refreshToken) {
        await postJson('/auth/logout', { refresh_token: token.refreshToken }).catch(() => undefined);
      }
    }
  }
};
