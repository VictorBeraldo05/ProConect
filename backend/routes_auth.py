from typing import Any, Dict

from flask import Blueprint, jsonify, request

from .supabase_client import get_admin_client, get_public_client
from .auth import (
    require_auth,
    get_current_user_profile,
    attach_session_cookies,
    clear_session_cookies,
)


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Cria usuário no Supabase Auth e insere perfil em `usuarios`.

    Body JSON: { nome, email, password, is_worker?, perfil_worker?, preferencias? }
    """
    data: Dict[str, Any] = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    cpf_raw = (data.get("cpf") or "").strip()
    is_worker = bool(data.get("is_worker", False))
    perfil_worker = data.get("perfil_worker") or {}
    preferencias = data.get("preferencias") or {}

    if not nome or not email or not password:
        return jsonify({"error": "Campos obrigatórios: nome, email, password"}), 400

    admin = get_admin_client()

    # 1) Cria usuário no Supabase Auth (email confirmado para facilitar MVP)
    try:
        created = admin.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {"nome": nome},
            }
        )
    except Exception as e:
        return jsonify({"error": f"Falha ao criar usuário no Auth: {e}"}), 400

    user = getattr(created, "user", None) or {}
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
    email_confirmed_at = user.get("email_confirmed_at") if isinstance(user, dict) else getattr(user, "email_confirmed_at", None)
    if not user_id:
        return jsonify({"error": "Não foi possível obter o id do usuário criado"}), 500

    # 2) Insere perfil em `usuarios`
    try:
        # normaliza CPF para apenas dígitos (se enviado)
        try:
            import re
            cpf_digits = re.sub(r"\D", "", cpf_raw) if cpf_raw else None
        except Exception:
            cpf_digits = cpf_raw or None

        profile = {
            "id": user_id,
            "nome": nome,
            "email": email,
            "cpf": cpf_digits,
            "is_worker": is_worker,
            "email_verificado": bool(email_confirmed_at),
            "perfil_worker": perfil_worker,
            "preferencias": preferencias,
        }
        inserted = admin.table("usuarios").insert(profile).execute()
        return jsonify({"user": {"id": user_id, "email": email}, "profile": inserted.data[0]}), 201
    except Exception as e:
        # rollback lógico: remover usuário Auth se perfil falhar
        try:
            admin.auth.admin.delete_user(user_id)
        except Exception:
            pass
        return jsonify({"error": f"Falha ao criar perfil: {e}"}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email_or_cpf = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    if not email_or_cpf or not password:
        return jsonify({"error": "Campos obrigatórios: email, password"}), 400

    # Se veio CPF, converte para email procurando na tabela usuarios
    email = email_or_cpf
    if "@" not in email_or_cpf:
        try:
            import re
            cpf_digits = re.sub(r"\D", "", email_or_cpf)
            # busca usuário por CPF
            pr = get_admin_client().table("usuarios").select("email").eq("cpf", cpf_digits).single().execute()
            if not pr.data or not pr.data.get("email"):
                return jsonify({"error": "CPF não encontrado"}), 401
            email = pr.data["email"]
        except Exception:
            return jsonify({"error": "CPF inválido"}), 400

    public_client = get_public_client()
    try:
        res = public_client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        # fallback: tenta com admin client se anon não estiver presente
        try:
            admin = get_admin_client()
            res = admin.auth.sign_in_with_password({"email": email, "password": password})
        except Exception as e2:
            return jsonify({"error": f"Falha no login: {e2}"}), 401

    session = getattr(res, "session", None)
    user = getattr(res, "user", None)
    if not session or not user:
        return jsonify({"error": "Credenciais inválidas"}), 401

    user_id = user.id if hasattr(user, "id") else user.get("id")
    # busca perfil (service key; filtra por id)
    profile = None
    try:
        pr = get_admin_client().table("usuarios").select("*").eq("id", user_id).single().execute()
        profile = pr.data
    except Exception:
        profile = None

    # Retorna tokens no corpo e em cookies httpOnly
    resp = attach_session_cookies(
        getattr(session, "access_token", None),
        getattr(session, "refresh_token", None),
        {"user": {"id": user_id, "email": getattr(user, "email", None)}, "profile": profile},
    )
    return resp


@auth_bp.route("/me", methods=["GET"])
@require_auth
def me(user_id: str):
    profile = get_current_user_profile(user_id)
    if not profile:
        return jsonify({"error": "Perfil não encontrado"}), 404
    return jsonify({"user_id": user_id, "profile": profile})


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json(silent=True) or {}
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        return jsonify({"error": "Campo obrigatório: refresh_token"}), 400

    client = get_public_client()
    try:
        # supabase-py v2 aceita string diretamente
        res = client.auth.refresh_session(refresh_token)
    except Exception:
        try:
            # fallback com dict (varia conforme versão)
            res = client.auth.refresh_session({"refresh_token": refresh_token})
        except Exception as e2:
            return jsonify({"error": f"Falha no refresh: {e2}"}), 401

    session = getattr(res, "session", None) or res
    user = getattr(res, "user", None) or getattr(session, "user", None)
    if not session or not user:
        return jsonify({"error": "Refresh inválido"}), 401

    user_id = user.id if hasattr(user, "id") else user.get("id")
    profile = None
    try:
        pr = get_admin_client().table("usuarios").select("*").eq("id", user_id).single().execute()
        profile = pr.data
    except Exception:
        profile = None

    resp = attach_session_cookies(
        getattr(session, "access_token", None),
        getattr(session, "refresh_token", None),
        {"user": {"id": user_id, "email": getattr(user, "email", None)}, "profile": profile},
    )
    return resp


@auth_bp.route("/logout", methods=["POST"])
def logout():
    return clear_session_cookies()
