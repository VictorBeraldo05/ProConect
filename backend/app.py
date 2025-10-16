import os
from flask import Flask, jsonify
from flask_cors import CORS

from .config import settings
from .routes_auth import auth_bp
from .routes_users import users_bp
from .routes_categorias import categorias_bp
from .routes_anuncios import anuncios_bp
from .routes_propostas import propostas_bp
from .routes_contratacoes import contratacoes_bp
from .routes_avaliacoes import avaliacoes_bp
from .routes_chat import chat_bp
from .routes_profissionais import profissionais_bp


def create_app() -> Flask:
    settings.validate()

    app = Flask(__name__)

    # CORS
    cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()] if settings.cors_origins else ["*"]
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True,
        expose_headers=["Content-Type"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    )

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(categorias_bp)
    app.register_blueprint(anuncios_bp)
    app.register_blueprint(propostas_bp)
    app.register_blueprint(contratacoes_bp)
    app.register_blueprint(avaliacoes_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(profissionais_bp)

    # Healthcheck
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    # JSON error handlers
    @app.errorhandler(Exception)
    def handle_exception(e):
        try:
            from werkzeug.exceptions import HTTPException
            if isinstance(e, HTTPException):
                return jsonify({"error": e.description}), e.code
        except Exception:
            pass
        return jsonify({"error": str(e)}), 500

    return app


app = create_app()
