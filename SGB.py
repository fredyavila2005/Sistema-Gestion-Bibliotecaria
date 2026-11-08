"""SGB — Sistema de Gestión Bibliotecaria (Programación Orientada a Objetos).

Versión en un solo archivo .py del notebook SGB.ipynb.
Ejecutar:  python SGB.py
Los datos se guardan en la carpeta datos/ junto a este archivo
(o en MyDrive/SGB/datos/ si se ejecuta dentro de Google Colab).
"""
import os
import re
from collections import Counter
from datetime import datetime, timedelta
from enum import Enum

# ════════════════════════════════════
# CELDA 0 — Configuración: Drive y rutas
# ════════════════════════════════════
try:
    from google.colab import drive  # type: ignore
    drive.mount('/content/drive')
    RUTA_BASE = '/content/drive/MyDrive/SGB/datos/'
    ENTORNO = 'Colab + Drive'
except ImportError:
    _carpeta = os.path.dirname(os.path.abspath(__file__))
    RUTA_BASE = os.path.join(_carpeta, 'datos', '')
    ENTORNO = 'Local'

os.makedirs(RUTA_BASE, exist_ok=True)

RUTA_USUARIOS = RUTA_BASE + 'usuarios.txt'
RUTA_LIBROS = RUTA_BASE + 'libros.txt'
RUTA_CATEGORIAS = RUTA_BASE + 'categorias.txt'
RUTA_PRESTAMOS = RUTA_BASE + 'prestamos.txt'
RUTA_MULTAS = RUTA_BASE + 'multas.txt'
RUTA_RESERVAS = RUTA_BASE + 'reservas.txt'

# ════════════════════════════════════
# SECCIÓN 1 — MODELO
# ════════════════════════════════════


# CELDA 1.1 — Enums
class TipoUsuarioEnum(Enum):
    """Tipos de usuario de la biblioteca."""
    ESTUDIANTE = 'ESTUDIANTE'
    DOCENTE = 'DOCENTE'
    EXTERNO = 'EXTERNO'


class EstadoPrestamoEnum(Enum):
    """Estados posibles de un préstamo."""
    ACTIVO = 'ACTIVO'
    DEVUELTO = 'DEVUELTO'
    VENCIDO = 'VENCIDO'


class EstadoMultaEnum(Enum):
    """Estados posibles de una multa."""
    PENDIENTE = 'PENDIENTE'
    PAGADA = 'PAGADA'


class EstadoReservaEnum(Enum):
    """Estados posibles de una reserva."""
    ACTIVA = 'ACTIVA'
    CUMPLIDA = 'CUMPLIDA'
    CANCELADA = 'CANCELADA'


# CELDA 1.2 — Clase Usuario
SEPARADOR = '|'
VACIO = 'NINGUNO'


def _validar_campo(valor):
    """Verifica que un campo no contenga el separador '|' ni saltos de línea.

    Retorna el valor convertido a texto. Lanza ValueError si no es válido.
    """
    texto = str(valor)
    if SEPARADOR in texto or '\n' in texto or '\r' in texto:
        raise ValueError(f"El valor '{texto}' no puede contener '|' ni saltos de línea.")
    return texto


class Usuario:
    """Persona que usa la biblioteca (estudiante, docente o externo)."""

    CAMPOS = 6

    def __init__(self, num_documento, nombre, tipo, correo, telefono, estado='ACTIVO'):
        """Crea un usuario.

        tipo debe ser un TipoUsuarioEnum; estado es 'ACTIVO' o 'SUSPENDIDO'.
        """
        self.num_documento = num_documento
        self.nombre = nombre
        self.tipo = tipo
        self.correo = correo
        self.telefono = telefono
        self.estado = estado

    def to_linea(self):
        """Convierte el usuario en una línea de texto para guardar en usuarios.txt."""
        return SEPARADOR.join([
            _validar_campo(self.num_documento),
            _validar_campo(self.nombre),
            self.tipo.value,
            _validar_campo(self.correo),
            _validar_campo(self.telefono),
            _validar_campo(self.estado),
        ])

    @staticmethod
    def from_linea(linea):
        """Crea un Usuario a partir de una línea de usuarios.txt.

        Lanza ValueError si la línea no tiene 6 campos o el tipo no es válido.
        """
        campos = linea.split(SEPARADOR)
        if len(campos) != Usuario.CAMPOS:
            raise ValueError(f'Línea de usuario inválida: {linea!r}')
        doc, nombre, tipo, correo, telefono, estado = campos
        return Usuario(doc, nombre, TipoUsuarioEnum(tipo), correo, telefono, estado)

    def __str__(self):
        """Texto legible del usuario para mostrar en pantalla."""
        return (f'{self.num_documento} | {self.nombre} | {self.tipo.value} | '
                f'{self.correo} | {self.telefono} | {self.estado}')


# CELDA 1.3 — Clase Categoria
class Categoria:
    """Grupo temático de libros (por ejemplo, Literatura o Tecnología)."""

    CAMPOS = 3

    def __init__(self, codigo, nombre, descripcion=None):
        """Crea una categoría. La descripción es opcional (None si no hay)."""
        self.codigo = codigo
        self.nombre = nombre
        self.descripcion = descripcion

    def to_linea(self):
        """Convierte la categoría en una línea para categorias.txt."""
        descripcion = self.descripcion if self.descripcion else VACIO
        return SEPARADOR.join([
            _validar_campo(self.codigo),
            _validar_campo(self.nombre),
            _validar_campo(descripcion),
        ])

    @staticmethod
    def from_linea(linea):
        """Crea una Categoria a partir de una línea de categorias.txt.

        Lanza ValueError si la línea no tiene 3 campos.
        """
        campos = linea.split(SEPARADOR)
        if len(campos) != Categoria.CAMPOS:
            raise ValueError(f'Línea de categoría inválida: {linea!r}')
        codigo, nombre, descripcion = campos
        return Categoria(codigo, nombre, None if descripcion == VACIO else descripcion)

    def __str__(self):
        """Texto legible de la categoría para mostrar en pantalla."""
        return f'{self.codigo} | {self.nombre} | {self.descripcion or "Sin descripción"}'


# CELDA 1.4 — Clase Libro
class Libro:
    """Título del catálogo, con control de ejemplares totales y disponibles."""

    CAMPOS = 7

    def __init__(self, isbn, titulo, autor, cod_categoria, anio, total_ejemplares,
                 disponibles=None):
        """Crea un libro.

        Si no se indica 'disponibles', se asume que todos los ejemplares lo están.
        """
        self.isbn = isbn
        self.titulo = titulo
        self.autor = autor
        self.cod_categoria = cod_categoria
        self.anio = anio
        self.total_ejemplares = total_ejemplares
        self.disponibles = total_ejemplares if disponibles is None else disponibles

    def to_linea(self):
        """Convierte el libro en una línea para libros.txt."""
        return SEPARADOR.join([
            _validar_campo(self.isbn),
            _validar_campo(self.titulo),
            _validar_campo(self.autor),
            _validar_campo(self.cod_categoria),
            str(self.anio),
            str(self.total_ejemplares),
            str(self.disponibles),
        ])

    @staticmethod
    def from_linea(linea):
        """Crea un Libro a partir de una línea de libros.txt.

        Lanza ValueError si la línea no tiene 7 campos o los números no son válidos.
        """
        campos = linea.split(SEPARADOR)
        if len(campos) != Libro.CAMPOS:
            raise ValueError(f'Línea de libro inválida: {linea!r}')
        isbn, titulo, autor, cod_cat, anio, total, disp = campos
        return Libro(isbn, titulo, autor, cod_cat, int(anio), int(total), int(disp))

    def __str__(self):
        """Texto legible del libro para mostrar en pantalla."""
        return (f'{self.isbn} | {self.titulo} | {self.autor} | {self.cod_categoria} | '
                f'{self.anio} | {self.disponibles}/{self.total_ejemplares} disponibles')


