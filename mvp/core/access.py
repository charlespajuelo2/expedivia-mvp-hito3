"""Control de acceso mínimo por rol (Etapa 5).

La política vive en ``mvp/etapa5/config/usuarios.json`` y es deliberadamente
simple: un usuario tiene un rol, el rol define permisos y el usuario tiene una
lista de expedientes asignados. El rol ``administrador`` puede acceder a todos.

No sustituye un sistema de identidad: es el mínimo verificable para demostrar
que un usuario sin permiso no accede a un expediente ni ejecuta acciones de
escritura.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import config

ACCIONES = ("ver", "cargar", "analizar", "decidir", "exportar", "administrar")


class AccesoDenegado(PermissionError):
    """El usuario no tiene rol, permiso o expediente asignado."""


@dataclass(frozen=True)
class PoliticaAcceso:
    """Roles, permisos y asignaciones cargados desde JSON."""

    version: str
    ruta: Path
    roles: dict[str, dict[str, Any]]
    usuarios: dict[str, dict[str, Any]]

    # -- Consultas ------------------------------------------------------

    def nombres(self) -> list[str]:
        return sorted(self.usuarios)

    def usuario(self, nombre: str | None) -> dict[str, Any] | None:
        if not nombre:
            return None
        nombre = nombre.strip()
        if nombre in self.usuarios:
            return {"nombre": nombre, **self.usuarios[nombre]}
        # Búsqueda tolerante a mayúsculas para la demostración.
        for existente, datos in self.usuarios.items():
            if existente.casefold() == nombre.casefold():
                return {"nombre": existente, **datos}
        return None

    def rol(self, nombre: str | None) -> str | None:
        usuario = self.usuario(nombre)
        return str(usuario["rol"]) if usuario else None

    def permisos(self, nombre: str | None) -> set[str]:
        usuario = self.usuario(nombre)
        if not usuario:
            return set()
        rol = self.roles.get(str(usuario["rol"]), {})
        return set(rol.get("permisos", []))

    def expedientes(self, nombre: str | None) -> list[str]:
        usuario = self.usuario(nombre)
        if not usuario:
            return []
        return [str(item) for item in usuario.get("expedientes", [])]

    def puede(
        self,
        nombre: str | None,
        accion: str,
        expediente_id: str | None = None,
    ) -> bool:
        """Comprueba permiso y, si se indica, asignación del expediente."""

        usuario = self.usuario(nombre)
        if not usuario:
            return False
        if accion not in self.permisos(nombre):
            return False
        if expediente_id is None:
            return True
        asignados = self.expedientes(nombre)
        if "*" in asignados:
            return True
        return expediente_id in asignados

    def exigir(
        self,
        nombre: str | None,
        accion: str,
        expediente_id: str | None = None,
    ) -> None:
        """Lanza ``AccesoDenegado`` con una causa comprensible."""

        if self.usuario(nombre) is None:
            raise AccesoDenegado(
                f"El usuario «{nombre or 'sin identificar'}» no está registrado "
                "en la política de acceso."
            )
        if accion not in self.permisos(nombre):
            raise AccesoDenegado(
                f"El rol «{self.rol(nombre)}» no tiene el permiso «{accion}»."
            )
        if expediente_id and not self.puede(nombre, accion, expediente_id):
            raise AccesoDenegado(
                f"El usuario «{nombre}» no tiene asignado el expediente "
                f"«{expediente_id}»."
            )

    def a_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "ruta": str(self.ruta),
            "usuarios": [
                {
                    "nombre": nombre,
                    "rol": datos.get("rol"),
                    "permisos": sorted(
                        self.permisos(nombre)
                    ),
                    "expedientes": self.expedientes(nombre),
                }
                for nombre, datos in sorted(self.usuarios.items())
            ],
        }


def cargar_politica(ruta: str | Path | None = None) -> PoliticaAcceso:
    """Carga y valida la política mínima de acceso."""

    ruta = Path(ruta or config.RUTA_USUARIOS)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe la política de acceso: {ruta}")
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    roles = datos.get("roles")
    usuarios = datos.get("usuarios")
    if not isinstance(roles, dict) or not roles:
        raise ValueError("La política no define roles.")
    if not isinstance(usuarios, dict) or not usuarios:
        raise ValueError("La política no define usuarios.")

    for nombre_rol, rol in roles.items():
        permisos = rol.get("permisos")
        if not isinstance(permisos, list):
            raise ValueError(f"El rol {nombre_rol} no define permisos.")
        desconocidos = set(permisos) - set(ACCIONES)
        if desconocidos:
            raise ValueError(
                f"El rol {nombre_rol} tiene permisos desconocidos: "
                + ", ".join(sorted(desconocidos))
            )
    for nombre, usuario in usuarios.items():
        rol = usuario.get("rol")
        if rol not in roles:
            raise ValueError(f"El usuario {nombre} tiene un rol inexistente: {rol}.")
        expedientes = usuario.get("expedientes")
        if not isinstance(expedientes, list) or not expedientes:
            raise ValueError(
                f"El usuario {nombre} debe declarar al menos un expediente o '*'."
            )

    return PoliticaAcceso(
        version=str(datos.get("version", "v1")),
        ruta=ruta,
        roles=roles,
        usuarios=usuarios,
    )


def verificar_acceso(
    usuario: str | None,
    accion: str,
    expediente_id: str | None = None,
    *,
    politica: PoliticaAcceso | None = None,
) -> bool:
    """Atajo booleano para pruebas y pantallas."""

    politica = politica or cargar_politica()
    return politica.puede(usuario, accion, expediente_id)
