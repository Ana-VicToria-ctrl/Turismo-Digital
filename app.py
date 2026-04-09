from __future__ import annotations

import sqlite3
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "data" / "turismo_tefe.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "tefe-turismo-projeto-final-2026"


ATTRACTION_SEEDS = [
    {
        "title": "Praça Santa Teresa",
        "summary": "Ponto histórico de convivência e palco de eventos no coração de Tefé.",
        "content": (
            "A Praça Santa Teresa é um dos espaços mais tradicionais de Tefé. "
            "Ela concentra encontros da população, eventos culturais, celebrações religiosas "
            "e momentos importantes da vida social da cidade. Pela localização central e pela "
            "força simbólica que carrega, funciona como um cartão de visita para quem deseja "
            "entender a identidade urbana e cultural do município."
        ),
        "image": "img/praca-santa-teresa.jpg",
    },
    {
        "title": "Feira da Agricultura Familiar",
        "summary": "Sabores regionais, produção local e valorização da economia amazônica.",
        "content": (
            "A Feira da Agricultura Familiar fortalece produtores locais e aproxima visitantes "
            "da cultura alimentar da região. O espaço reúne frutas, verduras, farinhas, peixes, "
            "artesanato e outros produtos típicos, criando uma experiência rica para quem deseja "
            "conhecer a economia criativa e o cotidiano de Tefé."
        ),
        "image": "img/feira-agricultura.webp",
    },
    {
        "title": "Festa da Castanha",
        "summary": "Celebração cultural com música, culinária e tradições da região.",
        "content": (
            "A Festa da Castanha destaca a produção regional e valoriza saberes tradicionais "
            "ligados ao extrativismo amazônico. O evento costuma reunir apresentações culturais, "
            "pratos típicos, música e manifestações populares, reforçando o vínculo entre natureza, "
            "economia local e memória coletiva."
        ),
        "image": "img/festa-castanha.jpg",
    },
    {
        "title": "Arraial Folclórico",
        "summary": "Quadrilhas, bois-bumbás e manifestações populares que movimentam a cidade.",
        "content": (
            "O arraial é uma das celebrações que mais animam Tefé ao longo do ano. A programação "
            "combina danças típicas, apresentações folclóricas, comidas regionais e muito encontro "
            "comunitário. É um momento em que a cidade exibe com força sua criatividade, alegria e "
            "tradição popular."
        ),
        "image": "img/arraial-tefe.jpg",
    },
    {
        "title": "Encontro das Águas",
        "summary": "Paisagem amazônica marcante para passeios, contemplação e fotografia.",
        "content": (
            "O Encontro das Águas na região de Tefé é um espetáculo visual que chama atenção pela "
            "força da paisagem amazônica. A experiência é ideal para contemplação, registro fotográfico "
            "e passeios guiados, tornando-se um ponto de grande interesse turístico e educativo."
        ),
        "image": "img/encontro-aguas.jpg",
    },
    {
        "title": "Passeios de Barco",
        "summary": "Vivência com a natureza, comunidades ribeirinhas e os igarapés da região.",
        "content": (
            "Os passeios de barco permitem um contato mais direto com rios, lagos, comunidades "
            "ribeirinhas e cenários naturais da região. É uma atividade que combina lazer, observação "
            "da paisagem e aproximação com o modo de vida amazônico, ampliando a experiência do visitante."
        ),
        "image": "img/passeio-barco.jpg",
    },
]


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_: object | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def ensure_column(db: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db() -> None:
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row

    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Nova',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS attractions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            summary TEXT NOT NULL,
            content TEXT NOT NULL,
            image TEXT NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        );
        """
    )

    ensure_column(db, "attractions", "summary", "TEXT NOT NULL DEFAULT ''")
    ensure_column(db, "attractions", "content", "TEXT NOT NULL DEFAULT ''")
    ensure_column(db, "attractions", "image", "TEXT NOT NULL DEFAULT 'img/encontro-aguas.jpg'")
    ensure_column(db, "attractions", "created_by", "INTEGER")
    ensure_column(db, "attractions", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

    seeds = [
        ("Administrador Tefé", "admin", "admin@tefe.com", "admin123", "admin"),
        ("Visitante Demo", "visitante", "visitante@tefe.com", "123456", "user"),
    ]

    for name, username, email, password, role in seeds:
        existing = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email),
        ).fetchone()
        if not existing:
            db.execute(
                """
                INSERT INTO users (name, username, email, password_hash, role)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, username, email, generate_password_hash(password), role),
            )

    admin_user = db.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    demo_user = db.execute("SELECT id FROM users WHERE username = 'visitante'").fetchone()

    for attraction in ATTRACTION_SEEDS:
        existing = db.execute(
            "SELECT id FROM attractions WHERE title = ?",
            (attraction["title"],),
        ).fetchone()
        if not existing:
            db.execute(
                """
                INSERT INTO attractions (title, summary, content, image, created_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    attraction["title"],
                    attraction["summary"],
                    attraction["content"],
                    attraction["image"],
                    admin_user["id"] if admin_user else None,
                ),
            )

    if demo_user:
        count = db.execute(
            "SELECT COUNT(*) AS total FROM suggestions WHERE user_id = ?",
            (demo_user["id"],),
        ).fetchone()["total"]
        if count == 0:
            db.executemany(
                """
                INSERT INTO suggestions (user_id, title, message, status)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        demo_user["id"],
                        "Roteiro gastronômico",
                        "Seria legal destacar melhor comidas típicas e feiras de fim de semana.",
                        "Em análise",
                    ),
                    (
                        demo_user["id"],
                        "Passeio de barco",
                        "Um mapa com pontos de saída para os passeios ajudaria bastante.",
                        "Nova",
                    ),
                ],
            )

    db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("Faça login para acessar essa área.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def role_required(role: str):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if session.get("role") != role:
                flash("Você não tem permissão para acessar essa área.", "error")
                if session.get("role") == "admin":
                    return redirect(url_for("admin_dashboard"))
                if session.get("role") == "user":
                    return redirect(url_for("user_dashboard"))
                return redirect(url_for("login"))
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


@app.context_processor
def inject_user():
    return {
        "current_user": {
            "id": session.get("user_id"),
            "name": session.get("name"),
            "role": session.get("role"),
        }
    }


def fetch_attractions(limit: int | None = None) -> list[sqlite3.Row]:
    query = """
        SELECT id, title, summary, content, image, created_at
        FROM attractions
        ORDER BY created_at DESC, id DESC
    """
    if limit:
        query += " LIMIT ?"
        return get_db().execute(query, (limit,)).fetchall()
    return get_db().execute(query).fetchall()


@app.route("/assets/<path:filename>")
def asset_file(filename: str):
    return send_from_directory(BASE_DIR, filename)


@app.route("/")
def home():
    return render_template("index.html", attractions=fetch_attractions(limit=3))


@app.route("/atracoes")
def attractions():
    return render_template("attractions.html", attractions=fetch_attractions())


@app.route("/atracoes/<int:attraction_id>")
def attraction_detail(attraction_id: int):
    attraction = get_db().execute(
        """
        SELECT id, title, summary, content, image, created_at
        FROM attractions
        WHERE id = ?
        """,
        (attraction_id,),
    ).fetchone()
    if attraction is None:
        flash("A atração solicitada não foi encontrada.", "error")
        return redirect(url_for("attractions"))
    return render_template("attraction_detail.html", attraction=attraction)


@app.route("/sobre")
def about():
    return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not all([name, username, email, password]):
            flash("Preencha todos os campos para criar a conta.", "error")
            return render_template("register.html")

        db = get_db()
        exists = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email),
        ).fetchone()

        if exists:
            flash("Esse usuário ou e-mail já está cadastrado.", "error")
            return render_template("register.html")

        db.execute(
            """
            INSERT INTO users (name, username, email, password_hash, role)
            VALUES (?, ?, ?, ?, 'user')
            """,
            (name, username, email, generate_password_hash(password)),
        )
        db.commit()
        flash("Conta criada com sucesso. Agora é só entrar.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_value = request.form.get("login", "").strip().lower()
        password = request.form.get("password", "")

        user = get_db().execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (login_value, login_value),
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session.update(
                {"user_id": user["id"], "name": user["name"], "role": user["role"]}
            )
            flash(f"Bem-vindo, {user['name']}!", "success")
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("user_dashboard"))

        flash("Credenciais inválidas. Tente novamente.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sessão encerrada com sucesso.", "info")
    return redirect(url_for("home"))


