/**
 * Bloqueia as páginas do painel a quem não tem sessão. As permissões finas são
 * decididas pela API; aqui só se garante que há sessão válida.
 */
import { withAuth } from 'next-auth/middleware';

export default withAuth({
  pages: { signIn: '/login' },
  callbacks: {
    authorized: ({ token }) => !!token && !token.error
  }
});

export const config = {
  // Tudo excepto login, registo, rotas do NextAuth e ficheiros estáticos.
  matcher: ['/((?!login|register|forgot-password|api/auth|_next|favicon.ico|assets).*)']
};
