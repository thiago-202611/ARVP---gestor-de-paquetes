# 📦 ARVP - Gestor de Paquetes

Gestor de paquetes liviano para Linux con compresión **Zstandard** y seguridad **SHA-256**.

## 🚀 Instalación
```bash
git clone [https://github.com/thiago-202611/ARVP---gestor-de-paquetes.git](https://github.com/thiago-202611/ARVP---gestor-de-paquetes.git)
cd "ARVP - gestor de paquetes"
python3 -m venv venv_parg
source venv_parg/bin/activate
pip install -r requirements.txt
update	Sincroniza el catálogo con GitHub.
upgrade	Actualiza los paquetes a la última versión.
list	Muestra qué tenés instalado
install <archivo>	Instala un paquete .parg local.
uninstall <nombre>	Elimina un paquete.
