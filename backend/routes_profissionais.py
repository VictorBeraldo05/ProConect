from typing import Any, Dict, List

from flask import Blueprint, request

from .supabase_client import get_admin_client
from .utils import ok, fail


profissionais_bp = Blueprint("profissionais", __name__, url_prefix="/api/profissionais")


@profissionais_bp.get("")
def listar_profissionais():
    busca = (request.args.get("busca") or "").strip().lower()
    categoria = (request.args.get("categoria") or "").strip()
    localizacao = (request.args.get("localizacao") or "").strip().lower()
    try:
        q = get_admin_client().table("usuarios").select("*").eq("is_worker", True)
        # filtro por categoria (perfil_worker.categorias contém item)
        if categoria:
            q = q.contains("perfil_worker", {"categorias": [categoria]})
        rows: List[Dict[str, Any]] = q.execute().data or []

        def match(p: Dict[str, Any]) -> bool:
            if not rows:
                return False
            if busca:
                nome = (p.get("nome") or "").lower()
                desc = ((p.get("perfil_worker") or {}).get("descricao") or "").lower()
                cats = [(c or "").lower() for c in (p.get("perfil_worker") or {}).get("categorias", [])]
                if not (busca in nome or busca in desc or any(busca in c for c in cats)):
                    return False
            if localizacao:
                cidade = ((p.get("endereco_cidade") or "").lower())
                if localizacao not in cidade:
                    return False
            return True

        filtered = [p for p in rows if match(p)] if (busca or localizacao) else rows
        return ok({"items": filtered})
    except Exception as e:
        return fail(f"Falha ao listar profissionais: {e}", 500)

