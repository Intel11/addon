# -*- coding: utf-8 -*-
# -*- Channel SleazeMovies -*-
# -*- Created for Alfa-addon -*-
# -*- By Sculkurt -*-

import re
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger

host = 'http://www.eroti.ga/'   #'http://www.eroti.ga/'  'https://www.sleazemovies.com/'


def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(item.clone(title="Todas", action="list_all", url=host, thumbnail=get_thumb('all', auto=True)))
    itemlist.append(item.clone(title="Generos", action="genero", url=host, thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(item.clone(title="Buscar", action="search", thumbnail=get_thumb('search', auto=True)))

    return itemlist


def search(item, texto):
    logger.info()
    if texto != "":
        texto = texto.replace(" ", "+")
    item.url = "%s?s=%s" % (host, texto)
    item.extra = "busqueda"
    try:
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def genero(item):
    logger.info()
    itemlist = list()
    data = httptools.downloadpage(host).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    patron = '<li class="cat-item.*?<a href="([^"]+)".*?>([^<]+)</a>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(action='list_all', title=scrapedtitle, url=scrapedurl))
    return itemlist


def list_all(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)  # Eliminamos tabuladores, dobles espacios saltos de linea, etc...
    patron = '<article id="post-\d+".*?'
    patron += 'h2 class="entry-title"><a href="([^"]+)".*?>(.*?) (?:watch|Watch).*?'
    patron += '<div class="twp-article-post-thumbnail">.*?'
    patron += 'src="([^?]+).*?'
    patron += '<p>([^<]+)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, img, plot in matches:
        contentTitle = scrapertools.find_single_match(scrapedtitle, '([^\(]+)')
        year = scrapertools.find_single_match(scrapedtitle, '(\d{4})')
        if not year:
            year = scrapertools.find_single_match(scrapedtitle, '\((\d{4})\)')
        itemlist.append(item.clone(action = "findvideos", title = scrapedtitle, contentTitle = contentTitle, url = scrapedurl,
                             thumbnail = img, plot=plot, contentType = "movie", infoLabels = {'year': year}))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)

    # Extrae la marca de siguiente página
    next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)"')
    if next_page != "":
	    itemlist.append(item.clone(action="list_all", title=">> Página siguiente", url=next_page, folder=True))
    return itemlist


def findvideos(item): 
    logger.info() 
    itemlist = [] 
    data = httptools.downloadpage(item.url).data 
    url = scrapertools.find_single_match(data, '<p><iframe src="([^#]+)')
    post = "r=&d=sleazemovies.tk"
    url = url.replace("/v/", "/api/source/")
    data = httptools.downloadpage(url, post=post).data
    patron = '"file":"([^"]+)","label":"([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url,quality in matches:
      url = url.replace("\/", "/")
      itemlist.append(item.clone(action="play", title=quality, quality=quality, url=url))
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(item.clone(title = '[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url = item.url,
                             action = "add_pelicula_to_library",
                             extra = "findvideos",
                             contentTitle = item.contentTitle,
                             thumbnail = item.thumbnail))
    return itemlist 

