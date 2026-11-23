# Frontend do Web ERP

O painel usa o **Able Pro (versão Next.js + TypeScript)**. O Able Pro é um tema comercial,
por isso o código dele **não** está neste repositório: entra a partir da vossa cópia licenciada.
Esta pasta tem apenas o código do ERP, organizado para encaixar no tema.

## Integrar o Able Pro (uma vez)

1. Copie o conteúdo da pasta `full-version` do Able Pro Next.js (TypeScript) para `frontend/`,
   **sem** apagar os ficheiros que já cá estão. Se o tema trouxer ficheiros com o mesmo nome
   (`middleware.ts`, `app/api/auth/[...nextauth]/route.ts`), fique com os deste repositório.
2. Instale as dependências do ERP por cima das do tema:
   ```bash
   npm install next-auth@4 @tanstack/react-query@5
   npm install -D openapi-typescript
   ```
3. Configure o `tsconfig.json` do tema com `"baseUrl": "src"` (o Able Pro já usa imports a
   partir de `src`, como `import ... from 'api/http'`).
4. Crie `.env.local`:
   ```
   WEBERP_API_URL=http://localhost:8000/api/v1
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=<gerar com: openssl rand -base64 32>
   ```
5. Apague as páginas de demonstração do tema que não vão ser usadas e substitua o menu do
   tema por `src/menu-items/erp.ts`, filtrado com `filterMenu(erpMenu, can)`.
6. Na página de login do tema, chame `signIn('weberp', { email, password })` e mostre a
   mensagem de `i18n/pt-MZ.json` para o código que chega em `?error=`.

## O que está aqui

| Caminho | Para quê |
| --- | --- |
| `src/auth/options.ts` | NextAuth: login no FastAPI, tokens na sessão, renovação automática |
| `src/app/api/auth/[...nextauth]/route.ts` | Rota do NextAuth |
| `src/middleware.ts` | Bloqueia páginas sem sessão |
| `src/api/http.ts` | `apiFetch()` com token e erros `{code, message, details}` |
| `src/modules/auth/` | `useCurrentUser()` (permissões, `can()`) e `useSwitchCompany()` |
| `src/menu-items/erp.ts` | Menu do ERP com a permissão de cada entrada |
| `src/i18n/pt-MZ.json` | Mensagens em português para cada código de erro da API |
| `src/utils/format.ts` | Formatos de Moçambique: `1 234,50 MT`, `23/11/2026` |

O código de negócio de cada módulo vai para `src/modules/<modulo>/` e as páginas para
`src/app/(dashboard)/<modulo>/`, para que actualizar o tema toque pouco no ERP.

## Tipos da API

Com a API a correr:

```bash
npx openapi-typescript http://localhost:8000/api/v1/openapi.json -o src/api/generated/schema.ts
```
