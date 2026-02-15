import struct
import zstandard as zstd
import os
import tarfile
import io
import json
import sys
import shutil
import hashlib

MAGIC_BYTES = b"PARG"
VERSION = 1
INSTALL_ROOT = "./parg_system"
STATE_FILE = os.path.join(INSTALL_ROOT, "registry.json")

os.makedirs(INSTALL_ROOT, exist_ok=True)

def create_parg(folder_path, output_name, pkg_name, pkg_version):
    if not os.path.exists(folder_path):
        print(f"❌ Error: La carpeta '{folder_path}' no existe.")
        return

    # 1. Preparar Payload
    data_buffer = io.BytesIO()
    with tarfile.open(fileobj=data_buffer, mode="w:gz") as tar:
        tar.add(folder_path, arcname=os.path.basename(folder_path))
    payload = data_buffer.getvalue()

    # 2. Preparar Metadatos Comprimidos
    metadata_dict = {
        "name": pkg_name,
        "version": pkg_version,
        "files": os.listdir(folder_path)
    }
    meta_raw = json.dumps(metadata_dict).encode('utf-8')
    cctx = zstd.ZstdCompressor(level=3)
    meta_compressed = cctx.compress(meta_raw)

    # 3. Construir el cuerpo (sin el hash todavía)
    meta_offset = 4 + 2 + 4 + len(payload)
    body = (
        MAGIC_BYTES + 
        struct.pack("<H", VERSION) + 
        struct.pack("<I", meta_offset) + 
        payload + 
        meta_compressed
    )

    # 4. Calcular Hash SHA-256 de seguridad
    file_hash = hashlib.sha256(body).hexdigest()

    with open(output_name, "wb") as f:
        f.write(body)
        f.write(file_hash.encode('utf-8')) # Escribimos el hash al final (64 bytes)

    print(f"📦 Paquete '{output_name}' generado exitosamente.")
    print(f"🛡️  Firma de integridad: {file_hash[:16]}...")

def install_parg(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: El archivo '{file_path}' no existe.")
        return

    with open(file_path, "rb") as f:
        full_data = f.read()
        
        # Separar cuerpo y hash
        body = full_data[:-64]
        stored_hash = full_data[-64:].decode('utf-8')
        
        # Verificar Integridad
        actual_hash = hashlib.sha256(body).hexdigest()
        if stored_hash != actual_hash:
            print("🛑 ¡ERROR DE SEGURIDAD! El paquete ha sido modificado o está corrupto.")
            return
        
        print("🛡️  Verificación de integridad: OK")

        # Parsear el cuerpo (bytes 0-4 son MAGIC, 4-6 VERSION, 6-10 OFFSET)
        offset = struct.unpack("<I", body[6:10])[0]
        
        # Extraer Metadatos
        compressed_meta = body[offset:]
        dctx = zstd.ZstdDecompressor()
        metadata = json.loads(dctx.decompress(compressed_meta).decode('utf-8'))

        print(f"📥 Instalando {metadata['name']} v{metadata['version']}...")

        # Extraer Archivos
        payload_data = body[10:offset]
        with tarfile.open(fileobj=io.BytesIO(payload_data), mode="r:gz") as tar:
            tar.extractall(path=INSTALL_ROOT)

        # Registrar
        registry = {}
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as r: registry = json.load(r)
        
        registry[metadata['name']] = {
            "version": metadata['version'],
            "path": os.path.join(INSTALL_ROOT, metadata['name'])
        }

        with open(STATE_FILE, "w") as r: json.dump(registry, r, indent=4)
        print(f"✅ ¡{metadata['name']} listo para usar!")

def list_pargs():
    if not os.path.exists(STATE_FILE):
        print("📭 No hay paquetes instalados.")
        return
    with open(STATE_FILE, "r") as r:
        registry = json.load(r)
        print("📋 Paquetes instalados:")
        for name, info in registry.items():
            print(f" - {name} (v{info['version']})")

def uninstall_parg(pkg_name):
    if not os.path.exists(STATE_FILE): return
    with open(STATE_FILE, "r") as r: registry = json.load(r)

    if pkg_name in registry:
        shutil.rmtree(registry[pkg_name]["path"], ignore_errors=True)
        del registry[pkg_name]
        with open(STATE_FILE, "w") as r: json.dump(registry, r, indent=4)
        print(f"🗑️  {pkg_name} desinstalado.")
    else:
        print(f"❌ {pkg_name} no encontrado.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 parg.py [build|install|uninstall|list]")
    else:
        cmd = sys.argv[1]
        if cmd == "build": create_parg(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        elif cmd == "install": install_parg(sys.argv[2])
        elif cmd == "uninstall": uninstall_parg(sys.argv[2])
        elif cmd == "list": list_pargs()
