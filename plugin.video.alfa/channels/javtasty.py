# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

from core.item import Item
from core import httptools
from core import scrapertools
from platformcode import config, logger

canonical = {
             'channel': 'javtasty', 
             'host': config.get_setting("current_host", 'javtasty', default=''), 
             'host_alt': ["https://www.javbangers.com"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="lista", title="Nuevos Vídeos", url=host + "/latest-updates/"))
    itemlist.append(Item(channel=item.channel, action="lista", title="Mejor Valorados", url=host + "/top-rated/"))
    itemlist.append(Item(channel=item.channel, action="lista", title="Más Vistos", url=host + "/most-popular/"))
    itemlist.append(Item(channel=item.channel, action="categorias", title="Categorías", url=host + "/categories/"))
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search"))
    itemlist.append(Item(channel=item.channel, action="configuracion", title="Configurar canal...", text_color="gold", folder=False))
    return itemlist


def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret


def search(item, texto):
    logger.info()
    item.url = "%s/search/%s/" % (host, texto)
    item.extra = texto
    try:
        return lista(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '(?s)<a class="item" href="([^"]+)".*?'
    patron += 'src="([^"]+)" '
    patron += 'alt="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        scrapedurl = urlparse.urljoin(host, scrapedurl)
        scrapedthumbnail = urlparse.urljoin(host, scrapedthumbnail)
        itemlist.append(Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   fanart=scrapedthumbnail))
    return sorted(itemlist, key=lambda i: i.title)


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    action = "play"
    if config.get_setting("menu_info", "javtasty"):
        action = "menu_info"
    # PURGA los PRIVATE 
    patron  = 'div class="video-item\s+".*?href="([^"]+)".*?'
    patron += 'data-original="([^"]+)" '
    patron += 'alt="([^"]+)"(.*?)fa fa-clock-o"></i>([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, quality, duration in matches:
        scrapedurl = urlparse.urljoin(host, scrapedurl)
        scrapedtitle = scrapedtitle.strip()
        if not 'HD' in quality :
            title = "[COLOR yellow]%s[/COLOR] %s" % (duration.strip(), scrapedtitle)
        else:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (duration.strip(), scrapedtitle)
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, contentTitle = title, url=scrapedurl,
                                   fanart=scrapedthumbnail, thumbnail=scrapedthumbnail))
    # Extrae la marca de siguiente página
    next_page = scrapertools.find_single_match(data, '<li class="next"><a href="([^"]+)"')
    if "#" in next_page:
        next_page = scrapertools.find_single_match(data, 'data-parameters="([^"]+)">Next')
        next_page = next_page.replace(":", "=").replace(";", "&").replace("+from_albums", "")
        next_page = "?%s" % next_page
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page ) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if "video_url_text" in data:
        patron = '(?:video_url|video_alt_url[0-9]*):\s*\'([^\']+)\'.*?'
        patron += '(?:video_url_text|video_alt_url[0-9]*_text):\s*\'([^\']+)\''
    else:
        patron = '(?:video_url|video_alt_url[0-9]*):\s*\'([^\']+)\'.*?'
        patron += 'postfix:\s*\'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)
    for url,quality in matches:
        itemlist.append(Item(channel=item.channel, action="play", title=quality, url=url) )
    if item.extra == "play_menu":
        return itemlist, data
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if "video_url_text" in data:
        patron = '(?:video_url|video_alt_url[0-9]*):\s*\'([^\']+)\'.*?'
        patron += '(?:video_url_text|video_alt_url[0-9]*_text):\s*\'([^\']+)\''
    else:
        patron = '(?:video_url|video_alt_url[0-9]*):\s*\'([^\']+)\'.*?'
        patron += 'postfix:\s*\'([^\']+)\''
    matches = scrapertools.find_multiple_matches(data, patron)
    for url,quality in matches:
        itemlist.append(['.mp4 %s' %quality, url])
    if item.extra == "play_menu":
        return itemlist, data
    return itemlist


def menu_info(item):
    logger.info()
    itemlist = []
    video_urls, data = play(Item(channel=item.channel, extra="play_menu"))
    itemlist.append(Item(channel=item.channel, action="play", title="Ver -- %s" % item.title, video_urls=video_urls))
    matches = scrapertools.find_multiple_matches(data, '<a href="([^"]+)" class="item" rel="screenshots"')
    for i, img in enumerate(matches):
        if i == 0:
            continue
        title = "Imagen %s" % (str(i))
        itemlist.append(Item(channel=item.channel, action="", title=title, thumbnail=img, fanart=img))
    return itemlist