@app.route("/painel", methods=["GET", "POST"])
@login_required
@role_required("user")
def user_dashboard():
    db = get_db()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        message = request.form.get("message", "").strip()

        if title and message:
            db.execute(
                """
                INSERT INTO suggestions (user_id, title, message)
                VALUES (?, ?, ?)
                """,
                (session["user_id"], title, message),
            )
            db.commit()
            flash("Sugestão enviada para a administração.", "success")
            return redirect(url_for("user_dashboard"))

        flash("Escreva um título e uma mensagem para enviar a sugestão.", "error")

    suggestions = db.execute(
        """
        SELECT title, message, status, created_at
        FROM suggestions
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (session["user_id"],),
    ).fetchall()

    return render_template("dashboard_user.html", suggestions=suggestions)


@app.route("/admin", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_dashboard():
    db = get_db()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        summary = request.form.get("summary", "").strip()
        content = request.form.get("content", "").strip()
        image = request.form.get("image", "").strip()

        if not all([title, summary, content, image]):
            flash("Preencha título, resumo, texto completo e imagem.", "error")
            return redirect(url_for("admin_dashboard"))

        exists = db.execute(
            "SELECT id FROM attractions WHERE title = ?",
            (title,),
        ).fetchone()
        if exists:
            flash("Já existe uma atração com esse título.", "error")
            return redirect(url_for("admin_dashboard"))

        db.execute(
            """
            INSERT INTO attractions (title, summary, content, image, created_by)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, summary, content, image, session["user_id"]),
        )
        db.commit()
        flash("Atração cadastrada com sucesso.", "success")
        return redirect(url_for("admin_dashboard"))

    users = db.execute(
        """
        SELECT name, username, email, role, created_at
        FROM users
        ORDER BY created_at DESC
        """
    ).fetchall()
    suggestions = db.execute(
        """
        SELECT s.title, s.message, s.status, s.created_at, u.name
        FROM suggestions s
        JOIN users u ON u.id = s.user_id
        ORDER BY s.created_at DESC
        """
    ).fetchall()
    attractions = fetch_attractions()

    stats = {
        "users": db.execute(
            "SELECT COUNT(*) AS total FROM users WHERE role = 'user'"
        ).fetchone()["total"],
        "admins": db.execute(
            "SELECT COUNT(*) AS total FROM users WHERE role = 'admin'"
        ).fetchone()["total"],
        "suggestions": db.execute(
            "SELECT COUNT(*) AS total FROM suggestions"
        ).fetchone()["total"],
        "attractions": db.execute(
            "SELECT COUNT(*) AS total FROM attractions"
        ).fetchone()["total"],
    }

    return render_template(
        "dashboard_admin.html",
        users=users,
        suggestions=suggestions,
        attractions=attractions,
        stats=stats,
    )