# CELDA 1.5 — Clase Prestamo
class Prestamo:
    """Préstamo de un libro a un usuario, con su fecha límite y su estado."""

    CAMPOS = 7

    def __init__(self, codigo, isbn, num_documento, fecha_prestamo, fecha_limite,
                 fecha_devolucion=None, estado=EstadoPrestamoEnum.ACTIVO):
        """Crea un préstamo.

        Las fechas son texto 'AAAA-MM-DD'. fecha_devolucion es None mientras
        el libro no se haya devuelto. estado es un EstadoPrestamoEnum.
        """
        self.codigo = codigo
        self.isbn = isbn
        self.num_documento = num_documento
        self.fecha_prestamo = fecha_prestamo
        self.fecha_limite = fecha_limite
        self.fecha_devolucion = fecha_devolucion
        self.estado = estado

    def to_linea(self):
        """Convierte el préstamo en una línea para prestamos.txt."""
        devolucion = self.fecha_devolucion if self.fecha_devolucion else VACIO
        return SEPARADOR.join([
            _validar_campo(self.codigo),
            _validar_campo(self.isbn),
            _validar_campo(self.num_documento),
            _validar_campo(self.fecha_prestamo),
            _validar_campo(self.fecha_limite),
            _validar_campo(devolucion),
            self.estado.value,
        ])

    @staticmethod
    def from_linea(linea):
        """Crea un Prestamo a partir de una línea de prestamos.txt.

        Lanza ValueError si la línea no tiene 7 campos o el estado no es válido.
        """
        campos = linea.split(SEPARADOR)
        if len(campos) != Prestamo.CAMPOS:
            raise ValueError(f'Línea de préstamo inválida: {linea!r}')
        codigo, isbn, doc, f_prestamo, f_limite, f_devolucion, estado = campos
        return Prestamo(codigo, isbn, doc, f_prestamo, f_limite,
                        None if f_devolucion == VACIO else f_devolucion,
                        EstadoPrestamoEnum(estado))

    def __str__(self):
        """Texto legible del préstamo para mostrar en pantalla."""
        devuelto = self.fecha_devolucion if self.fecha_devolucion else '—'
        return (f'{self.codigo} | libro {self.isbn} | usuario {self.num_documento} | '
                f'prestado {self.fecha_prestamo} | límite {self.fecha_limite} | '
                f'devuelto {devuelto} | {self.estado.value}')


# CELDA 1.6 — Clase Multa
class Multa:
    """Multa generada por devolver un libro después de la fecha límite."""

    CAMPOS = 5

    def __init__(self, codigo, cod_prestamo, dias_retraso, valor,
                 estado=EstadoMultaEnum.PENDIENTE):
        """Crea una multa. valor está en pesos (COP); estado es un EstadoMultaEnum."""
        self.codigo = codigo
        self.cod_prestamo = cod_prestamo
        self.dias_retraso = dias_retraso
        self.valor = valor
        self.estado = estado

    def to_linea(self):
        """Convierte la multa en una línea para multas.txt."""
        return SEPARADOR.join([
            _validar_campo(self.codigo),
            _validar_campo(self.cod_prestamo),
            str(self.dias_retraso),
            str(self.valor),
            self.estado.value,
        ])

    @staticmethod
    def from_linea(linea):
        """Crea una Multa a partir de una línea de multas.txt.

        Lanza ValueError si la línea no tiene 5 campos o los datos no son válidos.
        """
        campos = linea.split(SEPARADOR)
        if len(campos) != Multa.CAMPOS:
            raise ValueError(f'Línea de multa inválida: {linea!r}')
        codigo, cod_prestamo, dias, valor, estado = campos
        return Multa(codigo, cod_prestamo, int(dias), int(valor), EstadoMultaEnum(estado))

    def __str__(self):
        """Texto legible de la multa para mostrar en pantalla."""
        return (f'{self.codigo} | préstamo {self.cod_prestamo} | '
                f'{self.dias_retraso} días | ${self.valor:,} COP | {self.estado.value}')


# CELDA 1.7 — Clase Reserva
class Reserva:
    """Reserva de un libro sin ejemplares disponibles."""

    CAMPOS = 5

    def __init__(self, codigo, isbn, num_documento, fecha_reserva,
                 estado=EstadoReservaEnum.ACTIVA):
        """Crea una reserva. fecha_reserva es 'AAAA-MM-DD'; estado es un EstadoReservaEnum."""
        self.codigo = codigo
        self.isbn = isbn
        self.num_documento = num_documento
        self.fecha_reserva = fecha_reserva
        self.estado = estado

    def to_linea(self):
        """Convierte la reserva en una línea para reservas.txt."""
        return SEPARADOR.join([
            _validar_campo(self.codigo),
            _validar_campo(self.isbn),
            _validar_campo(self.num_documento),
            _validar_campo(self.fecha_reserva),
            self.estado.value,
        ])

    @staticmethod
    def from_linea(linea):
        """Crea una Reserva a partir de una línea de reservas.txt.

        Lanza ValueError si la línea no tiene 5 campos o el estado no es válido.
        """
        campos = linea.split(SEPARADOR)
        if len(campos) != Reserva.CAMPOS:
            raise ValueError(f'Línea de reserva inválida: {linea!r}')
        codigo, isbn, doc, fecha, estado = campos
        return Reserva(codigo, isbn, doc, fecha, EstadoReservaEnum(estado))

    def __str__(self):
        """Texto legible de la reserva para mostrar en pantalla."""
        return (f'{self.codigo} | libro {self.isbn} | usuario {self.num_documento} | '
                f'{self.fecha_reserva} | {self.estado.value}')


# ════════════════════════════════════
# SECCIÓN 2 — REPOSITORIOS
# ════════════════════════════════════


