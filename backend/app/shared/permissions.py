"""Registo central dos códigos de permissão (`modulo.recurso.accao`).

Cada módulo regista os seus códigos ao ser importado. Os papéis de sistema usam
padrões com `*`, expandidos contra este registo.
"""

from fnmatch import fnmatchcase

PERMISSIONS: dict[str, str] = {}


def register(codes: dict[str, str]) -> None:
    for code, description in codes.items():
        if code.count(".") != 2:
            raise ValueError(f"Código de permissão inválido: {code}")
        PERMISSIONS[code] = description


def expand(patterns: list[str]) -> set[str]:
    return {code for code in PERMISSIONS for p in patterns if fnmatchcase(code, p)}


# Papéis criados em cada nova empresa. Editáveis depois pelo administrador.
SYSTEM_ROLES: dict[str, tuple[str, list[str]]] = {
    "Administrador": ("Acesso total à empresa.", ["*"]),
    "Gestor": (
        "Vê todos os módulos, aprova descontos e anulações.",
        ["*.*.ver", "vendas.*", "stock.*", "facturacao.*", "core.auditoria.ver"],
    ),
    "Vendedor": (
        "Clientes, cotações, encomendas e facturas.",
        ["vendas.*", "facturacao.factura.*"],
    ),
    "Caixa": ("Vendas a dinheiro e recibos no ponto de venda.", ["facturacao.recibo.*"]),
    "Fiel de armazém": ("Movimentos e inventários de stock.", ["stock.*"]),
    "Contabilista": ("Contabilidade e relatórios fiscais.", ["contabilidade.*", "*.*.ver"]),
    "Consulta": ("Apenas leitura.", ["*.*.ver"]),
}
