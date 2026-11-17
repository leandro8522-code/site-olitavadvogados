import urllib.request, re, json, os
from datetime import datetime

# Diretório base dinâmico (funciona tanto no seu PC quanto no servidor Linux do GitHub)
SITE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTICIAS_JSON = os.path.join(SITE_DIR, "noticias.json")
IMG_DIR = os.path.join(SITE_DIR, "img", "noticias")
os.makedirs(IMG_DIR, exist_ok=True)
RSS_URL = "https://www12.senado.leg.br/noticias/rss"
BASE_SENADO = "https://www12.senado.leg.br"
FONTE_NOME = "Senado Federal"
FONTE_URL = "https://www12.senado.leg.br/hpsenado"
DELAYS = ["", "delay-1", "delay-2"]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    res = urllib.request.urlopen(req, timeout=25)
    return res.read().decode("utf-8", errors="ignore")

def limpar_html_basico(texto):
    texto = re.sub(r"&amp;", "&", texto)
    texto = re.sub(r"&lt;", "<", texto)
    texto = re.sub(r"&gt;", ">", texto)
    texto = re.sub(r"&nbsp;", " ", texto)
    texto = re.sub(r"&#\d+;", "", texto)
    return texto

def extrair_materia_completa(url):
    """
    Extrai com precisão:
    1. A imagem real e oficial da matéria (com legenda e crédito)
    2. O texto integral idêntico ao original (div id="textoMateria")
    """
    try:
        html = fetch(url)

        # 1. IMAGEM OFICIAL DA MATÉRIA
        img_match = re.search(r'<img[^>]+class="[^"]*fonteslide[^"]*"[^>]+src="([^"]+)"', html)
        if not img_match:
            img_match = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html)

        imagem = None
        if img_match:
            imagem = img_match.group(1).strip()
            if imagem.startswith("/"):
                imagem = BASE_SENADO + imagem

        legenda_match = re.search(r'<img[^>]+class="[^"]*fonteslide[^"]*"[^>]+legenda="([^"]+)"', html)
        legenda = legenda_match.group(1).strip() if legenda_match else ""
        credito_match = re.search(r'<img[^>]+class="[^"]*fonteslide[^"]*"[^>]+credito="([^"]+)"', html)
        credito = credito_match.group(1).strip() if credito_match else ""

        # 2. TEXTO INTEGRAL DA MATÉRIA (id="textoMateria")
        texto_match = re.search(r'<div id="textoMateria">(.*?)</div>\s*<div id="boxRodapeMateria"', html, re.DOTALL)
        if not texto_match:
            texto_match = re.search(r'<div id="textoMateria">(.*?)</div>', html, re.DOTALL)

        conteudo_puro = ""
        if texto_match:
            conteudo_puro = texto_match.group(1)
            conteudo_puro = re.sub(r'href="/', f'href="{BASE_SENADO}/', conteudo_puro)
            conteudo_puro = re.sub(r'<p>\s*</p>', '', conteudo_puro)
            conteudo_puro = re.sub(r'<p>[^<]*Compartilhe este conteúdo[^<]*</p>', '', conteudo_puro, flags=re.IGNORECASE)
            conteudo_puro = conteudo_puro.strip()
        else:
            paragrafos = re.findall(r"<p[^>]*>(.*?)</p>", html, re.DOTALL)
            textos_validos = []
            for p in paragrafos:
                p_limpo = re.sub(r"<[^>]+>", " ", p).strip()
                if len(p_limpo) > 60 and "compartilhe" not in p_limpo.lower() and not p_limpo.startswith("©"):
                    textos_validos.append(f"<p>{p_limpo}</p>")
            conteudo_puro = "".join(textos_validos)

        if not imagem:
            imagem = "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?auto=format&fit=crop&q=80&w=800"

        return imagem, legenda, credito, conteudo_puro

    except Exception as e:
        print(f"    Erro ao extrair {url}: {e}")
        return "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?auto=format&fit=crop&q=80&w=800", "", "", ""

def buscar_noticias():
    rss = fetch(RSS_URL)
    items = re.findall(r"<item>(.*?)</item>", rss, re.DOTALL)
    noticias = []

    for item in items:
        t = re.search(r"<title>(.*?)</title>", item, re.DOTALL)
        titulo = limpar_html_basico(re.sub(r"<[^>]+>", "", t.group(1))).strip() if t else ""

        l = re.search(r"<link>(.*?)</link>", item, re.DOTALL)
        link_original = l.group(1).strip() if l else ""

        d = re.search(r"<description>(.*?)</description>", item, re.DOTALL)
        resumo = limpar_html_basico(re.sub(r"<[^>]+>", "", d.group(1))).strip() if d else ""
        if len(resumo) > 190:
            resumo = resumo[:187] + "..."

        pub = re.search(r"<pubDate>(.*?)</pubDate>", item, re.DOTALL)
        data = pub.group(1).strip()[:10] if pub else ""

        if not titulo or not link_original:
            continue

        if "/materias/" not in link_original:
            continue

        post_id = re.sub(r"[^a-z0-9]", "-", link_original.split("/")[-1].lower())[:60]

        print(f"  Extraindo matéria integral: {titulo[:60]}...")
        imagem_remota, legenda, credito, conteudo_html = extrair_materia_completa(link_original)

        # Baixa a imagem para a pasta local img/noticias para evitar bloqueio anti-hotlink
        caminho_imagem = imagem_remota
        if imagem_remota and imagem_remota.startswith("http") and "unsplash" not in imagem_remota:
            nome_arq = f"senado_{post_id}.jpg"
            dest = os.path.join(IMG_DIR, nome_arq)
            try:
                req_img = urllib.request.Request(imagem_remota, headers=HEADERS)
                with urllib.request.urlopen(req_img, timeout=15) as r_img:
                    with open(dest, "wb") as f_img:
                        f_img.write(r_img.read())
                caminho_imagem = f"img/noticias/{nome_arq}"
            except Exception as e_img:
                print(f"    Aviso ao baixar imagem {imagem_remota}: {e_img}")

        noticias.append({
            "id": f"senado_{post_id}",
            "title": titulo,
            "summary": resumo,
            "link": link_original,
            "image": caminho_imagem,
            "legenda": legenda,
            "credito": credito,
            "conteudo": conteudo_html,
            "fonte": FONTE_NOME,
            "fonte_url": FONTE_URL,
            "data": data,
            "delay": ""
        })

    return noticias

def carregar_existentes():
    if not os.path.exists(NOTICIAS_JSON):
        return []
    try:
        with open(NOTICIAS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def salvar_noticias(noticias):
    with open(NOTICIAS_JSON, "w", encoding="utf-8") as f:
        json.dump(noticias, f, ensure_ascii=False, indent=4)

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando captura completa do Senado Federal...")
    novas = buscar_noticias()
    print(f"  → {len(novas)} matérias capturadas do Senado.")

    existentes = carregar_existentes()
    ids_novos = {n["id"] for n in novas}

    # Mantém as notícias antigas que não vieram nessa leva recente
    antigas_mantidas = [n for n in existentes if n.get("id") not in ids_novos]

    # As novas ficam no topo (mais recentes primeiro), seguidas pelas antigas (acumula até 50 notícias)
    todas = (novas + antigas_mantidas)[:50]

    for i, n in enumerate(todas):
        n["delay"] = DELAYS[i % 3]

    salvar_noticias(todas)
    print(f"  → Arquivo noticias.json salvo! Total acumulado no site: {len(todas)} notícias.")

if __name__ == "__main__":
    main()
