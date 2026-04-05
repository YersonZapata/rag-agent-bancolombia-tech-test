import os
import asyncio
import urllib.robotparser
import re
import logging
from urllib.parse import urljoin, urlparse, unquote
from playwright.async_api import async_playwright
from markdownify import markdownify as md

# ==========================================
# CONFIGURACIÓN Y LOGGER
# ==========================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.bancolombia.com"
START_URL = f"{BASE_URL}/personas"
DOMAIN = "www.bancolombia.com"
USER_AGENT = "CrawlerHibrido/1.0"
RATE_LIMIT_SEGUNDOS = 0.5
PALABRAS_IGNORADAS = ["simulador", "simular"]

def inicializar_robot_parser():
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(f"{BASE_URL}/robots.txt")
    try:
        rp.read()
        return rp
    except Exception as e:
        logger.error(f"[!] Error leyendo robots.txt: {e}")
        return None

def url_es_valida(url):
    url_lower = url.lower()
    for palabra in PALABRAS_IGNORADAS:
        if palabra in url_lower:
            return False
    return True

def limpiar_url(url_cruda):
    if not url_cruda:
        return ""
    url_decodificada = unquote(url_cruda)
    parsed = urlparse(url_decodificada)
    url_limpia = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return url_limpia.rstrip('/')

def limpiar_ruido_bancolombia(texto_md):

    # 1. Eliminar artefactos e íconos capturados por el scraper
    artefactos = [
        r'\*idea\*', r'\*alert\*', r'\*arrow2-right\*', r'\*arrow2-down\*',
        r'\*ok\*', r'\*ico-card\*', r'\*icon-contactless\*', r'\*document\*', 
        r'\*arrow-right\*', r'\{\}', r'error'
    ]
    for art in artefactos:
        texto_md = re.sub(art, '', texto_md, flags=re.IGNORECASE)
    
    # 2. Eliminar variables de código residual
    texto_md = re.sub(r'Deferred Modules.*', '', texto_md, flags=re.IGNORECASE)
    texto_md = re.sub(r'\*\s*\$\{title\}\$\{badge\}', '', texto_md)
    texto_md = re.sub(r'\$\{loading\}', '', texto_md)

     # 3. Eliminar llamados a la acción (CTAs) que no aportan contexto semántico
    # Solo los elimina si están en una línea solos (para no borrar texto útil por accidente)
    ctas = [
        r'Conocer más', r'Solicitar en oficinas', r'Descubre cómo',
        r'Abrir por internet', r'Conocer', r'Solicitar', r'Ver más',
        r'Ir al simulador', r'Continuar'
    ]
    for cta in ctas:
        texto_md = re.sub(rf'^\s*{cta}\s*$', '', texto_md, flags=re.IGNORECASE | re.MULTILINE)

    return texto_md

def html_a_markdown(html_bruto):
    """
    Convierte el HTML en Markdown estructurado y ejecuta la limpieza profunda.
    """
    # Convertir a Markdown
    texto_md = md(html_bruto, heading_style="ATX", strip=['img', 'a', 'picture']) 
    
    # Aplicar la limpieza de ruido específica
    texto_md = limpiar_ruido_bancolombia(texto_md)
    
    # Limpiar espacios en blanco al inicio y final de cada línea
    lineas_limpias = [linea.strip() for linea in texto_md.split('\n')]
    texto_md = '\n'.join(lineas_limpias)

    # Limpiar múltiples líneas en blanco (deja máximo 2 juntas)
    texto_md = re.sub(r'\n{3,}', '\n\n', texto_md)
    
    return texto_md.strip()

async def simular_scroll_humano(page):
    await page.evaluate("""
        async () => {
            await new Promise((resolve) => {
                let totalHeight = 0;
                let distance = 500; 
                let timer = setInterval(() => {
                    let scrollHeight = document.body.scrollHeight;
                    window.scrollBy(0, distance);
                    totalHeight += distance;

                    if(totalHeight >= scrollHeight - window.innerHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 150); 
            });
        }
    """)
    await asyncio.sleep(1)

# ==========================================
# LÓGICA DE DESCUBRIMIENTO ORIGINAL
# ==========================================
async def descubrir_categorias_menu(page):
    logger.info(f"Navegando a {START_URL} para leer el menú...")
    await page.goto(START_URL, wait_until="domcontentloaded", timeout=30000)
    
    categorias = set()
    try:
        menu_locator = page.locator('#menu-productos')
        if await menu_locator.count() > 0:
            logger.info("Desplegando menú 'Productos y Servicios'...")
            await menu_locator.first.hover()
            await asyncio.sleep(2) 
            
            enlaces = await page.locator('a[id^="header-productos-"]').evaluate_all(
                "(elementos) => elementos.map(e => e.getAttribute('href'))"
            )
            
            for href in enlaces:
                if href:
                    url_completa = urljoin(START_URL, href)
                    url_limpia = limpiar_url(url_completa)
                    
                    if urlparse(url_limpia).netloc == DOMAIN and url_es_valida(url_limpia):
                        categorias.add(url_limpia)
                        
    except Exception as e:
        logger.error(f"Error extrayendo categorías: {e}")

    categorias_lista = list(categorias)
    logger.info(f"Se encontraron {len(categorias_lista)} categorías principales (Padres).")
    return categorias_lista