# CELDA 2.1 — ArchivoUtil
class ArchivoUtil:
    """Utilidades para leer y escribir archivos de texto (.txt).

    Cada línea del archivo es un registro. Todos los métodos son estáticos,
    por lo que no hace falta crear un objeto para usarlos.
    """

    @staticmethod
    def existe(ruta):
        """Retorna True si el archivo existe en la ruta indicada."""
        return os.path.isfile(ruta)

    @staticmethod
    def crear_si_no_existe(ruta):
        """Crea un archivo vacío si no existe.

        Retorna True si lo creó y False si ya existía.
        """
        if os.path.isfile(ruta):
            return False
        carpeta = os.path.dirname(ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(ruta, 'a', encoding='utf-8'):
            pass
        return True

    @staticmethod
    def leer_lineas(ruta):
        """Lee todas las líneas no vacías de un archivo.

        Retorna una lista vacía si el archivo no existe.
        """
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return [l.strip() for l in f if l.strip()]
        except FileNotFoundError:
            return []

    @staticmethod
    def escribir_linea(ruta, linea):
        """Agrega una línea al final del archivo.

        Lanza ValueError si la línea contiene saltos de línea, porque
        rompería la regla de un registro por línea.
        """
        if '\n' in linea or '\r' in linea:
            raise ValueError('La línea no puede contener saltos de línea.')
        with open(ruta, 'a', encoding='utf-8') as f:
            f.write(linea + '\n')

    @staticmethod
    def reescribir(ruta, lineas):
        """Reemplaza el contenido completo del archivo con las líneas dadas.

        Si la lista está vacía, deja el archivo vacío.
        """
        with open(ruta, 'w', encoding='utf-8') as f:
            if lineas:
                f.write('\n'.join(lineas) + '\n')

    @staticmethod
    def generar_codigo(prefijo):
        """Genera un código único basado en la fecha y hora actuales.

        Ejemplo: generar_codigo('PRE') -> 'PRE-20251015083000123'
        """
        ts = datetime.now().strftime('%Y%m%d%H%M%S%f')[:17]
        return f'{prefijo}-{ts}'


# CELDA 2.2 — UsuarioRepository
class UsuarioRepository:
    """Guarda y consulta usuarios en usuarios.txt."""

    def __init__(self, ruta):
        """Recibe la ruta del archivo de usuarios (RUTA_USUARIOS)."""
        self.ruta = ruta

    def guardar(self, u):
        """Agrega un usuario nuevo al final del archivo."""
        ArchivoUtil.escribir_linea(self.ruta, u.to_linea())

    def find_by_documento(self, doc):
        """Busca un usuario por número de documento. Retorna Usuario o None."""
        for u in self.find_all():
            if u.num_documento == doc:
                return u
        return None

    def find_all(self):
        """Retorna la lista de todos los usuarios registrados."""
        return [Usuario.from_linea(l) for l in ArchivoUtil.leer_lineas(self.ruta)]

    def actualizar(self, u):
        """Reemplaza los datos del usuario que tenga el mismo documento.

        Retorna True si lo encontró y actualizó, False si no existe.
        """
        usuarios = self.find_all()
        encontrado = False
        for i, existente in enumerate(usuarios):
            if existente.num_documento == u.num_documento:
                usuarios[i] = u
                encontrado = True
                break
        if encontrado:
            ArchivoUtil.reescribir(self.ruta, [x.to_linea() for x in usuarios])
        return encontrado


# CELDA 2.3 — CategoriaRepository
class CategoriaRepository:
    """Guarda y consulta categorías en categorias.txt."""

    def __init__(self, ruta):
        """Recibe la ruta del archivo de categorías (RUTA_CATEGORIAS)."""
        self.ruta = ruta

    def guardar(self, c):
        """Agrega una categoría nueva al final del archivo."""
        ArchivoUtil.escribir_linea(self.ruta, c.to_linea())

    def find_by_codigo(self, cod):
        """Busca una categoría por código. Retorna Categoria o None."""
        for c in self.find_all():
            if c.codigo == cod:
                return c
        return None

    def find_all(self):
        """Retorna la lista de todas las categorías."""
        return [Categoria.from_linea(l) for l in ArchivoUtil.leer_lineas(self.ruta)]


# CELDA 2.4 — LibroRepository
class LibroRepository:
    """Guarda y consulta libros en libros.txt."""

    def __init__(self, ruta):
        """Recibe la ruta del archivo de libros (RUTA_LIBROS)."""
        self.ruta = ruta

    def guardar(self, l):
        """Agrega un libro nuevo al final del archivo."""
        ArchivoUtil.escribir_linea(self.ruta, l.to_linea())

    def find_all(self):
        """Retorna la lista de todos los libros del catálogo."""
        return [Libro.from_linea(x) for x in ArchivoUtil.leer_lineas(self.ruta)]

    def find_by_isbn(self, isbn):
        """Busca un libro por ISBN. Retorna Libro o None."""
        for l in self.find_all():
            if l.isbn == isbn:
                return l
        return None

    def find_by_titulo(self, txt):
        """Retorna los libros cuyo título contiene el texto (sin distinguir mayúsculas)."""
        txt = txt.lower()
        return [l for l in self.find_all() if txt in l.titulo.lower()]

    def find_by_categoria(self, cod):
        """Retorna los libros de la categoría con ese código."""
        return [l for l in self.find_all() if l.cod_categoria == cod]

    def actualizar(self, l):
        """Reemplaza los datos del libro que tenga el mismo ISBN.

        Retorna True si lo encontró y actualizó, False si no existe.
        """
        libros = self.find_all()
        encontrado = False
        for i, existente in enumerate(libros):
            if existente.isbn == l.isbn:
                libros[i] = l
                encontrado = True
                break
        if encontrado:
            ArchivoUtil.reescribir(self.ruta, [x.to_linea() for x in libros])
        return encontrado


# CELDA 2.5 — PrestamoRepository
class PrestamoRepository:
    """Guarda y consulta préstamos en prestamos.txt."""

    def __init__(self, ruta):
        """Recibe la ruta del archivo de préstamos (RUTA_PRESTAMOS)."""
        self.ruta = ruta

    def guardar(self, p):
        """Agrega un préstamo nuevo al final del archivo."""
        ArchivoUtil.escribir_linea(self.ruta, p.to_linea())

    def find_all(self):
        """Retorna la lista de todos los préstamos registrados."""
        return [Prestamo.from_linea(l) for l in ArchivoUtil.leer_lineas(self.ruta)]

    def find_by_codigo(self, cod):
        """Busca un préstamo por código. Retorna Prestamo o None."""
        for p in self.find_all():
            if p.codigo == cod:
                return p
        return None

    def find_by_usuario(self, doc):
        """Retorna los préstamos de un usuario (por número de documento)."""
        return [p for p in self.find_all() if p.num_documento == doc]

    def find_by_libro(self, isbn):
        """Retorna los préstamos de un libro (por ISBN)."""
        return [p for p in self.find_all() if p.isbn == isbn]

    def actualizar(self, p):
        """Reemplaza los datos del préstamo que tenga el mismo código.

        Retorna True si lo encontró y actualizó, False si no existe.
        """
        prestamos = self.find_all()
        encontrado = False
        for i, existente in enumerate(prestamos):
            if existente.codigo == p.codigo:
                prestamos[i] = p
                encontrado = True
                break
        if encontrado:
            ArchivoUtil.reescribir(self.ruta, [x.to_linea() for x in prestamos])
        return encontrado


# CELDA 2.6 — MultaRepository
class MultaRepository:
    """Guarda y consulta multas en multas.txt."""

    def __init__(self, ruta, repo_prestamos):
        """Recibe la ruta de multas (RUTA_MULTAS) y el PrestamoRepository.

        El repositorio de préstamos sirve para saber de qué usuario es cada multa.
        """
        self.ruta = ruta
        self.repo_prestamos = repo_prestamos

    def guardar(self, m):
        """Agrega una multa nueva al final del archivo."""
        ArchivoUtil.escribir_linea(self.ruta, m.to_linea())

    def find_all(self):
        """Retorna la lista de todas las multas."""
        return [Multa.from_linea(l) for l in ArchivoUtil.leer_lineas(self.ruta)]

    def find_by_codigo(self, cod):
        """Busca una multa por su código. Retorna Multa o None."""
        for m in self.find_all():
            if m.codigo == cod:
                return m
        return None

    def find_by_prestamo(self, cod):
        """Busca la multa asociada a un préstamo. Retorna Multa o None."""
        for m in self.find_all():
            if m.cod_prestamo == cod:
                return m
        return None

    def find_pendientes_usuario(self, doc):
        """Retorna las multas PENDIENTES de un usuario (por documento)."""
        codigos = {p.codigo for p in self.repo_prestamos.find_by_usuario(doc)}
        return [m for m in self.find_all()
                if m.cod_prestamo in codigos and m.estado == EstadoMultaEnum.PENDIENTE]

    def actualizar_estado(self, cod, estado):
        """Cambia el estado de la multa con ese código.

        Retorna True si la encontró y actualizó, False si no existe.
        """
        multas = self.find_all()
        encontrada = False
        for m in multas:
            if m.codigo == cod:
                m.estado = estado
                encontrada = True
                break
        if encontrada:
            ArchivoUtil.reescribir(self.ruta, [x.to_linea() for x in multas])
        return encontrada


# CELDA 2.7 — ReservaRepository
class ReservaRepository:
    """Guarda y consulta reservas en reservas.txt."""

    def __init__(self, ruta):
        """Recibe la ruta del archivo de reservas (RUTA_RESERVAS)."""
        self.ruta = ruta

    def guardar(self, r):
        """Agrega una reserva nueva al final del archivo."""
        ArchivoUtil.escribir_linea(self.ruta, r.to_linea())

    def find_all(self):
        """Retorna la lista de todas las reservas."""
        return [Reserva.from_linea(l) for l in ArchivoUtil.leer_lineas(self.ruta)]

    def find_by_codigo(self, cod):
        """Busca una reserva por su código. Retorna Reserva o None."""
        for r in self.find_all():
            if r.codigo == cod:
                return r
        return None

    def find_by_libro(self, isbn):
        """Retorna las reservas de un libro, en orden de llegada."""
        return [r for r in self.find_all() if r.isbn == isbn]

    def actualizar_estado(self, cod, estado):
        """Cambia el estado de la reserva con ese código.

        Retorna True si la encontró y actualizó, False si no existe.
        """
        reservas = self.find_all()
        encontrada = False
        for r in reservas:
            if r.codigo == cod:
                r.estado = estado
                encontrada = True
                break
        if encontrada:
            ArchivoUtil.reescribir(self.ruta, [x.to_linea() for x in reservas])
        return encontrada


# ════════════════════════════════════
# SECCIÓN 3 — SERVICIOS
# ════════════════════════════════════

ESTADOS_USUARIO = ('ACTIVO', 'SUSPENDIDO')
PATRON_CORREO = r'[^@\s|]+@[^@\s|]+\.[^@\s|]+'


# CELDA 3.1 — UsuarioService
class UsuarioService:
    """Reglas de negocio para la gestión de usuarios (RF-01)."""

    def __init__(self, repo_usuarios):
        """Recibe el UsuarioRepository que usará para guardar y consultar."""
        self.repo = repo_usuarios

    def registrar(self, num_documento, nombre, tipo, correo, telefono):
        """Registra un usuario nuevo con estado ACTIVO.

        tipo debe ser un TipoUsuarioEnum. Lanza ValueError si algún dato es
        inválido o si el documento ya está registrado. Retorna el Usuario creado.
        """
        num_documento = num_documento.strip()
        nombre = nombre.strip()
        correo = correo.strip()
        telefono = telefono.strip()

        if not num_documento.isdigit():
            raise ValueError('El documento debe contener solo números.')
        if not nombre:
            raise ValueError('El nombre no puede estar vacío.')
        if not isinstance(tipo, TipoUsuarioEnum):
            raise ValueError('El tipo de usuario no es válido.')
        if not re.fullmatch(PATRON_CORREO, correo):
            raise ValueError('El correo no tiene un formato válido.')
        if not telefono.isdigit():
            raise ValueError('El teléfono debe contener solo números.')
        if self.repo.find_by_documento(num_documento) is not None:
            raise ValueError(f'Ya existe un usuario con el documento {num_documento}.')

        usuario = Usuario(num_documento, nombre, tipo, correo, telefono, 'ACTIVO')
        self.repo.guardar(usuario)
        return usuario

    def buscar_por_documento(self, doc):
        """Retorna el Usuario con ese documento, o None si no existe."""
        return self.repo.find_by_documento(doc.strip())

    def actualizar(self, doc, correo=None, telefono=None, estado=None):
        """Actualiza correo, teléfono y/o estado de un usuario existente.

        Solo cambia los datos que se indiquen (los que sean None se conservan).
        Lanza ValueError si el usuario no existe o algún dato es inválido.
        Retorna el Usuario actualizado.
        """
        usuario = self.repo.find_by_documento(doc.strip())
        if usuario is None:
            raise ValueError(f'No existe un usuario con el documento {doc}.')

        if correo is not None:
            correo = correo.strip()
            if not re.fullmatch(PATRON_CORREO, correo):
                raise ValueError('El correo no tiene un formato válido.')
            usuario.correo = correo
        if telefono is not None:
            telefono = telefono.strip()
            if not telefono.isdigit():
                raise ValueError('El teléfono debe contener solo números.')
            usuario.telefono = telefono
        if estado is not None:
            estado = estado.strip().upper()
            if estado not in ESTADOS_USUARIO:
                raise ValueError('El estado debe ser ACTIVO o SUSPENDIDO.')
            usuario.estado = estado

        self.repo.actualizar(usuario)
        return usuario

    def listar_todos(self):
        """Retorna la lista de todos los usuarios registrados."""
        return self.repo.find_all()


# CELDA 3.2 — LibroService
class LibroService:
    """Reglas de negocio para el catálogo de libros y categorías (RF-02)."""

    def __init__(self, repo_libros, repo_categorias):
        """Recibe el LibroRepository y el CategoriaRepository."""
        self.repo_libros = repo_libros
        self.repo_categorias = repo_categorias

    def registrar_categoria(self, codigo, nombre, descripcion=None):
        """Registra una categoría nueva.

        Lanza ValueError si faltan datos o el código ya existe.
        Retorna la Categoria creada.
        """
        codigo = codigo.strip().upper()
        nombre = nombre.strip()
        descripcion = descripcion.strip() if descripcion else None

        if not codigo:
            raise ValueError('El código de la categoría no puede estar vacío.')
        if not nombre:
            raise ValueError('El nombre de la categoría no puede estar vacío.')
        if self.repo_categorias.find_by_codigo(codigo) is not None:
            raise ValueError(f'Ya existe la categoría con código {codigo}.')

        categoria = Categoria(codigo, nombre, descripcion or None)
        self.repo_categorias.guardar(categoria)
        return categoria

    def listar_categorias(self):
        """Retorna la lista de todas las categorías registradas."""
        return self.repo_categorias.find_all()

    def registrar(self, isbn, titulo, autor, cod_categoria, anio, total_ejemplares):
        """Registra un libro nuevo con todos sus ejemplares disponibles.

        Lanza ValueError si algún dato es inválido, la categoría no existe
        o el ISBN ya está registrado. Retorna el Libro creado.
        """
        isbn = isbn.strip()
        titulo = titulo.strip()
        autor = autor.strip()
        cod_categoria = cod_categoria.strip().upper()

        if not isbn:
            raise ValueError('El ISBN no puede estar vacío.')
        if not titulo:
            raise ValueError('El título no puede estar vacío.')
        if not autor:
            raise ValueError('El autor no puede estar vacío.')
        if self.repo_categorias.find_by_codigo(cod_categoria) is None:
            raise ValueError(f'La categoría {cod_categoria} no existe. Regístrala primero.')
        if not isinstance(anio, int) or not (1000 <= anio <= 2100):
            raise ValueError('El año de publicación no es válido.')
        if not isinstance(total_ejemplares, int) or total_ejemplares < 1:
            raise ValueError('El número de ejemplares debe ser al menos 1.')
        if self.repo_libros.find_by_isbn(isbn) is not None:
            raise ValueError(f'Ya existe un libro con el ISBN {isbn}.')

        libro = Libro(isbn, titulo, autor, cod_categoria, anio, total_ejemplares)
        self.repo_libros.guardar(libro)
        return libro

    def buscar_por_isbn(self, isbn):
        """Retorna el Libro con ese ISBN, o None si no existe."""
        return self.repo_libros.find_by_isbn(isbn.strip())

    def buscar_por_titulo(self, txt):
        """Retorna los libros cuyo título contiene el texto indicado."""
        return self.repo_libros.find_by_titulo(txt.strip())

    def listar_por_categoria(self, cod):
        """Retorna los libros de una categoría."""
        return self.repo_libros.find_by_categoria(cod.strip().upper())

    def listar_disponibles(self):
        """Retorna los libros que tienen al menos un ejemplar disponible."""
        return [l for l in self.repo_libros.find_all() if l.disponibles > 0]


# CELDA 3.3 — PrestamoService
FORMATO_FECHA = '%Y-%m-%d'

DIAS_PRESTAMO = {
    TipoUsuarioEnum.ESTUDIANTE: 7,
    TipoUsuarioEnum.DOCENTE: 15,
    TipoUsuarioEnum.EXTERNO: 5,
}

CUPO_PRESTAMOS = {
    TipoUsuarioEnum.ESTUDIANTE: 3,
    TipoUsuarioEnum.DOCENTE: 5,
    TipoUsuarioEnum.EXTERNO: 2,
}


class PrestamoService:
    """Reglas de negocio para préstamos y devoluciones (RF-03)."""

    def __init__(self, repo_prestamos, repo_usuarios, repo_libros,
                 repo_multas=None, multa_service=None, reserva_service=None):
        """Recibe los repositorios y servicios que necesita.

        repo_multas valida multas pendientes al prestar. multa_service calcula
        la multa al devolver con retraso. reserva_service atiende la siguiente
        reserva al devolver. Los tres son opcionales (None = no se aplican).
        """
        self.repo_prestamos = repo_prestamos
        self.repo_usuarios = repo_usuarios
        self.repo_libros = repo_libros
        self.repo_multas = repo_multas
        self.multa_service = multa_service
        self.reserva_service = reserva_service
        self.ultima_multa = None

    @staticmethod
    def _parsear_fecha(texto):
        """Convierte 'AAAA-MM-DD' en datetime. Lanza ValueError si es inválida."""
        try:
            return datetime.strptime(texto.strip(), FORMATO_FECHA)
        except ValueError:
            raise ValueError('Fecha inválida. Usa el formato AAAA-MM-DD.')

    def _prestamos_sin_devolver(self, doc):
        """Retorna los préstamos del usuario que siguen ACTIVO o VENCIDO."""
        return [p for p in self.repo_prestamos.find_by_usuario(doc)
                if p.estado != EstadoPrestamoEnum.DEVUELTO]

    def prestar(self, num_documento, isbn, fecha_prestamo):
        """Registra un préstamo y descuenta un ejemplar disponible.

        Valida: usuario existente y ACTIVO, sin multas pendientes, cupo
        disponible, libro existente con ejemplares y que el usuario no tenga
        ya ese libro. Calcula la fecha límite según el tipo de usuario.
        Lanza ValueError si alguna regla falla. Retorna el Prestamo creado.
        """
        num_documento = num_documento.strip()
        isbn = isbn.strip()
        inicio = self._parsear_fecha(fecha_prestamo)

        usuario = self.repo_usuarios.find_by_documento(num_documento)
        if usuario is None:
            raise ValueError(f'No existe un usuario con el documento {num_documento}.')
        if usuario.estado != 'ACTIVO':
            raise ValueError('El usuario no está activo.')

        if self.repo_multas is not None:
            if self.repo_multas.find_pendientes_usuario(num_documento):
                raise ValueError('El usuario tiene multas pendientes.')

        pendientes = self._prestamos_sin_devolver(num_documento)
        cupo = CUPO_PRESTAMOS[usuario.tipo]
        if len(pendientes) >= cupo:
            raise ValueError(f'El usuario alcanzó su cupo de {cupo} libros.')

        libro = self.repo_libros.find_by_isbn(isbn)
        if libro is None:
            raise ValueError(f'No existe un libro con el ISBN {isbn}.')
        if libro.disponibles < 1:
            raise ValueError('No hay ejemplares disponibles de ese libro.')
        if any(p.isbn == isbn for p in pendientes):
            raise ValueError('El usuario ya tiene prestado ese libro.')

        limite = inicio + timedelta(days=DIAS_PRESTAMO[usuario.tipo])
        prestamo = Prestamo(ArchivoUtil.generar_codigo('PRE'), isbn, num_documento,
                            inicio.strftime(FORMATO_FECHA), limite.strftime(FORMATO_FECHA))
        self.repo_prestamos.guardar(prestamo)

        libro.disponibles -= 1
        self.repo_libros.actualizar(libro)
        return prestamo

    def devolver(self, codigo, fecha_devolucion):
        """Registra la devolución de un préstamo y libera el ejemplar.

        Lanza ValueError si el préstamo no existe, ya fue devuelto o la fecha
        es anterior a la del préstamo. Retorna el Prestamo actualizado.
        Si hay retraso, crea la multa (queda en ultima_multa).
        """
        prestamo = self.repo_prestamos.find_by_codigo(codigo.strip())
        if prestamo is None:
            raise ValueError(f'No existe un préstamo con el código {codigo}.')
        if prestamo.estado == EstadoPrestamoEnum.DEVUELTO:
            raise ValueError('Ese préstamo ya fue devuelto.')

        fecha = self._parsear_fecha(fecha_devolucion)
        if fecha < self._parsear_fecha(prestamo.fecha_prestamo):
            raise ValueError('La devolución no puede ser anterior al préstamo.')

        prestamo.fecha_devolucion = fecha.strftime(FORMATO_FECHA)
        prestamo.estado = EstadoPrestamoEnum.DEVUELTO
        self.repo_prestamos.actualizar(prestamo)

        libro = self.repo_libros.find_by_isbn(prestamo.isbn)
        if libro is not None:
            libro.disponibles = min(libro.disponibles + 1, libro.total_ejemplares)
            self.repo_libros.actualizar(libro)

        self.ultima_multa = None
        if self.multa_service is not None:
            self.ultima_multa = self.multa_service.calcular_multa(prestamo)
        if self.reserva_service is not None:
            self.reserva_service.cumplir_siguiente(prestamo.isbn)
        return prestamo

    def buscar_por_codigo(self, codigo):
        """Retorna el Prestamo con ese código, o None si no existe."""
        return self.repo_prestamos.find_by_codigo(codigo.strip())

    def historial_usuario(self, doc):
        """Retorna todos los préstamos de un usuario, en orden cronológico."""
        prestamos = self.repo_prestamos.find_by_usuario(doc.strip())
        return sorted(prestamos, key=lambda p: (p.fecha_prestamo, p.codigo))

    def listar_vencidos(self, fecha):
        """Retorna los préstamos vencidos a la fecha dada ('AAAA-MM-DD').

        Un préstamo no devuelto cuya fecha límite es anterior a esa fecha se
        marca como VENCIDO y se guarda el cambio en el archivo.
        """
        corte = self._parsear_fecha(fecha)
        vencidos = []
        for p in self.repo_prestamos.find_all():
            if p.estado == EstadoPrestamoEnum.DEVUELTO:
                continue
            if self._parsear_fecha(p.fecha_limite) < corte:
                if p.estado != EstadoPrestamoEnum.VENCIDO:
                    p.estado = EstadoPrestamoEnum.VENCIDO
                    self.repo_prestamos.actualizar(p)
                vencidos.append(p)
        return vencidos


# CELDA 3.4 — MultaService
VALOR_MULTA_DIA = 1000  # COP por cada día de retraso


class MultaService:
    """Reglas de negocio para multas por retraso (RF-04)."""

    def __init__(self, repo_multas, repo_prestamos):
        """Recibe el MultaRepository y el PrestamoRepository."""
        self.repo_multas = repo_multas
        self.repo_prestamos = repo_prestamos

    def calcular_multa(self, prestamo):
        """Calcula y guarda la multa de un préstamo devuelto con retraso.

        Cobra COP 1.000 por cada día después de la fecha límite. Retorna la
        Multa creada, o None si se devolvió a tiempo. Si el préstamo ya tiene
        multa, retorna la existente (no la duplica). Lanza ValueError si el
        préstamo aún no se ha devuelto.
        """
        if not prestamo.fecha_devolucion:
            raise ValueError('El préstamo aún no ha sido devuelto.')

        existente = self.repo_multas.find_by_prestamo(prestamo.codigo)
        if existente is not None:
            return existente

        devolucion = datetime.strptime(prestamo.fecha_devolucion, FORMATO_FECHA)
        limite = datetime.strptime(prestamo.fecha_limite, FORMATO_FECHA)
        dias = (devolucion - limite).days
        if dias <= 0:
            return None

        multa = Multa(ArchivoUtil.generar_codigo('MUL'), prestamo.codigo,
                      dias, dias * VALOR_MULTA_DIA)
        self.repo_multas.guardar(multa)
        return multa

    def pagar(self, cod_multa):
        """Registra el pago de una multa pendiente.

        Lanza ValueError si la multa no existe o ya fue pagada.
        Retorna la Multa actualizada.
        """
        multa = self.repo_multas.find_by_codigo(cod_multa.strip())
        if multa is None:
            raise ValueError(f'No existe una multa con el código {cod_multa}.')
        if multa.estado == EstadoMultaEnum.PAGADA:
            raise ValueError('Esa multa ya fue pagada.')
        self.repo_multas.actualizar_estado(multa.codigo, EstadoMultaEnum.PAGADA)
        multa.estado = EstadoMultaEnum.PAGADA
        return multa

    def listar_pendientes_usuario(self, doc):
        """Retorna las multas PENDIENTES de un usuario (por documento)."""
        return self.repo_multas.find_pendientes_usuario(doc.strip())


# CELDA 3.5 — ReservaService
class ReservaService:
    """Reglas de negocio para reservas de libros sin disponibilidad (RF-04)."""

    def __init__(self, repo_reservas, repo_usuarios, repo_libros):
        """Recibe los repositorios de reservas, usuarios y libros."""
        self.repo_reservas = repo_reservas
        self.repo_usuarios = repo_usuarios
        self.repo_libros = repo_libros

    def reservar(self, num_documento, isbn, fecha_reserva):
        """Reserva un libro que no tiene ejemplares disponibles.

        Lanza ValueError si el usuario no existe o no está activo, el libro no
        existe, aún tiene ejemplares disponibles, la fecha es inválida o el
        usuario ya tiene una reserva ACTIVA de ese libro. Retorna la Reserva.
        """
        num_documento = num_documento.strip()
        isbn = isbn.strip()
        try:
            datetime.strptime(fecha_reserva.strip(), FORMATO_FECHA)
        except ValueError:
            raise ValueError('Fecha inválida. Usa el formato AAAA-MM-DD.')

        usuario = self.repo_usuarios.find_by_documento(num_documento)
        if usuario is None:
            raise ValueError(f'No existe un usuario con el documento {num_documento}.')
        if usuario.estado != 'ACTIVO':
            raise ValueError('El usuario no está activo.')

        libro = self.repo_libros.find_by_isbn(isbn)
        if libro is None:
            raise ValueError(f'No existe un libro con el ISBN {isbn}.')
        if libro.disponibles > 0:
            raise ValueError('El libro tiene ejemplares disponibles: puedes prestarlo.')

        for r in self.repo_reservas.find_by_libro(isbn):
            if r.num_documento == num_documento and r.estado == EstadoReservaEnum.ACTIVA:
                raise ValueError('El usuario ya tiene una reserva activa de ese libro.')

        reserva = Reserva(ArchivoUtil.generar_codigo('RES'), isbn, num_documento,
                          fecha_reserva.strip())
        self.repo_reservas.guardar(reserva)
        return reserva

    def cancelar(self, codigo):
        """Cancela una reserva ACTIVA.

        Lanza ValueError si no existe o ya no está activa.
        Retorna la Reserva actualizada.
        """
        reserva = self.repo_reservas.find_by_codigo(codigo.strip())
        if reserva is None:
            raise ValueError(f'No existe una reserva con el código {codigo}.')
        if reserva.estado != EstadoReservaEnum.ACTIVA:
            raise ValueError('Solo se pueden cancelar reservas activas.')
        self.repo_reservas.actualizar_estado(reserva.codigo, EstadoReservaEnum.CANCELADA)
        reserva.estado = EstadoReservaEnum.CANCELADA
        return reserva

    def listar_por_libro(self, isbn):
        """Retorna las reservas de un libro, en orden de llegada."""
        return self.repo_reservas.find_by_libro(isbn.strip())

    def cumplir_siguiente(self, isbn):
        """Marca como CUMPLIDA la reserva ACTIVA más antigua de un libro.

        Se usa al devolver un libro: se atiende por orden de llegada.
        Retorna la Reserva cumplida, o None si no había reservas activas.
        """
        for r in self.repo_reservas.find_by_libro(isbn):
            if r.estado == EstadoReservaEnum.ACTIVA:
                self.repo_reservas.actualizar_estado(r.codigo, EstadoReservaEnum.CUMPLIDA)
                r.estado = EstadoReservaEnum.CUMPLIDA
                return r
        return None


# CELDA 3.6 — AnalisisDatosService
class AnalisisDatosService:
    """Genera indicadores estadísticos a partir de los archivos de datos (RF-05)."""

    def __init__(self, ruta_prestamos, ruta_libros, ruta_categorias,
                 ruta_usuarios, ruta_multas):
        """Recibe las rutas de los archivos .txt que se analizan."""
        self.ruta_prestamos = ruta_prestamos
        self.ruta_libros = ruta_libros
        self.ruta_categorias = ruta_categorias
        self.ruta_usuarios = ruta_usuarios
        self.ruta_multas = ruta_multas

    @staticmethod
    def _fecha(texto):
        """Convierte 'AAAA-MM-DD' en datetime. Lanza ValueError si es inválida."""
        try:
            return datetime.strptime(texto.strip(), '%Y-%m-%d')
        except ValueError:
            raise ValueError('Fecha inválida. Usa el formato AAAA-MM-DD.')

    def libros_mas_prestados(self, fecha_ini, fecha_fin, top_n=10):
        """Retorna los N libros más prestados entre dos fechas (inclusive).

        Cada elemento es una tupla (isbn, titulo, veces_prestado), ordenada
        de mayor a menor. Las fechas se reciben como texto 'AAAA-MM-DD'.
        """
        ini = self._fecha(fecha_ini)
        fin = self._fecha(fecha_fin)
        if ini > fin:
            raise ValueError('La fecha inicial no puede ser posterior a la final.')

        titulos = {}
        for linea in ArchivoUtil.leer_lineas(self.ruta_libros):
            campos = linea.split('|')
            titulos[campos[0]] = campos[1]

        contador = Counter()
        for linea in ArchivoUtil.leer_lineas(self.ruta_prestamos):
            campos = linea.split('|')
            fecha = datetime.strptime(campos[3], '%Y-%m-%d')
            if ini <= fecha <= fin:
                contador[campos[1]] += 1

        return [(isbn, titulos.get(isbn, 'Desconocido'), n)
                for isbn, n in contador.most_common(top_n)]

    def prestamos_por_categoria(self):
        """Retorna la distribución de préstamos por categoría.

        Lista de tuplas (cod_categoria, nombre, cantidad, porcentaje),
        ordenada de mayor a menor cantidad. El porcentaje es sobre el total
        de préstamos.
        """
        categoria_de_libro = {}
        for linea in ArchivoUtil.leer_lineas(self.ruta_libros):
            campos = linea.split('|')
            categoria_de_libro[campos[0]] = campos[3]

        nombres = {}
        for linea in ArchivoUtil.leer_lineas(self.ruta_categorias):
            campos = linea.split('|')
            nombres[campos[0]] = campos[1]

        contador = Counter()
        total = 0
        for linea in ArchivoUtil.leer_lineas(self.ruta_prestamos):
            isbn = linea.split('|')[1]
            contador[categoria_de_libro.get(isbn, 'SIN-CATEGORIA')] += 1
            total += 1

        if total == 0:
            return []
        return [(cod, nombres.get(cod, 'Desconocida'), n, round(n * 100 / total, 1))
                for cod, n in contador.most_common()]

    def morosidad_por_tipo(self, fecha_corte=None):
        """Retorna la tasa de morosidad por tipo de usuario.

        Un préstamo es moroso si está VENCIDO, si se devolvió después de la
        fecha límite, o si no se ha devuelto y su fecha límite ya pasó a la
        fecha de corte (por defecto, hoy). Retorna un diccionario
        {tipo: (total, morosos, tasa_porcentaje)} con los tres tipos.
        """
        corte = self._fecha(fecha_corte) if fecha_corte else datetime.now()

        tipo_de_usuario = {}
        for linea in ArchivoUtil.leer_lineas(self.ruta_usuarios):
            campos = linea.split('|')
            tipo_de_usuario[campos[0]] = campos[2]

        totales = {t.value: 0 for t in TipoUsuarioEnum}
        morosos = {t.value: 0 for t in TipoUsuarioEnum}

        for linea in ArchivoUtil.leer_lineas(self.ruta_prestamos):
            campos = linea.split('|')
            tipo = tipo_de_usuario.get(campos[2])
            if tipo not in totales:
                continue
            totales[tipo] += 1

            limite = datetime.strptime(campos[4], '%Y-%m-%d')
            estado = campos[6]
            if estado == 'VENCIDO':
                es_moroso = True
            elif estado == 'DEVUELTO':
                devolucion = datetime.strptime(campos[5], '%Y-%m-%d')
                es_moroso = devolucion > limite
            else:
                es_moroso = limite < corte
            if es_moroso:
                morosos[tipo] += 1

        return {t: (totales[t], morosos[t],
                    round(morosos[t] * 100 / totales[t], 1) if totales[t] else 0.0)
                for t in totales}

    def duracion_promedio_prestamo(self):
        """Retorna la duración promedio real (en días) de los préstamos devueltos.

        Promedio = suma de días entre fecha_prestamo y fecha_devolucion
        dividida entre el número de préstamos devueltos. Retorna una tupla
        (promedio, cantidad_devueltos); el promedio es 0.0 si no hay devueltos.
        """
        suma = 0
        cantidad = 0
        for linea in ArchivoUtil.leer_lineas(self.ruta_prestamos):
            campos = linea.split('|')
            if campos[6] != 'DEVUELTO':
                continue
            prestamo = datetime.strptime(campos[3], '%Y-%m-%d')
            devolucion = datetime.strptime(campos[5], '%Y-%m-%d')
            suma += (devolucion - prestamo).days
            cantidad += 1
        if cantidad == 0:
            return (0.0, 0)
        return (round(suma / cantidad, 2), cantidad)

    def reporte_multas(self):
        """Retorna el reporte financiero de multas.

        Diccionario con 'generado', 'pagado' y 'pendiente' (valores en COP)
        y 'cantidad' de multas.
        """
        generado = pagado = pendiente = cantidad = 0
        for linea in ArchivoUtil.leer_lineas(self.ruta_multas):
            campos = linea.split('|')
            valor = int(campos[3])
            generado += valor
            cantidad += 1
            if campos[4] == 'PAGADA':
                pagado += valor
            else:
                pendiente += valor
        return {'generado': generado, 'pagado': pagado,
                'pendiente': pendiente, 'cantidad': cantidad}


# ════════════════════════════════════
# SECCIÓN 4 — INTERFAZ DE USUARIO
# ════════════════════════════════════


# CELDA 4.0 — Funciones auxiliares de consola
def limpiar_pantalla():
    """Separa visualmente las pantallas imprimiendo líneas en blanco."""
    print('\n' * 2)


def leer_texto(mensaje, obligatorio=True):
    """Pide un texto por consola.

    Si es obligatorio, repite la pregunta hasta que no esté vacío.
    Si no lo es, retorna '' cuando el usuario solo presiona Enter.
    """
    while True:
        valor = input(mensaje).strip()
        if valor or not obligatorio:
            return valor
        print('  ✘ Este dato es obligatorio.')


def leer_entero(mensaje, minimo=None, maximo=None):
    """Pide un número entero por consola.

    Repite la pregunta si no es un entero o está fuera del rango indicado.
    """
    while True:
        valor = input(mensaje).strip()
        try:
            numero = int(valor)
        except ValueError:
            print('  ✘ Escribe un número entero.')
            continue
        if minimo is not None and numero < minimo:
            print(f'  ✘ El valor mínimo es {minimo}.')
            continue
        if maximo is not None and numero > maximo:
            print(f'  ✘ El valor máximo es {maximo}.')
            continue
        return numero


def leer_fecha(mensaje):
    """Pide una fecha en formato AAAA-MM-DD y la retorna como texto.

    Repite la pregunta hasta que la fecha sea válida.
    """
    while True:
        valor = input(mensaje).strip()
        try:
            datetime.strptime(valor, '%Y-%m-%d')
            return valor
        except ValueError:
            print('  ✘ Fecha inválida. Usa el formato AAAA-MM-DD (ej. 2025-10-15).')


# CELDA 4.1 — menu_usuarios()
def _elegir_tipo_usuario():
    """Pide al usuario que elija un tipo y retorna el TipoUsuarioEnum."""
    print('  Tipo de usuario:')
    print('    1. Estudiante')
    print('    2. Docente')
    print('    3. Externo')
    opcion = leer_entero('  Elige (1-3): ', 1, 3)
    return [TipoUsuarioEnum.ESTUDIANTE, TipoUsuarioEnum.DOCENTE,
            TipoUsuarioEnum.EXTERNO][opcion - 1]


def menu_usuarios(srv_usuarios):
    """Menú de gestión de usuarios (RF-01). Recibe el UsuarioService."""
    while True:
        limpiar_pantalla()
        print('═══ GESTIÓN DE USUARIOS ═══')
        print('1. Registrar usuario')
        print('2. Consultar usuario por documento')
        print('3. Actualizar contacto y estado')
        print('4. Listar todos los usuarios')
        print('0. Volver')
        opcion = input('Opción: ').strip()

        try:
            if opcion == '1':
                doc = leer_texto('Documento: ')
                nombre = leer_texto('Nombre completo: ')
                tipo = _elegir_tipo_usuario()
                correo = leer_texto('Correo: ')
                telefono = leer_texto('Teléfono: ')
                u = srv_usuarios.registrar(doc, nombre, tipo, correo, telefono)
                print(f'  ✔ Usuario registrado: {u}')

            elif opcion == '2':
                u = srv_usuarios.buscar_por_documento(leer_texto('Documento: '))
                print(f'  {u}' if u else '  ✘ No existe un usuario con ese documento.')

            elif opcion == '3':
                doc = leer_texto('Documento del usuario: ')
                print('  (Enter deja el dato sin cambios)')
                correo = leer_texto('  Nuevo correo: ', obligatorio=False) or None
                telefono = leer_texto('  Nuevo teléfono: ', obligatorio=False) or None
                estado = leer_texto('  Nuevo estado (ACTIVO/SUSPENDIDO): ',
                                    obligatorio=False) or None
                u = srv_usuarios.actualizar(doc, correo, telefono, estado)
                print(f'  ✔ Usuario actualizado: {u}')

            elif opcion == '4':
                usuarios = srv_usuarios.listar_todos()
                if not usuarios:
                    print('  (No hay usuarios registrados)')
                for u in usuarios:
                    print(f'  {u}')

            elif opcion == '0':
                return
            else:
                print('  ✘ Opción no válida.')
        except ValueError as e:
            print(f'  ✘ {e}')


# CELDA 4.2 — menu_libros()
def _mostrar_libros(libros):
    """Imprime una lista de libros, o un aviso si está vacía."""
    if not libros:
        print('  (No se encontraron libros)')
    for l in libros:
        print(f'  {l}')


def menu_libros(srv_libros):
    """Menú de gestión de libros y categorías (RF-02). Recibe el LibroService."""
    while True:
        limpiar_pantalla()
        print('═══ GESTIÓN DE LIBROS Y CATEGORÍAS ═══')
        print('1. Registrar categoría')
        print('2. Listar categorías')
        print('3. Registrar libro')
        print('4. Consultar libro por ISBN')
        print('5. Buscar libros por título')
        print('6. Listar libros por categoría')
        print('7. Listar libros con ejemplares disponibles')
        print('0. Volver')
        opcion = input('Opción: ').strip()

        try:
            if opcion == '1':
                codigo = leer_texto('Código (ej. LIT): ')
                nombre = leer_texto('Nombre: ')
                descripcion = leer_texto('Descripción (opcional): ', obligatorio=False)
                c = srv_libros.registrar_categoria(codigo, nombre, descripcion)
                print(f'  ✔ Categoría registrada: {c}')

            elif opcion == '2':
                categorias = srv_libros.listar_categorias()
                if not categorias:
                    print('  (No hay categorías registradas)')
                for c in categorias:
                    print(f'  {c}')

            elif opcion == '3':
                isbn = leer_texto('ISBN: ')
                titulo = leer_texto('Título: ')
                autor = leer_texto('Autor: ')
                cod_cat = leer_texto('Código de categoría: ')
                anio = leer_entero('Año de publicación: ')
                total = leer_entero('Número de ejemplares: ', minimo=1)
                l = srv_libros.registrar(isbn, titulo, autor, cod_cat, anio, total)
                print(f'  ✔ Libro registrado: {l}')

            elif opcion == '4':
                l = srv_libros.buscar_por_isbn(leer_texto('ISBN: '))
                print(f'  {l}' if l else '  ✘ No existe un libro con ese ISBN.')

            elif opcion == '5':
                _mostrar_libros(srv_libros.buscar_por_titulo(leer_texto('Texto del título: ')))

            elif opcion == '6':
                _mostrar_libros(srv_libros.listar_por_categoria(
                    leer_texto('Código de categoría: ')))

            elif opcion == '7':
                _mostrar_libros(srv_libros.listar_disponibles())

            elif opcion == '0':
                return
            else:
                print('  ✘ Opción no válida.')
        except ValueError as e:
            print(f'  ✘ {e}')


# CELDA 4.3 — menu_prestamos()
def _mostrar_prestamos(prestamos):
    """Imprime una lista de préstamos, o un aviso si está vacía."""
    if not prestamos:
        print('  (No se encontraron préstamos)')
    for p in prestamos:
        print(f'  {p}')


def _pedir_fecha_o_hoy(mensaje):
    """Pide una fecha AAAA-MM-DD. Si el usuario solo presiona Enter, usa hoy."""
    while True:
        valor = input(mensaje).strip()
        if not valor:
            return datetime.now().strftime('%Y-%m-%d')
        try:
            datetime.strptime(valor, '%Y-%m-%d')
            return valor
        except ValueError:
            print('  ✘ Fecha inválida. Usa el formato AAAA-MM-DD (ej. 2026-10-15).')


def menu_prestamos(srv_prestamos):
    """Menú de gestión de préstamos (RF-03). Recibe el PrestamoService."""
    while True:
        limpiar_pantalla()
        print('═══ GESTIÓN DE PRÉSTAMOS ═══')
        print('1. Prestar un libro')
        print('2. Devolver un libro')
        print('3. Consultar préstamo por código')
        print('4. Listar préstamos de un usuario')
        print('5. Listar préstamos vencidos a una fecha')
        print('0. Volver')
        opcion = input('Opción: ').strip()

        try:
            if opcion == '1':
                doc = leer_texto('Documento del usuario: ')
                isbn = leer_texto('ISBN del libro: ')
                fecha = _pedir_fecha_o_hoy('Fecha del préstamo (Enter = hoy): ')
                p = srv_prestamos.prestar(doc, isbn, fecha)
                print(f'  ✔ Préstamo registrado: {p}')

            elif opcion == '2':
                codigo = leer_texto('Código del préstamo: ')
                fecha = _pedir_fecha_o_hoy('Fecha de devolución (Enter = hoy): ')
                p = srv_prestamos.devolver(codigo, fecha)
                print(f'  ✔ Devolución registrada: {p}')
                if srv_prestamos.ultima_multa is not None:
                    print(f'  ⚠ Devolución con retraso. Multa generada: '
                          f'{srv_prestamos.ultima_multa}')

            elif opcion == '3':
                p = srv_prestamos.buscar_por_codigo(leer_texto('Código del préstamo: '))
                print(f'  {p}' if p else '  ✘ No existe un préstamo con ese código.')

            elif opcion == '4':
                _mostrar_prestamos(srv_prestamos.historial_usuario(leer_texto('Documento: ')))

            elif opcion == '5':
                fecha = _pedir_fecha_o_hoy('Fecha de corte (Enter = hoy): ')
                _mostrar_prestamos(srv_prestamos.listar_vencidos(fecha))

            elif opcion == '0':
                return
            else:
                print('  ✘ Opción no válida.')
        except ValueError as e:
            print(f'  ✘ {e}')


# CELDA 4.4 — menu_reservas_multas()
def menu_reservas_multas(srv_reservas, srv_multas, srv_prestamos):
    """Menú de reservas, multas e historial del usuario (RF-04).

    Recibe ReservaService, MultaService y PrestamoService.
    """
    while True:
        limpiar_pantalla()
        print('═══ RESERVAS, MULTAS E HISTORIAL ═══')
        print('1. Reservar un libro sin ejemplares')
        print('2. Cancelar una reserva')
        print('3. Listar reservas de un libro')
        print('4. Consultar multas pendientes de un usuario')
        print('5. Pagar una multa')
        print('6. Historial de préstamos de un usuario')
        print('0. Volver')
        opcion = input('Opción: ').strip()

        try:
            if opcion == '1':
                doc = leer_texto('Documento del usuario: ')
                isbn = leer_texto('ISBN del libro: ')
                fecha = _pedir_fecha_o_hoy('Fecha de la reserva (Enter = hoy): ')
                r = srv_reservas.reservar(doc, isbn, fecha)
                print(f'  ✔ Reserva registrada: {r}')

            elif opcion == '2':
                r = srv_reservas.cancelar(leer_texto('Código de la reserva: '))
                print(f'  ✔ Reserva cancelada: {r}')

            elif opcion == '3':
                reservas = srv_reservas.listar_por_libro(leer_texto('ISBN del libro: '))
                if not reservas:
                    print('  (No hay reservas para ese libro)')
                for r in reservas:
                    print(f'  {r}')

            elif opcion == '4':
                multas = srv_multas.listar_pendientes_usuario(leer_texto('Documento: '))
                if not multas:
                    print('  (El usuario no tiene multas pendientes)')
                for m in multas:
                    print(f'  {m}')
                if multas:
                    print(f'  Total pendiente: ${sum(m.valor for m in multas):,} COP')

            elif opcion == '5':
                m = srv_multas.pagar(leer_texto('Código de la multa: '))
                print(f'  ✔ Multa pagada: {m}')

            elif opcion == '6':
                doc = leer_texto('Documento: ')
                _mostrar_prestamos(srv_prestamos.historial_usuario(doc))
                pendientes = srv_multas.listar_pendientes_usuario(doc)
                print(f'  Multas pendientes: {len(pendientes)}')

            elif opcion == '0':
                return
            else:
                print('  ✘ Opción no válida.')
        except ValueError as e:
            print(f'  ✘ {e}')


# CELDA 4.5 — menu_analisis()
def menu_analisis(srv_analisis):
    """Menú de análisis de datos (RF-05). Recibe el AnalisisDatosService."""
    while True:
        limpiar_pantalla()
        print('═══ ANÁLISIS DE DATOS ═══')
        print('1. Libros más prestados en un periodo')
        print('2. Distribución de préstamos por categoría')
        print('3. Tasa de morosidad por tipo de usuario')
        print('4. Duración promedio de los préstamos devueltos')
        print('5. Reporte de multas')
        print('0. Volver')
        opcion = input('Opción: ').strip()

        try:
            if opcion == '1':
                ini = leer_fecha('Fecha inicio (AAAA-MM-DD): ')
                fin = leer_fecha('Fecha fin (AAAA-MM-DD): ')
                top_n = leer_entero('¿Cuántos libros listar? (ej. 10): ', minimo=1)
                resultado = srv_analisis.libros_mas_prestados(ini, fin, top_n)
                if not resultado:
                    print('  (No hubo préstamos en ese periodo)')
                for i, (isbn, titulo, veces) in enumerate(resultado, start=1):
                    print(f'  {i}. {titulo} (ISBN {isbn}) — {veces} préstamos')

            elif opcion == '2':
                resultado = srv_analisis.prestamos_por_categoria()
                if not resultado:
                    print('  (No hay préstamos registrados)')
                for cod, nombre, cantidad, porcentaje in resultado:
                    print(f'  {cod} | {nombre}: {cantidad} préstamos ({porcentaje}%)')

            elif opcion == '3':
                resultado = srv_analisis.morosidad_por_tipo()
                print(f'  {"Tipo":<12}{"Total":>8}{"Morosos":>10}{"Tasa (%)":>10}')
                for tipo, (total, morosos, tasa) in resultado.items():
                    print(f'  {tipo:<12}{total:>8}{morosos:>10}{tasa:>10}')

            elif opcion == '4':
                promedio, cantidad = srv_analisis.duracion_promedio_prestamo()
                if cantidad == 0:
                    print('  (No hay préstamos devueltos)')
                else:
                    print(f'  Duración promedio: {promedio} días '
                          f'({cantidad} préstamos devueltos)')

            elif opcion == '5':
                r = srv_analisis.reporte_multas()
                print(f'  Multas registradas: {r["cantidad"]}')
                print(f'  Valor generado:  ${r["generado"]:,} COP')
                print(f'  Valor pagado:    ${r["pagado"]:,} COP')
                print(f'  Valor pendiente: ${r["pendiente"]:,} COP')

            elif opcion == '0':
                return
            else:
                print('  ✘ Opción no válida.')
        except ValueError as e:
            print(f'  ✘ {e}')


# CELDA 4.6 — menu_principal()
def menu_principal(srv_usuarios, srv_libros, srv_prestamos,
                   srv_reservas, srv_multas, srv_analisis):
    """Bucle principal del sistema. Opciones 1-5 y 0 para salir."""
    while True:
        print('\n╔════════════════════════════════════╗')
        print('║  SISTEMA DE GESTIÓN BIBLIOTECARIA  ║')
        print('╚════════════════════════════════════╝')
        print('1. Usuarios')
        print('2. Libros y categorías')
        print('3. Préstamos')
        print('4. Reservas, multas e historial')
        print('5. Análisis de datos')
        print('0. Salir')
        opcion = input('Opción: ').strip()

        try:
            if opcion == '1':
                menu_usuarios(srv_usuarios)
            elif opcion == '2':
                menu_libros(srv_libros)
            elif opcion == '3':
                menu_prestamos(srv_prestamos)
            elif opcion == '4':
                menu_reservas_multas(srv_reservas, srv_multas, srv_prestamos)
            elif opcion == '5':
                menu_analisis(srv_analisis)
            elif opcion == '0':
                print('Hasta pronto.')
                return
            else:
                print('  ✘ Opción no válida.')
        except (ValueError, OSError) as e:
            print(f'  ✘ Error: {e}')


# ════════════════════════════════════
# DATOS DE PRUEBA PRECARGADOS (opcional)
# ════════════════════════════════════
CARGAR_DATOS_PRUEBA = False  # Cambia a True para reemplazar los datos por los de prueba


def cargar_datos_prueba():
    """Reemplaza el contenido de los 6 archivos por datos de prueba."""
    ArchivoUtil.reescribir(RUTA_CATEGORIAS, [
        'LIT|Literatura|Novelas y cuentos',
        'TEC|Tecnologia|Programacion y sistemas',
        'CIE|Ciencias|Fisica y matematicas'])
    ArchivoUtil.reescribir(RUTA_LIBROS, [
        '9789585001234|Cien anios de soledad|Gabriel Garcia Marquez|LIT|1967|5|3',
        '9789587654321|Estructuras de datos en Python|Ana Gomez|TEC|2020|2|0',
        '9789580000003|El amor en los tiempos del colera|Gabriel Garcia Marquez|LIT|1985|3|3',
        '9789580000004|Fisica universitaria|Sears Zemansky|CIE|2018|4|3'])
    ArchivoUtil.reescribir(RUTA_USUARIOS, [
        '1098765432|Maria Lopez|ESTUDIANTE|maria.lopez@correo.com|3001234567|ACTIVO',
        '1001234567|Juan Perez|DOCENTE|juan.perez@correo.com|3109876543|ACTIVO',
        '1055555555|Carlos Ruiz|EXTERNO|carlos.ruiz@correo.com|3205555555|ACTIVO'])
    ArchivoUtil.reescribir(RUTA_PRESTAMOS, [
        'PRE-20251001080000|9789585001234|1098765432|2025-10-01|2025-10-08|2025-10-06|DEVUELTO',
        'PRE-20251005090000|9789585001234|1098765432|2025-10-05|2025-10-12|2025-10-15|DEVUELTO',
        'PRE-20251010100000|9789587654321|1001234567|2025-10-10|2025-10-25|2025-10-24|DEVUELTO',
        'PRE-20251012110000|9789587654321|1001234567|2025-10-12|2025-10-27|NINGUNO|ACTIVO',
        'PRE-20251015083000|9789585001234|1055555555|2025-10-15|2025-10-20|2025-10-25|DEVUELTO',
        'PRE-20251018120000|9789580000004|1055555555|2025-10-18|2025-10-23|NINGUNO|VENCIDO',
        'PRE-20251020101500|9789585001234|1001234567|2025-10-20|2025-11-04|NINGUNO|ACTIVO'])
    ArchivoUtil.reescribir(RUTA_MULTAS, [
        'MUL-20251015120000|PRE-20251005090000|3|3000|PAGADA',
        'MUL-20251025140000|PRE-20251015083000|5|5000|PENDIENTE'])
    ArchivoUtil.reescribir(RUTA_RESERVAS, [
        'RES-20251016090000|9789587654321|1098765432|2025-10-16|ACTIVA'])
    print('✔ Datos de prueba cargados.')


# ════════════════════════════════════
# SECCIÓN 5 — EJECUCIÓN PRINCIPAL
# ════════════════════════════════════
def main():
    """Crea repositorios y servicios, y arranca el menú principal."""
    for ruta in [RUTA_USUARIOS, RUTA_CATEGORIAS, RUTA_LIBROS,
                 RUTA_PRESTAMOS, RUTA_MULTAS, RUTA_RESERVAS]:
        ArchivoUtil.crear_si_no_existe(ruta)

    if CARGAR_DATOS_PRUEBA:
        cargar_datos_prueba()

    print(f'✔ Entorno: {ENTORNO}')
    print(f'✔ Datos en: {RUTA_BASE}')

    repo_usuarios = UsuarioRepository(RUTA_USUARIOS)
    repo_categorias = CategoriaRepository(RUTA_CATEGORIAS)
    repo_libros = LibroRepository(RUTA_LIBROS)
    repo_prestamos = PrestamoRepository(RUTA_PRESTAMOS)
    repo_multas = MultaRepository(RUTA_MULTAS, repo_prestamos)
    repo_reservas = ReservaRepository(RUTA_RESERVAS)

    srv_usuarios = UsuarioService(repo_usuarios)
    srv_libros = LibroService(repo_libros, repo_categorias)
    srv_multas = MultaService(repo_multas, repo_prestamos)
    srv_reservas = ReservaService(repo_reservas, repo_usuarios, repo_libros)
    srv_prestamos = PrestamoService(repo_prestamos, repo_usuarios, repo_libros,
                                    repo_multas, srv_multas, srv_reservas)
    srv_analisis = AnalisisDatosService(RUTA_PRESTAMOS, RUTA_LIBROS, RUTA_CATEGORIAS,
                                        RUTA_USUARIOS, RUTA_MULTAS)

    menu_principal(srv_usuarios, srv_libros, srv_prestamos,
                   srv_reservas, srv_multas, srv_analisis)


if __name__ == '__main__':
    main()