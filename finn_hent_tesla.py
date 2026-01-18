import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

URL = "https://www.finn.no/car/used/search.html"

PARAMS = {
    "make": "0.807",  # Tesla
    "sort": "PUBLISHED_DESC",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}


def finn_modell(text: str) -> str:
    t = text.lower()
    if "model s" in t:
        return "Model S"
    if "model 3" in t:
        return "Model 3"
    if "model x" in t:
        return "Model X"
    if "model y" in t:
        return "Model Y"
    return "Ukjent"


def finn_drivlinje(text: str) -> str:
    t = text.lower()
    if "awd" in t or "firehjul" in t or "dual motor" in t:
        return "AWD"
    if "rwd" in t or "bakhjul" in t:
        return "RWD"
    return "Ukjent"


def finn_farge(text: str) -> str:
    for f in ["svart", "hvit", "kvit", "blå", "rød", "raud", "grå", "sølv"]:
        if f in text.lower():
            return f.capitalize()
    return "Ukjent"


def finn_interiør(text: str) -> str:
    t = text.lower()
    if "hvitt interiør" in t or "kvit interiør" in t:
        return "Hvitt"
    if "svart interiør" in t:
        return "Svart"
    return "Ukjent"


def parse_pris_fra_tekst(tekst: str):
    """
    Prøv å finne pris frå tekst som: "349 000 kr"
    """
    m = re.search(r"(\d{2,3}(?:\s?\d{3})+)\s*kr", tekst.lower())
    if not m:
        return None
    try:
        return int(m.group(1).replace(" ", ""))
    except Exception:
        return None


def hent_tesla_dataframe(max_pages: int = 10, sleep_sec: int = 1) -> pd.DataFrame:
    annonser = []

    for page in range(1, max_pages + 1):
        PARAMS["page"] = page

        r = requests.get(URL, params=PARAMS, headers=HEADERS, timeout=30)
        print("Status:", r.status_code, "Page:", page)
        print("URL:", r.url)

        if r.status_code != 200:
            print("Stopper pga status != 200")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        arts = soup.select("article")
        print("Fant article:", len(arts))

        # FINN side 2+ kan vere JS / tom
        if page > 1 and len(arts) == 0:
            print("Stopper: FINN gir ingen <article> på side", page)
            break

        for art in arts:
            try:
                tekst = art.get_text(" ", strip=True)

                # Tittel
                tittel_tag = art.select_one("h2")
                if not tittel_tag:
                    continue
                tittel = tittel_tag.get_text(strip=True)

                # Pris (1) prøv data-testid
                pris = None
                pris_tag = art.select_one("[data-testid='price']")
                if pris_tag:
                    pris_txt = pris_tag.get_text(" ", strip=True)
                    try:
                        pris = int(re.sub(r"\D", "", pris_txt))
                    except Exception:
                        pris = None

                # Pris (2) fallback
                if pris is None:
                    pris = parse_pris_fra_tekst(tekst)

                # km
                km = None
                km_match = re.search(r"(\d[\d\s]*)\s?km", tekst.lower())
                if km_match:
                    try:
                        km = int(km_match.group(1).replace(" ", ""))
                    except Exception:
                        km = None

                # år
                år = None
                år_match = re.search(r"(19|20)\d{2}", tekst)
                if år_match:
                    try:
                        år = int(år_match.group())
                    except Exception:
                        år = None

                # link
                full_lenke = None
                a = art.find("a", href=True)
                if a and a.get("href"):
                    if a["href"].startswith("http"):
                        full_lenke = a["href"]
                    else:
                        full_lenke = "https://www.finn.no" + a["href"]

                # Merk: vi tar med annonsen sjølv om pris er None
                annonser.append(
                    {
                        "Modell": finn_modell(tittel),
                        "Årsmodell": år,
                        "Km": km,
                        "Pris": pris,
                        "Drivlinje": finn_drivlinje(tekst),
                        "Farge": finn_farge(tekst),
                        "Interiør": finn_interiør(tekst),
                        "FINN-link": full_lenke,
                    }
                )

            except Exception:
                continue

        time.sleep(sleep_sec)

    df = pd.DataFrame(annonser)

    # tom DF med rette kolonner om ingen annonser
    if df.empty:
        print("Ingen annonser samlet.")
        return pd.DataFrame(
            columns=[
                "Modell",
                "Årsmodell",
                "Km",
                "Pris",
                "Drivlinje",
                "Farge",
                "Interiør",
                "FINN-link",
            ]
        )

    return df


def lagre_csv(filename: str = "tesla_finn.csv", max_pages: int = 10) -> pd.DataFrame:
    df = hent_tesla_dataframe(max_pages=max_pages)
    print("Antall annonser funnet:", len(df))

    # lagre alltid CSV
    df.to_csv(filename, index=False)
    return df