async def extraer_enlaces_hijos(page, url_origen_real, url_base_categoria):
    hijos_encontrados = set()
    try:
        enlaces = await page.locator("a").evaluate_all(
            "(elementos) => elementos.map(e => e.getAttribute('href'))"
        )
        for href in enlaces:
            if href:
                url_completa = urljoin(url_origen_real, href)
                url_limpia = limpiar_url(url_completa)
                
                if not url_es_valida(url_limpia):
                    continue

                if (urlparse(url_limpia).netloc == DOMAIN and 
                    url_limpia.startswith(url_base_categoria + '/') and 
                    url_limpia != url_origen_real):
                    
                    hijos_encontrados.add(url_limpia)
    except Exception:
        pass 
        
    return hijos_encontrados

async def mapear_y_extraer_rama(page, rp, categoria_raiz, visitados_global, paginas_guardadas, max_productos):
    logger.info(f"=== EXPLORANDO RAMA: {categoria_raiz} ===")

    # Parseamos la URL, tomamos el path, lo dividimos por '/' y filtramos vacíos
    path_segmentos = [seg for seg in urlparse(categoria_raiz).path.split('/') if seg]
    # Tomamos el último segmento, reemplazamos '-' por espacios y ponemos mayúscula inicial
    nombre_categoria = path_segmentos[-1].replace('-', ' ').capitalize() if path_segmentos else "General"
    
    cola_visitas = [categoria_raiz]

    while cola_visitas:
        if max_productos != -1 and len(paginas_guardadas) >= max_productos:
            logger.info(f"Límite máximo de {max_productos} páginas alcanzado. Deteniendo rama...")
            return True # Indicamos que se alcanzó el límite global

        url_actual = cola_visitas.pop(0)
        
        if url_actual in visitados_global:
            continue
            
        if rp and not rp.can_fetch(USER_AGENT, url_actual):
            logger.warning(f"Robots.txt bloquea: {url_actual}")
            visitados_global.add(url_actual)
            continue

        logger.info(f"Navegando: {url_actual}")
        
        try:
            await page.goto(url_actual, wait_until="domcontentloaded", timeout=20000)
            await simular_scroll_humano(page)
            
            url_final_servidor = limpiar_url(page.url)
            visitados_global.add(url_actual)
            visitados_global.add(url_final_servidor)

            # ==========================================
            # LIMPIEZA DE DOM MEJORADA EN EL NAVEGADOR
            # ==========================================
            titulo = await page.title()
            html_sucio = await page.evaluate("""
                () => {
                    const basura = [
                        'script', 'style', 'noscript', 'meta', 'link', 
                        'svg', 'iframe', 'canvas', 'header', 'footer', 'nav',
                        'button', 'form', 'input', 'select', 'textarea', 
                        '[role="dialog"]', '[role="alert"]', '.cookie-banner',
                        'aside', 'path', '[class*="icon"]', '[class*="btn"]', 
                        '[class*="modal"]', '[id*="menu"]'
                    ];
                    
                    basura.forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => el.remove());
                    });

                    document.querySelectorAll('*').forEach(el => {
                        ['class', 'style', 'id', 'data-tab', 'dir', 'aria-hidden'].forEach(attr => el.removeAttribute(attr));
                    });

                    return document.body.innerHTML;
                }
            """)

            # Convertimos el DOM limpio a Markdown
            markdown_listo = html_a_markdown(html_sucio)
            logger.info(f"Convertido a Markdown: {titulo}")
            
            # Guardamos el producto en memoria
            paginas_guardadas.append({
                "id": str(len(paginas_guardadas) + 1),
                "producto": titulo,               
                "categoria": nombre_categoria,    
                "url": url_final_servidor,
                "contenido": markdown_listo
            })

            # Extraemos y encolamos los hijos descubiertos
            nuevos_hijos = await extraer_enlaces_hijos(page, url_final_servidor, categoria_raiz)
            
            for hijo in nuevos_hijos:
                if hijo not in visitados_global and hijo not in cola_visitas:
                    logger.info(f"Nuevo hijo descubierto: {hijo}")
                    cola_visitas.append(hijo)
                    
            await asyncio.sleep(RATE_LIMIT_SEGUNDOS)

        except Exception as e:
            logger.error(f"Error procesando {url_actual}: {e}")
            visitados_global.add(url_actual)
            
    return False

# ==========================================
# ENDPOINT PRINCIPAL QUE CONECTA CON MAIN.PY
# ==========================================
async def ejecutar_scraping():
    max_productos = int(os.getenv("MAX_PRODUCTOS_A_GUARDAR", "2"))
    logger.info("Iniciando proceso de Scraping y Mapeo de Bancolombia...")
    
    rp = inicializar_robot_parser()
    visitados_global = set()
    paginas_guardadas = []
    limite_alcanzado = False

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT)
        page = await context.new_page()

        # 1. Recuperamos la lógica de leer el menú principal
        categorias_raiz = await descubrir_categorias_menu(page)
        
        if not categorias_raiz:
            logger.warning("No se encontraron categorías en el menú.")
            await browser.close()
            return paginas_guardadas

        # 2. Iteramos por cada rama igual que el original
        for categoria in categorias_raiz:
            if limite_alcanzado:
                break
                
            limite_alcanzado = await mapear_y_extraer_rama(
                page, rp, categoria, visitados_global, paginas_guardadas, max_productos
            )

        await browser.close()

    logger.info(f"Scraping finalizado. {len(paginas_guardadas)} productos extraídos en total.")
    return paginas_guardadas