import 'next-auth';
import 'next-auth/jwt';

declare module 'next-auth' {
  interface User {
    accessToken: string;
    refreshToken: string;
    accessTokenExpires: number;
    companyId: string | null;
  }

  interface Session {
    accessToken: string;
    companyId: string | null;
    error?: 'RefreshAccessTokenError';
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    accessToken: string;
    refreshToken: string;
    accessTokenExpires: number;
    companyId: string | null;
    error?: 'RefreshAccessTokenError';
  }
}
