Backend (Flask) – Supabase Auth

Resumo
- API em Flask pronta para PythonAnywhere com rotas de autenticação integradas ao Supabase Auth e à tabela `usuarios` do seu schema simplificado.
- Estrutura mínima: `auth/register`, `auth/login`, `auth/me`, e rotas `users/me` (GET/PATCH).

Requisitos
- Python 3.10+
- Variáveis de ambiente:
  - SUPABASE_URL
  - SUPABASE_ANON_KEY (opcional; preferimos SERVICE_ROLE para server-side)
  - SUPABASE_SERVICE_ROLE_KEY
  - SUPABASE_JWT_SECRET
  - CORS_ORIGINS (opcional, padrão: *)

Instalação local
1. Crie e ative um virtualenv.
2. Instale dependências: `pip install -r backend/requirements.txt`.
3. Configure `.env` (baseie-se em `backend/.env.example`).
4. Execute: `flask --app backend.app:app run --debug`.

Deploy no PythonAnywhere (WSGI)
- Use `backend/wsgi.py` como entrypoint (aponta para `backend.app:app`).
- Defina as variáveis de ambiente no painel do PythonAnywhere.

Notas sobre Supabase
 - Registro (`/api/auth/register`) cria usuário no Supabase Auth (via Service Role) e em seguida insere o perfil em `usuarios` com o mesmo UUID.
 - Login (`/api/auth/login`) autentica no Supabase Auth e retorna os tokens + perfil.
 - `GET /api/auth/me`/`GET /api/users/me` exige `Authorization: Bearer <access_token>` do Supabase; o backend valida o JWT usando `SUPABASE_JWT_SECRET` e recupera o perfil.

Endpoints adicionais
- Categorias
  - `GET /api/categorias` – lista categorias.
- Anúncios
  - `GET /api/anuncios?tipo=&categoria_id=&busca=&urgencia=&status=&order=&page=&page_size=`
  - `POST /api/anuncios` – cria (auth).
  - `GET /api/anuncios/:id` – detalhe.
  - `PATCH /api/anuncios/:id` – atualiza (dono).
  - `DELETE /api/anuncios/:id` – exclui (dono).
- Propostas
  - `POST /api/propostas` – cria (worker) com `anuncio_id`.
  - `GET /api/propostas?anuncio_id=` – se informado, requer ser dono do anúncio; senão, lista do usuário autenticado.
  - `PATCH /api/propostas/:id` – atualiza (worker).
- Contratações
  - `POST /api/contratacoes` – cria (dono do anúncio) a partir de `anuncio_id` e opcional `proposta_id`.
  - `GET /api/contratacoes/minhas` – listagem para contratado e/ou anunciante.
  - `PATCH /api/contratacoes/:id` – atualizar status/valor (partes).
- Avaliações
  - `POST /api/avaliacoes` – cria (partes da contratação).
  - `GET /api/avaliacoes?contratacao_id=` – lista por contratação.
  - `GET /api/avaliacoes/por-contratado/:usuario_id` – lista e média agregada.
- Conversas e Mensagens
  - `GET /api/conversas` – lista conversas do usuário.
  - `POST /api/conversas` – cria conversa com `usuario_b_id` (opcional contexto do anúncio).
  - `GET /api/conversas/:id` – detalhe (participante).
  - `GET /api/conversas/:id/mensagens` – lista mensagens (participante).
  - `POST /api/conversas/:id/mensagens` – envia mensagem (participante).
  - `PATCH /api/mensagens/:id` – marcar lida.

Observações
- Filtros de busca em anúncios usam uma estratégia simples com duas consultas (título e descrição) e mescla no backend (MVP).
- Autorização é checada no backend (mesmo usando a Service Role) para respeitar as regras de negócio.
