"""
Редиректы со старых URL на новые (301)
Для сохранения SEO после миграции сайта
"""

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Карта редиректов: старый путь -> новый URL
REDIRECTS = {
    "/kak-izmenilsya-raschet-naloga-usn-v-2023-godu/": "/news/kak-izmenilsya-raschet-naloga-usn-v-2023-godu/",
    "/novaya-forma-deklaracii-usn/": "/news/novaya-forma-deklaracii-usn/",
    "/kak_likvidirovat_ip/": "/news/kak_likvidirovat_ip/",
    "/novaya-forma-deklaracii-usn-v-kakom-sluchae-v-2021-godu-ee-primenyat-ili-polzovatsya-staroj/": "/news/novaya-forma-deklaracii-usn-v-kakom-sluchae-v-2021-godu-ee-primenyat-ili-polzovatsya-staroj/",
    "/shablony_prikazov/": "/upd",
    "/kakie-nalogi-platit-ip-na-usn-s-rabotnikami/": "/news/kakie-nalogi-platit-ip-na-usn-s-rabotnikami/",
    "/kak_likvidirovat_ooo/": "/news/kak_likvidirovat_ooo/",
    "/forma_p13014/": "/upd/",
    "/nulevaya-deklaraciya-zapolnit/": "/upd/",
    "/kratko-ob-usn/": "/news/kratko-ob-usn/",
    "/zapolnenie-nalogovoj-deklaracii-po-uproshchenke-avtomaticheskim-sposobom-v-2021-godu/": "/news/zapolnenie-nalogovoj-deklaracii-po-uproshchenke-avtomaticheskim-sposobom-v-2021-godu/",
    "/kak-pravilno-zapolnit-shablon-deklaracii-po-uproshchenke-v-2020-2021-godu/": "/news/kak-pravilno-zapolnit-shablon-deklaracii-po-uproshchenke-v-2020-2021-godu/",
    "/podrobnoe-opisanie-zapolneniya-nalogovoj-deklaracii-s-formulami-dlya-ip/": "/news/podrobnoe-opisanie-zapolneniya-nalogovoj-deklaracii-s-formulami-dlya-ip/",
    "/generaciya_ustavov/": "/upd/",
    "/nalogovaya-deklaraciya-po-uproshchennoj-sisteme-v-2020-godu/": "/news/nalogovaya-deklaraciya-po-uproshchennoj-sisteme-v-2020-godu/",
    "/stati-usn/": "/news/",
    "/kalkulyator-usn-2021/": "/upd/ip/",
    "/kak-podavat-deklaraciyu-usn/": "/news/kak-podavat-deklaraciyu-usn/",
    "/raschet-pokazatelej-i-obrazec-zapolnenij-nalogovoj-deklaracii-po-uproshchennoj-sisteme-nalogooblozheniya/": "/news/raschet-pokazatelej-i-obrazec-zapolnenij-nalogovoj-deklaracii-po-uproshchennoj-sisteme-nalogooblozheniya/",
    "/pravila/": "/terms/",
    "/uvedomlenie-o-prekrashchenii-primeneniya-usn/": "/news/uvedomlenie-o-prekrashchenii-primeneniya-usn/",
    "/avansovye-platezhi-po-usn-v-2023-godu/": "/news/avansovye-platezhi-po-usn-v-2023-godu/",
    "/raschet-naloga-na-usn-dohody-minus-raskhody/": "/news/raschet-naloga-na-usn-dohody-minus-raskhody/",
    "/otchyotnost-ip-na-usn-bez-rabotnikov-v-2023/": "/news/otchyotnost-ip-na-usn-bez-rabotnikov-v-2023/",
    "/kakie-sushchestvuyut-lgoty-pri-primenenii-usn-organizaciyami/": "/news/kakie-sushchestvuyut-lgoty-pri-primenenii-usn-organizaciyami/",
    "/nuzhno-li-stavit-depozit-v-dohod-na-usn-i-patente/": "/news/nuzhno-li-stavit-depozit-v-dohod-na-usn-i-patente/",
    "/mozhet-li-ip-podat-deklaraciyu-po-usn-onlajn/": "/news/mozhet-li-ip-podat-deklaraciyu-po-usn-onlajn/",
    "/kogda-usn-i-patent-nelzya-sovmeshchat/": "/news/kogda-usn-i-patent-nelzya-sovmeshchat/",
    "/kak-vesti-uchet-raskhodov-ip-pri-usn/": "/news/kak-vesti-uchet-raskhodov-ip-pri-usn/",
    "/sovmeshchenie-usn-s-patentom/": "/news/sovmeshchenie-usn-s-patentom/",
    "/kak-ip-uvedomit-fns-o-perekhode-s-usn-na-npd/": "/news/kak-ip-uvedomit-fns-o-perekhode-s-usn-na-npd/",
    "/po-kakoj-forme-sdavat-deklaraciyu-po-usn-za-2023-god/": "/news/po-kakoj-forme-sdavat-deklaraciyu-po-usn-za-2023-god/",
    "/perekhod-s-envd-perejti-na-usn-kak-ehto-mozhno-sdelat/": "/news/perekhod-s-envd-perejti-na-usn-kak-ehto-mozhno-sdelat/",
    "/kak-umenshit-nalog-usn/": "/news/kak-umenshit-nalog-usn/",
    "/deklaraciya-usn-dohody-minus-raskhody-v-2023-godu/": "/news/deklaraciya-usn-dohody-minus-raskhody-v-2023-godu/",
    "/gosduma-obnovila-formulu-rascheta-vznosov-s-1-yanvarya-2018-goda-dlya-nalogoplatelshchikov/": "/news/gosduma-obnovila-formulu-rascheta-vznosov-s-1-yanvarya-2018-goda-dlya-nalogoplatelshchikov/",
    "/kak-ip-sdat-deklaraciyu-po-usn-v-elektronnom-vide/": "/news/kak-ip-sdat-deklaraciyu-po-usn-v-elektronnom-vide/",
    "/nuzhna-li-onlajn-kassa-dlya-ip-na-usn/": "/news/nuzhna-li-onlajn-kassa-dlya-ip-na-usn/",
    "/kakuyu-sistemu-nalogooblozheniya-vybrat-gruzoperevozchikam/": "/news/kakuyu-sistemu-nalogooblozheniya-vybrat-gruzoperevozchikam/",
    "/sroki-sdachi-otchetnosti-v-nalogovuyu-pri-usn/": "/news/sroki-sdachi-otchetnosti-v-nalogovuyu-pri-usn/",
    "/sistema-nalogooblozheniya-dlya-ip-sdayushchego-nedvizhimost-v-arendu/": "/news/sistema-nalogooblozheniya-dlya-ip-sdayushchego-nedvizhimost-v-arendu/",
    "/otchetnost-ooo-na-usn-bez-rabotnikov/": "/news/otchetnost-ooo-na-usn-bez-rabotnikov/",
    "/patentnaya-sistema-nalogooblozheniya-skolko-platit-i-kak-perejti/": "/news/patentnaya-sistema-nalogooblozheniya-skolko-platit-i-kak-perejti/",
    "/kak-perejti-na-uproshchennuyu-sistemu-nalogooblozheniya/": "/news/kak-perejti-na-uproshchennuyu-sistemu-nalogooblozheniya/",
    "/mozhet-li-ip-na-nalogovyh-kanikulah-menyat-usn-na-patent-i-naoborot/": "/news/mozhet-li-ip-na-nalogovyh-kanikulah-menyat-usn-na-patent-i-naoborot/",
    "/chto-vhodit-v-edinyj-nalogovyj-platezh/": "/news/chto-vhodit-v-edinyj-nalogovyj-platezh/",
    "/usn-dohody-ili-usn-dohody-minus-raskhody-chto-vygodnee-v-2023-godu/": "/news/usn-dohody-ili-usn-dohody-minus-raskhody-chto-vygodnee-v-2023-godu/",
    "/chto-delat-pri-utrate-prava-na-primenenie-usn/": "/news/chto-delat-pri-utrate-prava-na-primenenie-usn/",
    "/kak-oformit-nalogovyj-patent/": "/news/kak-oformit-nalogovyj-patent/",
    "/novyj-zakon-gosdumy-ot-17-noyabrya-2017-goda-ob-otmene-onlajn-kass-dlya-ip/": "/news/novyj-zakon-gosdumy-ot-17-noyabrya-2017-goda-ob-otmene-onlajn-kass-dlya-ip/",
    "/gosduma-prodlila-dlya-predprinimatelej-perekhod-s-envd-na-uproshchenku-do-31-marta/": "/news/gosduma-prodlila-dlya-predprinimatelej-perekhod-s-envd-na-uproshchenku-do-31-marta/",
    "/kody-byudzhetnoj-klassifikacii-dlya-usn/": "/news/kody-byudzhetnoj-klassifikacii-dlya-usn/",
    "/kak-uprostit-podgotovku-otchetnosti-po-usn/": "/news/kak-uprostit-podgotovku-otchetnosti-po-usn/",
    "/kak-rasschityvat-i-uplachivat-peni-za-neuplatu-avansovyh-platezhej-po-usn/": "/news/kak-rasschityvat-i-uplachivat-peni-za-neuplatu-avansovyh-platezhej-po-usn/",
    "/izmeneniya-2023-goda-v-nulevoj-deklaracii-usn-dlya-ip/": "/news/izmeneniya-2023-goda-v-nulevoj-deklaracii-usn-dlya-ip/",
    "/shtrafy-za-nesvoevremennuyu-sdachu-deklaracii-po-usn/": "/news/shtrafy-za-nesvoevremennuyu-sdachu-deklaracii-po-usn/",
    "/nalogovye-kanikuly-dlya-ip-v-2023-godu/": "/news/nalogovye-kanikuly-dlya-ip-v-2023-godu/",
    "/kak-na-usn-pomenyat-obekt-nalogooblozheniya/": "/news/kak-na-usn-pomenyat-obekt-nalogooblozheniya/",
    "/kak-rasschitat-raskhody-pri-stavke-6-usn/": "/news/kak-rasschitat-raskhody-pri-stavke-6-usn/",
    "/kakie-usloviya-dlya-perekhoda-na-usn/": "/news/kakie-usloviya-dlya-perekhoda-na-usn/",
    "/chto-vybrat-predprinimatelyu-dlya-usn-buhgaltera-ili-onlajn-servis/": "/news/chto-vybrat-predprinimatelyu-dlya-usn-buhgaltera-ili-onlajn-servis/",
    "/uproshchennaya-sistema-nalogooblozheniya-dlya-organizacij/": "/news/uproshchennaya-sistema-nalogooblozheniya-dlya-organizacij/",
    "/kak-bystro-i-pravilno-zapolnit-deklaraciyu-po-usn/": "/news/kak-bystro-i-pravilno-zapolnit-deklaraciyu-po-usn/",
    "/platit-li-ip-na-usn-nalog-na-imushchestvo/": "/news/platit-li-ip-na-usn-nalog-na-imushchestvo/",
    "/kakie-kadrovye-dokumenty-dolzhny-byt-u-ip-s-sotrudnikami/": "/news/kakie-kadrovye-dokumenty-dolzhny-byt-u-ip-s-sotrudnikami/",
    "/kak-uchest-na-usn-komissiyu-marketplejsa/": "/news/kak-uchest-na-usn-komissiyu-marketplejsa/",
    "/kak-ip-na-usn-platit-nalogi-iz-za-granicy/": "/news/kak-ip-na-usn-platit-nalogi-iz-za-granicy/",
    "/otchety-i-vznosy-individualnogo-predprinimatelya-na-uproshchenke-6-v-2019-godu/": "/news/otchety-i-vznosy-individualnogo-predprinimatelya-na-uproshchenke-6-v-2019-godu/",
    "/raschet-pri-obekte-nalogooblozheniya/": "/news/raschet-pri-obekte-nalogooblozheniya/",
    "/aktualnye-novosti-o-vnesennyh-izmeneniyah-uproshchennuyu-sistemu-nalogooblozheniya-2018-godu/": "/news/aktualnye-novosti-o-vnesennyh-izmeneniyah-uproshchennuyu-sistemu-nalogooblozheniya-2018-godu/",
    "/kuda-sdavat-deklaraciyu-po-usn/": "/news/kuda-sdavat-deklaraciyu-po-usn/",
    "/s-kakimi-sistemami-nalogooblozheniya-mozhno-sovmeshchat-usn/": "/news/s-kakimi-sistemami-nalogooblozheniya-mozhno-sovmeshchat-usn/",
    "/perekhod-s-usn-na-osno/": "/news/perekhod-s-usn-na-osno/",
    "/kak-umenshit-usn-na-fiksirovannye-vznosy-v-2023-godu/": "/news/kak-umenshit-usn-na-fiksirovannye-vznosy-v-2023-godu/",
    "/podacha-deklaracii-usn-pri-zakrytii-ip-2023/": "/news/podacha-deklaracii-usn-pri-zakrytii-ip-2023/",
    "/podgotovka-i-podacha-nalogovoj-deklaracii-ooo-na-usn/": "/news/podgotovka-i-podacha-nalogovoj-deklaracii-ooo-na-usn/",
    "/kak-zapolnit-zayavlenie-o-perekhode-na-usn/": "/news/kak-zapolnit-zayavlenie-o-perekhode-na-usn/",
    "/kak-ip-na-usn-podat-nulevuyu-deklaraciyu/": "/news/kak-ip-na-usn-podat-nulevuyu-deklaraciyu/",
    "/nulevaya-deklaraciya-usn-dlya-ip-kak-zapolnit/": "/news/nulevaya-deklaraciya-usn-dlya-ip-kak-zapolnit/",
    "/usn-s-01-07-2020-i-01-01-2021-goda/": "/news/usn-s-01-07-2020-i-01-01-2021-goda/",
    "/limity-po-dohodam-dlya-usn-na-2023-god/": "/news/limity-po-dohodam-dlya-usn-na-2023-god/",
    "/kakuyu-otchetnost-dolzhny-podavat-nekommercheskie-organizacii/": "/news/kakuyu-otchetnost-dolzhny-podavat-nekommercheskie-organizacii/",
    "/plan-grafik-sdachi-otchetnosti-nalogoplatelshchikov-po-uproshchenke/": "/news/plan-grafik-sdachi-otchetnosti-nalogoplatelshchikov-po-uproshchenke/",
    "/avtomatizirovannaya-uproshchyonnaya-sistema-nalogooblozheniya/": "/news/avtomatizirovannaya-uproshchyonnaya-sistema-nalogooblozheniya/",
    "/platezhnoe-poruchenie-po-usn-dlya-ip-v-2023-godu/": "/news/platezhnoe-poruchenie-po-usn-dlya-ip-v-2023-godu/",
    "/osobennosti-sdachi-deklaracii-po-usn-pri-mobilizacii/": "/news/osobennosti-sdachi-deklaracii-po-usn-pri-mobilizacii/",
    "/nulevaya-otchetnost-ooo-na-usn/": "/news/nulevaya-otchetnost-ooo-na-usn/",
    "/novye-pravila-umensheniya-usn-i-patenta-na-vznosy/": "/news/novye-pravila-umensheniya-usn-i-patenta-na-vznosy/",
}

# Также проверяем варианты без trailing slash
REDIRECTS_NO_SLASH = {k.rstrip('/'): v for k, v in REDIRECTS.items() if k.endswith('/')}


class RedirectMiddleware(BaseHTTPMiddleware):
    """Middleware для обработки 301 редиректов"""
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Проверяем точное совпадение
        if path in REDIRECTS:
            new_url = REDIRECTS[path]
            return RedirectResponse(url=new_url, status_code=301)
        
        # Проверяем вариант без trailing slash
        if path in REDIRECTS_NO_SLASH:
            new_url = REDIRECTS_NO_SLASH[path]
            return RedirectResponse(url=new_url, status_code=301)
        
        return await call_next(request)
