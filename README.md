# Tefe Turismo com Flask

Projeto acadêmico repaginado com:

- site de apresentação turística de Tefé-AM
- cadastro e login com Flask
- painel normal para usuários
- painel administrativo separado
- banco local em SQLite

## Como rodar

1. Ative o ambiente virtual:

```bash
source .venv/bin/activate
```

2. Instale as dependências caso precise:

```bash
pip install -r requirements.txt
```

3. Inicie o servidor:

```bash
flask --app app run
```

Ou:

```bash
python app.py
```

4. Abra no navegador:

```text
http://127.0.0.1:5000
```

## Acessos prontos

- Admin: `admin` / `admin123`
- Usuário: `visitante@tefe.com` / `123456`

## Estrutura principal

- `app.py`: aplicação Flask e regras de autenticação
- `templates/`: páginas HTML com Jinja2
- `static/style.css`: visual do sistema
- `data/turismo_tefe.db`: banco criado automaticamente