@app.route("/admin/editar-atracao/<int:attraction_id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_attraction(attraction_id):
    db = get_db()

    # Buscar atração
    attraction = db.execute(
        "SELECT * FROM attractions WHERE id = ?",
        (attraction_id,),
    ).fetchone()

    if not attraction:
        flash("Atração não encontrada.", "error")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        summary = request.form.get("summary", "").strip()
        content = request.form.get("content", "").strip()
        image = request.form.get("image", "").strip()

        if not all([title, summary, content, image]):
            flash("Preencha todos os campos.", "error")
            return redirect(url_for("edit_attraction", attraction_id=attraction_id))

        db.execute(
            """
            UPDATE attractions
            SET title = ?, summary = ?, content = ?, image = ?
            WHERE id = ?
            """,
            (title, summary, content, image, attraction_id),
        )
        db.commit()

        flash("Atração atualizada com sucesso!", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("edit_attraction.html", attraction=attraction)
@app.route("/admin/excluir-atracao/<int:attraction_id>")
@login_required
@role_required("admin")
def delete_attraction(attraction_id):
    db = get_db()

    db.execute("DELETE FROM attractions WHERE id = ?", (attraction_id,))
    db.commit()

    flash("Atração excluída com sucesso!", "success")
    return redirect(url_for("admin_dashboard"))
init_db()

if __name__ == "__main__":
    app.run(debug=True)
