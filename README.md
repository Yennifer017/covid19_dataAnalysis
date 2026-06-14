# Covid 19 Data Analysis

Documentacion base del proyecto con MkDocs y despliegue automatizado en GitHub Actions.

[![Deploy MkDocs site](https://github.com/Yennifer017/covid19_dataAnalysis/actions/workflows/mkdocs.yml/badge.svg)](https://github.com/Yennifer017/covid19_dataAnalysis/actions/workflows/mkdocs.yml)

## Documentacion del proyecto

La documentacion tecnica del proyecto se construye con MkDocs y se publica automaticamente con GitHub Actions.

## Entorno virtual

No es obligatorio para el repositorio, pero se recomienda usar uno para aislar MkDocs y sus dependencias.

Si el `python3` de Homebrew da problemas con `ensurepip`, es mejor usar  explícitamente el Python del sistema:

```bash
/usr/bin/python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecucion local

1. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

2. Levantar el sitio en local:

   ```bash
   mkdocs serve
   ```
    
3. Generar la version estatica:

   ```bash
   mkdocs build --strict
   ```

## Despliegue

- La configuracion de MkDocs esta en [mkdocs.yml](mkdocs.yml).
- El flujo de publicacion automatica esta en [.github/workflows/mkdocs.yml](.github/workflows/mkdocs.yml).
- El contenido base vive en [docs/](docs/).
- En GitHub Pages se deja habilitado en la configuracion del repositorio para publicar el sitio.