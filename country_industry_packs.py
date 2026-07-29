"""Country-specific industry data packs for IIDATECH reports.

This layer deliberately sits beside ``industry_packs.py``. Regional industry
packs remain the default database; when the user selects a country, the app
routes report evidence through these country records instead of the regional
pack text.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from industry_packs import INDUSTRY_PACK_CATALOG


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def country_record_id(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode("utf-8", errors="ignore")).hexdigest()[:16]


def slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


COUNTRY_CATALOG = [
    {
        "country": "United States",
        "region": "North America",
        "sources": [
            ("U.S. Census Bureau", "https://www.census.gov/data.html", "business formation, establishments, retail, construction, housing, trade, and demographic data"),
            ("Bureau of Economic Analysis", "https://www.bea.gov/data", "GDP, industry value added, personal consumption, regional accounts, and input-output tables"),
            ("Bureau of Labor Statistics", "https://www.bls.gov/data/", "employment, wages, productivity, prices, and industry workforce benchmarks"),
            ("SEC EDGAR", "https://www.sec.gov/edgar/search/", "public-company filings for revenue, margin, risk factors, M&A, and comparable-company evidence"),
        ],
    },
    {
        "country": "India",
        "region": "South Asia",
        "sources": [
            ("MOSPI", "https://www.mospi.gov.in/", "national accounts, industry output, price statistics, and enterprise indicators"),
            ("Reserve Bank of India", "https://www.rbi.org.in/", "credit, banking, payments, inflation, financial stability, and sectoral lending data"),
            ("DPIIT / Invest India", "https://www.investindia.gov.in/", "FDI policy, industrial corridors, startup policy, and sector investment context"),
            ("data.gov.in", "https://data.gov.in/", "official Indian government datasets across ministries and states"),
        ],
    },
    {
        "country": "United Kingdom",
        "region": "Europe",
        "sources": [
            ("Office for National Statistics", "https://www.ons.gov.uk/", "GDP, business demography, prices, labor, trade, and household indicators"),
            ("Companies House", "https://find-and-update.company-information.service.gov.uk/", "company filings, accounts, directors, and incorporation data"),
            ("Financial Conduct Authority", "https://www.fca.org.uk/data", "financial services regulation, authorization, market studies, and enforcement data"),
        ],
    },
    {
        "country": "Germany",
        "region": "Europe",
        "sources": [
            ("Destatis", "https://www.destatis.de/EN/Home/_node.html", "German official statistics for production, trade, population, prices, and enterprises"),
            ("Bundesbank", "https://www.bundesbank.de/en/statistics", "financial, banking, payments, credit, and macroeconomic statistics"),
            ("Federal Network Agency", "https://www.bundesnetzagentur.de/EN/Home/home_node.html", "energy, telecommunications, postal, rail, and infrastructure regulation"),
        ],
    },
    {
        "country": "France",
        "region": "Europe",
        "sources": [
            ("INSEE", "https://www.insee.fr/en/accueil", "official French statistics for firms, households, prices, trade, and national accounts"),
            ("Banque de France", "https://www.banque-france.fr/en/statistics", "financial, credit, corporate, and macroeconomic statistics"),
            ("Autorite des marches financiers", "https://www.amf-france.org/en", "capital-market regulation, listed-company disclosure, and investor protection"),
        ],
    },
    {
        "country": "Canada",
        "region": "North America",
        "sources": [
            ("Statistics Canada", "https://www.statcan.gc.ca/en/start", "business, labor, prices, trade, population, and industry statistics"),
            ("Bank of Canada", "https://www.bankofcanada.ca/rates/", "rates, credit, payments, monetary, and financial-system indicators"),
            ("SEDAR+", "https://www.sedarplus.ca/", "Canadian public-company filings and securities disclosure"),
        ],
    },
    {
        "country": "Australia",
        "region": "Asia-Pacific",
        "sources": [
            ("Australian Bureau of Statistics", "https://www.abs.gov.au/statistics", "industry, population, labor, prices, trade, and national accounts"),
            ("Reserve Bank of Australia", "https://www.rba.gov.au/statistics/", "financial, payments, credit, inflation, and monetary data"),
            ("ASIC", "https://asic.gov.au/regulatory-resources/find-a-document/", "company, financial services, enforcement, and market disclosure resources"),
        ],
    },
    {
        "country": "Japan",
        "region": "Asia-Pacific",
        "sources": [
            ("Statistics Bureau of Japan", "https://www.stat.go.jp/english/", "population, labor, household, economy, and industry statistics"),
            ("METI", "https://www.meti.go.jp/english/statistics/", "industrial production, commerce, energy, and technology policy statistics"),
            ("Bank of Japan", "https://www.boj.or.jp/en/statistics/", "financial, payments, credit, prices, and monetary statistics"),
        ],
    },
    {
        "country": "China",
        "region": "Asia-Pacific",
        "sources": [
            ("National Bureau of Statistics of China", "https://www.stats.gov.cn/english/", "national accounts, industry, trade, investment, population, and price statistics"),
            ("People's Bank of China", "http://www.pbc.gov.cn/en/3688006/index.html", "monetary, credit, payments, and financial-market statistics"),
            ("Ministry of Commerce", "http://english.mofcom.gov.cn/", "trade, FDI, ecommerce, and commerce policy context"),
        ],
    },
    {
        "country": "Singapore",
        "region": "Asia-Pacific",
        "sources": [
            ("SingStat", "https://www.singstat.gov.sg/", "population, enterprise, trade, prices, national accounts, and sector statistics"),
            ("Monetary Authority of Singapore", "https://www.mas.gov.sg/statistics", "financial services, payments, fintech, and regulatory data"),
            ("Enterprise Singapore", "https://www.enterprisesg.gov.sg/", "SME, trade, standards, productivity, and enterprise support context"),
        ],
    },
    {
        "country": "United Arab Emirates",
        "region": "Middle East",
        "sources": [
            ("Federal Competitiveness and Statistics Centre", "https://fcsc.gov.ae/en-us", "UAE national statistics for population, economy, trade, and sectors"),
            ("Central Bank of the UAE", "https://www.centralbank.ae/en/research-and-statistics/", "banking, payments, credit, and financial statistics"),
            ("UAE Ministry of Economy", "https://www.moec.gov.ae/en/home", "company, investment, competition, trade, and sector policy context"),
        ],
    },
    {
        "country": "Brazil",
        "region": "Latin America",
        "sources": [
            ("IBGE", "https://www.ibge.gov.br/en/home-eng.html", "Brazil official statistics for industry, services, agriculture, population, and prices"),
            ("Banco Central do Brasil", "https://www.bcb.gov.br/en/statistics", "financial, payments, credit, and monetary statistics"),
            ("CVM", "https://www.gov.br/cvm/en", "securities regulation and public-company disclosure"),
        ],
    },
    {
        "country": "South Africa",
        "region": "Africa",
        "sources": [
            ("Statistics South Africa", "https://www.statssa.gov.za/", "population, labor, GDP, prices, industry, trade, and enterprise statistics"),
            ("South African Reserve Bank", "https://www.resbank.co.za/en/home/what-we-do/statistics", "financial, payments, credit, and macroeconomic statistics"),
            ("Companies and Intellectual Property Commission", "https://www.cipc.co.za/", "company registration and business formalization context"),
        ],
    },
    {
        "country": "South Korea",
        "region": "Asia-Pacific",
        "sources": [
            ("KOSIS", "https://kosis.kr/eng/", "Korean official statistics across industry, demographics, trade, prices, and labor"),
            ("Bank of Korea", "https://www.bok.or.kr/eng/main/main.do", "financial, monetary, payments, and economic statistics"),
            ("Ministry of SMEs and Startups", "https://www.mss.go.kr/site/eng/main.do", "SME, startup, venture, and innovation policy context"),
        ],
    },
    {
        "country": "Taiwan",
        "region": "Asia-Pacific",
        "sources": [
            ("National Statistics, Republic of China Taiwan", "https://eng.stat.gov.tw/", "Taiwan official statistics for industry, population, trade, and prices"),
            ("Ministry of Economic Affairs", "https://www.moea.gov.tw/Mns/english/home/English.aspx", "industrial development, trade, investment, energy, and technology policy context"),
            ("Financial Supervisory Commission", "https://www.fsc.gov.tw/en/", "financial services regulation and listed-company disclosure context"),
        ],
    },
    {
        "country": "Mexico",
        "region": "Latin America",
        "sources": [
            ("INEGI", "https://www.inegi.org.mx/", "Mexico official statistics for enterprises, industry, commerce, population, and prices"),
            ("Banco de Mexico", "https://www.banxico.org.mx/", "financial, payments, credit, monetary, and macroeconomic statistics"),
            ("Secretaria de Economia", "https://www.gob.mx/se", "trade, investment, industry, and enterprise policy context"),
        ],
    },
    {
        "country": "Indonesia",
        "region": "Asia-Pacific",
        "sources": [
            ("Statistics Indonesia", "https://www.bps.go.id/en", "population, enterprise, trade, prices, agriculture, and industry statistics"),
            ("Bank Indonesia", "https://www.bi.go.id/en/statistik/default.aspx", "financial, payments, monetary, and credit statistics"),
            ("Ministry of Investment / BKPM", "https://www.bkpm.go.id/en", "investment, licensing, sector opportunity, and FDI context"),
        ],
    },
    {
        "country": "Saudi Arabia",
        "region": "Middle East",
        "sources": [
            ("General Authority for Statistics", "https://www.stats.gov.sa/en", "Saudi official statistics for GDP, labor, prices, business, trade, and sectors"),
            ("Saudi Central Bank", "https://www.sama.gov.sa/en-US/EconomicReports/Pages/default.aspx", "financial, banking, payments, credit, and macroeconomic statistics"),
            ("Ministry of Investment", "https://misa.gov.sa/", "investment opportunities, licensing, Vision 2030 sector context, and FDI policy"),
        ],
    },
]

COUNTRY_CATALOG.extend(
    [
        {
            "country": "Italy",
            "region": "Europe",
            "sources": [
                ("ISTAT", "https://www.istat.it/en/", "official statistics for enterprises, households, prices, trade, labor, and national accounts"),
                ("Banca d'Italia", "https://www.bancaditalia.it/statistiche/index.html?com.dotmarketing.htmlpage.language=1", "banking, financial, credit, payments, and macroeconomic statistics"),
                ("CONSOB", "https://www.consob.it/web/consob-and-its-activities", "securities regulation, listed-company disclosure, and market supervision"),
            ],
        },
        {
            "country": "Spain",
            "region": "Europe",
            "sources": [
                ("INE Spain", "https://www.ine.es/en/", "official statistics for enterprises, prices, labor, population, tourism, trade, and national accounts"),
                ("Banco de Espana", "https://www.bde.es/wbe/en/estadisticas/", "financial, banking, credit, payments, and macroeconomic statistics"),
                ("CNMV", "https://www.cnmv.es/portal/home.aspx?lang=en", "securities regulation, listed-company filings, and capital-market disclosure"),
            ],
        },
        {
            "country": "Netherlands",
            "region": "Europe",
            "sources": [
                ("Statistics Netherlands", "https://www.cbs.nl/en-gb", "enterprise, trade, labor, population, prices, and sector statistics"),
                ("De Nederlandsche Bank", "https://www.dnb.nl/en/statistics/", "financial, banking, payments, pension, and monetary statistics"),
                ("Netherlands Enterprise Agency", "https://english.rvo.nl/", "innovation, energy, trade, grants, and enterprise support context"),
            ],
        },
        {
            "country": "Sweden",
            "region": "Europe",
            "sources": [
                ("Statistics Sweden", "https://www.scb.se/en/", "business, population, labor, prices, trade, and national accounts"),
                ("Sveriges Riksbank", "https://www.riksbank.se/en-gb/statistics/", "monetary, payments, financial-market, and macroeconomic statistics"),
                ("Swedish Companies Registration Office", "https://bolagsverket.se/en", "company registration, filings, and business-demography context"),
            ],
        },
        {
            "country": "Switzerland",
            "region": "Europe",
            "sources": [
                ("Federal Statistical Office Switzerland", "https://www.bfs.admin.ch/bfs/en/home.html", "enterprise, labor, population, prices, trade, and national statistics"),
                ("Swiss National Bank", "https://data.snb.ch/en", "banking, financial, credit, payments, and macroeconomic data"),
                ("FINMA", "https://www.finma.ch/en/documentation/", "financial-market regulation, supervision, and enforcement context"),
            ],
        },
        {
            "country": "Ireland",
            "region": "Europe",
            "sources": [
                ("Central Statistics Office Ireland", "https://www.cso.ie/en/", "enterprise, trade, labor, prices, population, and national accounts"),
                ("Central Bank of Ireland", "https://www.centralbank.ie/statistics", "financial, banking, credit, payments, and macroeconomic statistics"),
                ("Enterprise Ireland", "https://www.enterprise-ireland.com/en/", "startup, export, innovation, and enterprise support context"),
            ],
        },
        {
            "country": "Poland",
            "region": "Europe",
            "sources": [
                ("Statistics Poland", "https://stat.gov.pl/en/", "enterprise, prices, labor, trade, population, and industry statistics"),
                ("Narodowy Bank Polski", "https://nbp.pl/en/statistic-and-financial-reporting/", "financial, banking, payments, credit, and monetary statistics"),
                ("Polish Investment and Trade Agency", "https://www.paih.gov.pl/en/", "investment, export, sector opportunity, and business-location context"),
            ],
        },
        {
            "country": "Israel",
            "region": "Middle East",
            "sources": [
                ("Israel Central Bureau of Statistics", "https://www.cbs.gov.il/en/Pages/default.aspx", "population, business, labor, prices, trade, and national accounts"),
                ("Bank of Israel", "https://www.boi.org.il/en/economic-roles/statistics/", "financial, banking, credit, payments, and macroeconomic statistics"),
                ("Israel Innovation Authority", "https://innovationisrael.org.il/en/", "innovation, startup, R&D, grants, and technology-sector context"),
            ],
        },
        {
            "country": "Turkey",
            "region": "Middle East / Europe",
            "sources": [
                ("Turkish Statistical Institute", "https://www.tuik.gov.tr/Home/Index", "enterprise, industry, trade, prices, labor, and demographic statistics"),
                ("Central Bank of the Republic of Turkiye", "https://www.tcmb.gov.tr/wps/wcm/connect/en/tcmb+en", "financial, credit, payments, exchange-rate, and macroeconomic statistics"),
                ("Investment Office of the Presidency of Turkiye", "https://www.invest.gov.tr/en/pages/home-page.aspx", "investment, sector, incentive, and business-location context"),
            ],
        },
        {
            "country": "Malaysia",
            "region": "Asia-Pacific",
            "sources": [
                ("Department of Statistics Malaysia", "https://www.dosm.gov.my/portal-main/home", "population, business, prices, trade, labor, and sector statistics"),
                ("Bank Negara Malaysia", "https://www.bnm.gov.my/statistics", "financial, payments, credit, monetary, and banking statistics"),
                ("Malaysian Investment Development Authority", "https://www.mida.gov.my/", "investment, incentives, manufacturing, services, and sector opportunity context"),
            ],
        },
        {
            "country": "Thailand",
            "region": "Asia-Pacific",
            "sources": [
                ("National Statistical Office Thailand", "https://www.nso.go.th/nsoweb/index?set_lang=en", "population, labor, enterprise, trade, and sector statistics"),
                ("Bank of Thailand", "https://www.bot.or.th/en/statistics.html", "financial, payments, credit, banking, and macroeconomic statistics"),
                ("Thailand Board of Investment", "https://www.boi.go.th/index.php?page=index&language=en", "investment promotion, incentives, and sector opportunity context"),
            ],
        },
        {
            "country": "Philippines",
            "region": "Asia-Pacific",
            "sources": [
                ("Philippine Statistics Authority", "https://psa.gov.ph/", "population, enterprise, prices, trade, labor, agriculture, and national accounts"),
                ("Bangko Sentral ng Pilipinas", "https://www.bsp.gov.ph/SitePages/Statistics/Statistics.aspx", "financial, payments, credit, banking, and monetary statistics"),
                ("Board of Investments Philippines", "https://boi.gov.ph/", "investment priorities, incentives, industry policy, and sector context"),
            ],
        },
        {
            "country": "Vietnam",
            "region": "Asia-Pacific",
            "sources": [
                ("General Statistics Office of Vietnam", "https://www.gso.gov.vn/en/homepage/", "population, enterprise, trade, labor, prices, and national accounts"),
                ("State Bank of Vietnam", "https://www.sbv.gov.vn/webcenter/portal/en/home", "financial, banking, credit, payments, and monetary context"),
                ("Foreign Investment Agency Vietnam", "https://fia.mpi.gov.vn/en", "FDI, investment licensing, industrial parks, and sector opportunity context"),
            ],
        },
        {
            "country": "New Zealand",
            "region": "Asia-Pacific",
            "sources": [
                ("Stats NZ", "https://www.stats.govt.nz/", "business, population, labor, prices, trade, and national accounts"),
                ("Reserve Bank of New Zealand", "https://www.rbnz.govt.nz/statistics", "financial, banking, payments, monetary, and credit statistics"),
                ("New Zealand Companies Office", "https://companies-register.companiesoffice.govt.nz/", "company registration, filings, and business-demography context"),
            ],
        },
        {
            "country": "Qatar",
            "region": "Middle East",
            "sources": [
                ("Planning and Statistics Authority Qatar", "https://www.psa.gov.qa/en/Pages/default.aspx", "population, economy, prices, labor, and sector statistics"),
                ("Qatar Central Bank", "https://www.qcb.gov.qa/en/Pages/default.aspx", "financial, banking, credit, payments, and monetary statistics"),
                ("Invest Qatar", "https://www.invest.qa/", "investment opportunities, incentives, sectors, and business setup context"),
            ],
        },
        {
            "country": "Kuwait",
            "region": "Middle East",
            "sources": [
                ("Central Statistical Bureau Kuwait", "https://www.csb.gov.kw/", "population, labor, prices, trade, and sector statistics"),
                ("Central Bank of Kuwait", "https://www.cbk.gov.kw/en/statistics-and-publication/statistical-releases", "financial, banking, credit, payments, and monetary statistics"),
                ("Kuwait Direct Investment Promotion Authority", "https://kdipa.gov.kw/", "investment licensing, incentives, and sector opportunity context"),
            ],
        },
        {
            "country": "Egypt",
            "region": "Africa / Middle East",
            "sources": [
                ("CAPMAS Egypt", "https://www.capmas.gov.eg/", "population, enterprise, trade, labor, prices, and sector statistics"),
                ("Central Bank of Egypt", "https://www.cbe.org.eg/en/economic-research/statistics", "financial, banking, credit, payments, and macroeconomic statistics"),
                ("General Authority for Investment and Free Zones", "https://www.gafi.gov.eg/English/Pages/default.aspx", "investment, free zones, company formation, and sector context"),
            ],
        },
        {
            "country": "Nigeria",
            "region": "Africa",
            "sources": [
                ("National Bureau of Statistics Nigeria", "https://www.nigerianstat.gov.ng/", "population, enterprise, prices, labor, trade, and sector statistics"),
                ("Central Bank of Nigeria", "https://www.cbn.gov.ng/rates/", "financial, payments, credit, banking, and macroeconomic statistics"),
                ("Nigerian Investment Promotion Commission", "https://www.nipc.gov.ng/", "investment promotion, incentives, sectors, and business setup context"),
            ],
        },
        {
            "country": "Kenya",
            "region": "Africa",
            "sources": [
                ("Kenya National Bureau of Statistics", "https://www.knbs.or.ke/", "population, enterprise, prices, labor, trade, and national accounts"),
                ("Central Bank of Kenya", "https://www.centralbank.go.ke/statistics/", "financial, credit, payments, banking, and monetary statistics"),
                ("Kenya Investment Authority", "https://www.invest.go.ke/", "investment promotion, sectors, licensing, and business setup context"),
            ],
        },
        {
            "country": "Argentina",
            "region": "Latin America",
            "sources": [
                ("INDEC Argentina", "https://www.indec.gob.ar/indec/web/Institucional-Indec-InformacionDeArchivo-1", "population, prices, labor, industry, trade, and national statistics"),
                ("Banco Central de la Republica Argentina", "https://www.bcra.gob.ar/PublicacionesEstadisticas/Principales_variables.asp", "financial, banking, credit, exchange-rate, and monetary statistics"),
                ("CNV Argentina", "https://www.argentina.gob.ar/cnv", "securities regulation, capital-market disclosure, and listed-company context"),
            ],
        },
        {
            "country": "Chile",
            "region": "Latin America",
            "sources": [
                ("Instituto Nacional de Estadisticas Chile", "https://www.ine.gob.cl/", "population, enterprise, labor, prices, trade, and sector statistics"),
                ("Banco Central de Chile", "https://www.bcentral.cl/en/web/banco-central/statistics", "financial, payments, credit, monetary, and macroeconomic statistics"),
                ("InvestChile", "https://www.investchile.gob.cl/", "investment promotion, incentives, sectors, and business-location context"),
            ],
        },
        {
            "country": "Colombia",
            "region": "Latin America",
            "sources": [
                ("DANE Colombia", "https://www.dane.gov.co/index.php/en/", "population, enterprise, prices, labor, trade, and national accounts"),
                ("Banco de la Republica Colombia", "https://www.banrep.gov.co/en/statistics", "financial, credit, payments, monetary, and macroeconomic statistics"),
                ("ProColombia", "https://procolombia.co/en", "investment, export, tourism, sectors, and business-opportunity context"),
            ],
        },
    ]
)


COUNTRY_BY_NORMALIZED = {slug(row["country"]): row for row in COUNTRY_CATALOG}
COUNTRY_ALIASES = {
    "usa": "united_states",
    "us": "united_states",
    "u_s": "united_states",
    "america": "united_states",
    "uk": "united_kingdom",
    "u_k": "united_kingdom",
    "uae": "united_arab_emirates",
    "u_a_e": "united_arab_emirates",
    "south_korea_republic_of_korea": "south_korea",
    "korea": "south_korea",
}


def active_industry_rows() -> list[dict]:
    return [row for row in INDUSTRY_PACK_CATALOG if row.get("status") == "active"]


def country_options() -> list[str]:
    return [row["country"] for row in COUNTRY_CATALOG]


def normalize_country(value: str | None) -> str:
    key = slug(value or "")
    key = COUNTRY_ALIASES.get(key, key)
    row = COUNTRY_BY_NORMALIZED.get(key)
    return row["country"] if row else (value or "").strip()


def country_row(value: str | None) -> dict | None:
    selected = normalize_country(value)
    key = slug(selected)
    key = COUNTRY_ALIASES.get(key, key)
    return COUNTRY_BY_NORMALIZED.get(key)


def source_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        host = ""
    if host.startswith("www."):
        host = host[4:]
    return host


def country_source_domains(country: str | None) -> list[str]:
    row = country_row(country)
    if not row:
        return []
    domains: list[str] = []
    for _publisher, url, _coverage in row["sources"]:
        domain = source_domain(url)
        if domain and domain not in domains:
            domains.append(domain)
    return domains


def country_grounding_profile(country: str | None) -> dict:
    scraper_routes = [
        "local_country_dataset_records",
        "xcrawl_site_search",
        "tavily_site_search_if_configured",
        "exa_site_search_if_configured",
        "firecrawl_site_search_if_configured",
    ]
    row = country_row(country)
    if not row:
        selected = normalize_country(country)
        return {
            "country": selected,
            "region": "",
            "minimum_source_count": 3,
            "source_count": 0,
            "domains": [],
            "sources": [],
            "scraper_routes": scraper_routes,
            "status": "missing_country_pack",
            "routing_rule": "No country pack exists; do not generate country-specific figures.",
        }

    sources = []
    for publisher, url, coverage in row["sources"]:
        domain = source_domain(url)
        coverage_terms = re.sub(r"[^a-zA-Z0-9 ]+", " ", coverage)
        sources.append(
            {
                "publisher": publisher,
                "url": url,
                "domain": domain,
                "coverage": coverage,
                "scraper_query": (
                    f"site:{domain} {row['country']} {coverage_terms} market data statistics "
                    "business count regulation pricing financials"
                ).strip(),
            }
        )

    return {
        "country": row["country"],
        "region": row["region"],
        "minimum_source_count": 3,
        "source_count": len(sources),
        "domains": [source["domain"] for source in sources if source["domain"]],
        "sources": sources,
        "scraper_routes": scraper_routes,
        "status": "ready" if len(sources) >= 3 else "needs_more_sources",
        "routing_rule": (
            f"When {row['country']} is selected, use these country-local official domains first. "
            "Regional/global sources may be used only as explicitly labelled proxies and never as the "
            "source of country-specific figures."
        ),
    }


def country_pack_rows() -> list[dict]:
    return [
        {
            "Country": row["country"],
            "Region": row["region"],
            "Official source count": len(row["sources"]),
            "Industry overlays": len(active_industry_rows()),
        }
        for row in COUNTRY_CATALOG
    ]


def country_grounding_rows() -> list[dict]:
    rows = []
    for row in COUNTRY_CATALOG:
        profile = country_grounding_profile(row["country"])
        rows.append(
            {
                "Country": profile["country"],
                "Region": profile["region"],
                "Country source count": profile["source_count"],
                "Grounding status": profile["status"],
                "Scraper routes": ", ".join(profile["scraper_routes"]),
                "Allowed source domains": ", ".join(profile["domains"]),
            }
        )
    return rows


def _country_profile_records(country_row: dict) -> list[dict]:
    rows: list[dict] = []
    country = country_row["country"]
    country_key = slug(country)
    source_names = ", ".join(source[0] for source in country_row["sources"])
    for publisher, url, coverage in country_row["sources"]:
        rows.append(
            {
                "id": country_record_id(country, publisher, "profile"),
                "pack_id": f"country::{country_key}::profile",
                "source_family": "country_pack_official_profile",
                "publisher": publisher,
                "title": f"{country} official country evidence profile - {publisher}",
                "url": url,
                "retrieved_at": now_iso(),
                "geography": country,
                "year": "2026",
                "metric_name": "Country evidence source",
                "metric_value": coverage,
                "unit": "official dataset/source family",
                "topic_tags": ["country_pack", country_key, "official_statistics", "market_sizing", "regulation"],
                "text": (
                    f"{publisher} is part of the country-specific evidence pack for {country}. "
                    f"Use it to localize market sizing, regulatory analysis, business counts, labor costs, "
                    f"pricing benchmarks, trade flows, public-company comps, and investment context. "
                    f"Country source set for this market includes: {source_names}."
                ),
                "confidence": 0.9,
            }
        )
    return rows


def _country_databank_records(country_row: dict) -> list[dict]:
    """Source-route records for each country data bank.

    These are not extracted evidence. They tell the app which official sources,
    news routes, legal/policy routes, and financial-record routes must be used
    before a country-specific claim can be promoted to verified evidence.
    """
    rows: list[dict] = []
    country = country_row["country"]
    country_key = slug(country)
    for publisher, url, coverage in country_row["sources"]:
        rows.append(
            {
                "id": country_record_id(country, publisher, "country_databank_source"),
                "pack_id": f"country::{country_key}::databank",
                "source_family": "country_databank_source",
                "publisher": publisher,
                "title": f"{country} verified source route - {publisher}",
                "url": url,
                "retrieved_at": now_iso(),
                "geography": country,
                "year": "2026",
                "metric_name": "Country data-bank source route",
                "metric_value": coverage,
                "unit": "source route only",
                "topic_tags": [
                    "country_databank",
                    "verified_source_route",
                    country_key,
                    "official_statistics",
                    "financial_records",
                    "policy_sources",
                ],
                "text": (
                    f"{publisher} is a country-local verified source route for {country}. "
                    f"Coverage: {coverage}. Use this source route to fetch extracted metrics, "
                    "laws, filings, or statistics. This route alone is not a verified figure."
                ),
                "confidence": 0.95,
            }
        )

    rows.append(
        {
            "id": country_record_id(country, "gdelt", "country_news_route"),
            "pack_id": f"country::{country_key}::news",
            "source_family": "country_news_route",
            "publisher": "GDELT Project",
            "title": f"{country} verified news and article route",
            "url": "https://www.gdeltproject.org/",
            "retrieved_at": now_iso(),
            "geography": country,
            "year": "2026",
            "metric_name": "Country news route",
            "metric_value": "Use GDELT/news search to find recent country-local articles, magazines, and blogs; verify each source before use",
            "unit": "source route only",
            "topic_tags": [
                "country_news",
                "article_search",
                "magazine_search",
                "blog_search",
                "source_route",
                country_key,
            ],
            "text": (
                f"News route for {country}. Use it to discover recent country-local news, "
                "magazine, and industry blog evidence, then cite the underlying article URL. "
                "Do not use this route record itself as a market fact."
            ),
            "confidence": 0.74,
        }
    )
    return rows


DOMAIN_MECHANICS = {
    "ai_workflow_automation": "AI software, SaaS, workflow automation, agents, copilots, orchestration, APIs, connectors, token costs, governance, retention, ACV, CAC, gross margin, churn, and SMB adoption.",
    "agriculture": "agriculture, food processing, agritech, exports, farmer economics, procurement, certification, cold chain, distributor margin, commodity prices, farm yield, and working capital.",
    "fashion": "fashion, apparel, textile, luxury, retail, inventory turns, gross margin, return rate, channel mix, sourcing, brand positioning, ecommerce conversion, and customer retention.",
    "healthcare": "healthcare, medtech, pharma, diagnostics, clinical workflow, reimbursement, hospital procurement, safety regulation, device approval, lab economics, and patient acquisition.",
    "finance": "fintech, banking, lending, payments, insurance, accounting, tax, bookkeeping, payroll, credit losses, take rate, net interest margin, transaction volume, compliance, fraud, CAC, and retention.",
    "energy": "energy, power, renewables, storage, grid, capex, project finance, tariffs, utilization, interconnection, O&M, battery economics, and regulatory incentives.",
    "water_environment": "water, wastewater, environmental infrastructure, treatment capacity, capex, O&M, compliance permits, effluent standards, tariffs, reuse, desalination, and utility procurement.",
    "real_estate": "real estate, construction, interior design, home improvement, renovation, furniture procurement, architecture, BIM, facility management, housing demand, construction cost, lease rates, occupancy, capex, permitting, contractor workflows, design fee realization, subcontractor margin, and property yield.",
    "logistics": "logistics, transport, warehousing, fleet, freight flows, procurement, B2B marketplaces, supplier enablement, shipping, marine, ports, utilization, route density, fuel cost, warehouse throughput, 3PL margin, and delivery SLA.",
    "education": "education, edtech, workforce training, HR, recruiting, labor-market workflows, enrollment, completion, learning outcomes, school procurement, B2B/B2C pricing, tutor supply, and retention.",
    "consumer": "consumer products, ecommerce, retail, beauty, wellness, pet care, home services, local services, GMV, basket size, purchase frequency, channel margin, logistics cost, return rate, subscription retention, and brand CAC.",
    "manufacturing": "manufacturing, industrial automation, Industry 4.0, factory throughput, downtime, predictive maintenance, yield, labor productivity, capex, and plant-level ROI.",
    "climate": "climate, carbon, sustainability, circular economy, emissions accounting, carbon credits, MRV, recycling economics, disclosure compliance, and decarbonization capex.",
    "hospitality": "hospitality, travel, tourism, hotel, restaurants, foodservice, QSR, cloud kitchens, catering, events, exhibitions, RevPAR, ADR, occupancy, food cost, labor cost, gross bookings, room nights, guest acquisition, OTA take rate, seasonality, and loyalty.",
    "cybersecurity": "cybersecurity, privacy, risk, compliance, breach cost, managed security, threat monitoring, vulnerability management, identity, cloud security, and retention.",
    "telecom": "telecommunications, broadband, connectivity, data centers, ARPU, fiber rollout, spectrum, tower economics, 5G, churn, capex, and network utilization.",
    "automotive": "automotive, EV, mobility, vehicle software, charging, dealer economics, fleet utilization, parts, aftersales, ADAS, battery cost, and financing attach.",
    "semiconductors": "semiconductors, electronics, hardware supply chain, chips, wafers, foundry, fab capex, yield, equipment utilization, cycle time, and inventory.",
    "mining": "mining, metals, critical minerals, materials, reserves, grade, extraction cost, processing, commodity prices, capex, permitting, and offtake.",
    "aerospace_defense": "aerospace, defense, space, aviation, procurement, backlog, launch cadence, certification, MRO, aircraft utilization, satellite economics, and program risk.",
    "media": "media, entertainment, gaming, creator economy, audience, engagement, subscriptions, ARPU, ad yield, content cost, licensing, retention, and platform take rate.",
    "sports": "sports, fitness, recreation, youth sports, club management, participation, facility utilization, memberships, registration fees, payment processing, fan engagement, ticketing, coach/admin workflows, safety, retention, and seasonality.",
    "compliance": "legal services, regtech, public sector, govtech, nonprofit, social impact, contract operations, procurement rules, grant/donor reporting, audit evidence, privacy, records retention, certification, compliance workload, and regulated go-to-market.",
}


def _industry_country_record(country_row: dict, industry_row: dict) -> dict:
    country = country_row["country"]
    country_key = slug(country)
    pack_id = industry_row["pack_id"]
    domain = industry_row["domain"]
    mechanics = DOMAIN_MECHANICS.get(domain, industry_row["industry"])
    official_sources = "; ".join(f"{name}: {coverage}" for name, _url, coverage in country_row["sources"])
    primary_url = country_row["sources"][0][1]
    return {
        "id": country_record_id(country, pack_id, domain, "country_industry"),
        "pack_id": f"country::{country_key}::{pack_id}",
        "source_family": "country_industry_pack",
        "publisher": "IIDATECH Country Industry Dataset",
        "title": f"{country} country-specific pack for {industry_row['industry']}",
        "url": primary_url,
        "retrieved_at": now_iso(),
        "geography": country,
        "year": "2026",
        "metric_name": "Country-industry routing layer",
        "metric_value": "Use country official datasets first; regional industry packs are secondary proxies only",
        "unit": "routing and evidence protocol",
        "topic_tags": [
            "country_pack",
            "country_industry_pack",
            country_key,
            domain,
            pack_id,
            "market_sizing",
            "regulation",
            "competition",
            "unit_economics",
        ],
        "text": (
            f"Country-specific evidence layer for {industry_row['industry']} in {country}. "
            f"When the report is run in country mode, skip regional industry-pack records unless they are explicitly "
            f"labeled as proxy evidence. Build the section around {country} government/statistical sources, country "
            f"regulators, local public-company filings where available, local pricing and labor assumptions, country "
            f"laws/standards, and country-specific demand drivers. Official country sources to use first: "
            f"{official_sources}. Industry scope: {industry_row['industry']}. Domain tag: {domain}. "
            f"Country-industry mechanics to cover: {mechanics} "
            f"Financial model must connect country evidence to TAM/SAM/SOM, revenue build, unit economics, margin, "
            f"working capital, customer acquisition, retention/churn, pricing, comparable companies, and forecast scenarios. "
            f"Test prompt inherited from regional pack: {industry_row.get('test_prompt', '')}."
        ),
        "confidence": 0.82,
    }


def _industry_policy_route_record(country_row: dict, industry_row: dict) -> dict:
    country = country_row["country"]
    country_key = slug(country)
    pack_id = industry_row["pack_id"]
    domain = industry_row["domain"]
    mechanics = DOMAIN_MECHANICS.get(domain, industry_row["industry"])
    source_names = "; ".join(f"{name}: {coverage}" for name, _url, coverage in country_row["sources"])
    return {
        "id": country_record_id(country, pack_id, domain, "policy_route"),
        "pack_id": f"country::{country_key}::{pack_id}::policy",
        "source_family": "country_industry_policy_route",
        "publisher": "IIDATECH Country Policy Databank",
        "title": f"{country} policy and legal source route for {industry_row['industry']}",
        "url": country_row["sources"][0][1],
        "retrieved_at": now_iso(),
        "geography": country,
        "year": "2026",
        "metric_name": "Country-industry legal and policy route",
        "metric_value": "Fetch laws, standards, regulator guidance, certification costs, approval timelines, enforcement actions, and public consultations before writing regulatory findings",
        "unit": "source route only",
        "topic_tags": [
            "country_policy_route",
            "legal",
            "standards",
            "regulation",
            "certification",
            "compliance",
            country_key,
            domain,
            pack_id,
        ],
        "text": (
            f"For {industry_row['industry']} in {country}, check country-local legal and policy sources before "
            f"regulatory sections. Required mechanics: {mechanics} Official source routes: {source_names}. "
            "This route is not extracted legal evidence; cite the specific law, regulator page, standard, fee schedule, "
            "or enforcement document after retrieval."
        ),
        "confidence": 0.9,
    }


def _industry_financial_route_record(country_row: dict, industry_row: dict) -> dict:
    country = country_row["country"]
    country_key = slug(country)
    pack_id = industry_row["pack_id"]
    domain = industry_row["domain"]
    return {
        "id": country_record_id(country, pack_id, domain, "financial_route"),
        "pack_id": f"country::{country_key}::{pack_id}::financial",
        "source_family": "country_industry_financial_route",
        "publisher": "IIDATECH Country Financial Databank",
        "title": f"{country} financial-record route for {industry_row['industry']}",
        "url": country_row["sources"][0][1],
        "retrieved_at": now_iso(),
        "geography": country,
        "year": "2026",
        "metric_name": "Country-industry financial-record route",
        "metric_value": "Fetch central-bank data, public-company filings, securities-regulator records, pricing pages, procurement records, and comparable-company financials before showing financial figures",
        "unit": "source route only",
        "topic_tags": [
            "country_financial_route",
            "financial_records",
            "public_company_filings",
            "market_data",
            "pricing",
            "valuation",
            country_key,
            domain,
            pack_id,
        ],
        "text": (
            f"For {industry_row['industry']} in {country}, verified financial figures must come from extracted country-local "
            "records, company filings, regulator datasets, pricing/procurement evidence, or same-date public comparable data. "
            "This route record helps source collection; it cannot support TAM, SAM, SOM, revenue, margin, or valuation by itself."
        ),
        "confidence": 0.9,
    }


def country_industry_records(country: str | None = None, domain: str | None = None) -> list[dict]:
    selected_country = normalize_country(country) if country else ""
    records: list[dict] = []
    for country_row in COUNTRY_CATALOG:
        if selected_country and country_row["country"] != selected_country:
            continue
        records.extend(_country_profile_records(country_row))
        records.extend(_country_databank_records(country_row))
        for industry_row in active_industry_rows():
            if domain and industry_row["domain"] != domain:
                continue
            records.append(_industry_country_record(country_row, industry_row))
            records.append(_industry_policy_route_record(country_row, industry_row))
            records.append(_industry_financial_route_record(country_row, industry_row))
    return records


def source_text_for_country_domain(country: str, domain: str) -> str:
    selected_country = normalize_country(country)
    records = country_industry_records(selected_country, domain)
    if not records:
        return ""
    blocks = []
    for record in records:
        blocks.append(
            "[COUNTRY INDUSTRY PACK | {source_family} | confidence {confidence:.0%}]\n"
            "Title: {title}\n"
            "Publisher: {publisher} | Geography: {geography} | Year: {year}\n"
            "Metric: {metric_name} = {metric_value} {unit}\n"
            "Summary: {text}\n"
            "Source: {url}".format(**record)
        )
    return (
        f"COUNTRY-SPECIFIC INDUSTRY DATA PACK FOR {selected_country.upper()}:\n"
        "Use this pack before any regional industry database records. Regional packs are skipped in country mode.\n\n"
        + "\n\n".join(blocks)
    )


def country_pack_summary() -> dict:
    country_count = len(COUNTRY_CATALOG)
    industry_count = len(active_industry_rows())
    records = country_industry_records()
    return {
        "country_count": country_count,
        "countries": country_options(),
        "industry_count": industry_count,
        "country_industry_overlay_count": country_count * industry_count,
        "record_count": len(records),
    }


EXPANDED_COUNTRY_CATALOG = [
    {
        "country": "Pakistan",
        "region": "South Asia",
        "sources": [
            ("Pakistan Bureau of Statistics", "https://www.pbs.gov.pk/", "population, enterprise, labor, prices, agriculture, industry, and trade statistics"),
            ("State Bank of Pakistan", "https://www.sbp.org.pk/ecodata/index2.asp", "banking, payments, credit, monetary, and financial statistics"),
            ("Board of Investment Pakistan", "https://invest.gov.pk/", "investment policy, sectors, incentives, and business setup context"),
        ],
    },
    {
        "country": "Bangladesh",
        "region": "South Asia",
        "sources": [
            ("Bangladesh Bureau of Statistics", "https://bbs.gov.bd/", "population, enterprise, prices, agriculture, manufacturing, and trade statistics"),
            ("Bangladesh Bank", "https://www.bb.org.bd/en/index.php/econdata/index", "financial, credit, payments, monetary, and banking statistics"),
            ("Bangladesh Investment Development Authority", "https://bida.gov.bd/", "investment, business setup, sector policy, and investor services"),
        ],
    },
    {
        "country": "Sri Lanka",
        "region": "South Asia",
        "sources": [
            ("Department of Census and Statistics Sri Lanka", "http://www.statistics.gov.lk/", "population, business, labor, prices, agriculture, and national accounts"),
            ("Central Bank of Sri Lanka", "https://www.cbsl.gov.lk/en/statistics", "financial, payments, credit, monetary, and macroeconomic statistics"),
            ("Board of Investment of Sri Lanka", "https://investsrilanka.com/", "investment opportunities, incentives, and business setup context"),
        ],
    },
    {
        "country": "Nepal",
        "region": "South Asia",
        "sources": [
            ("National Statistics Office Nepal", "https://nsonepal.gov.np/", "population, labor, prices, agriculture, industry, and national statistics"),
            ("Nepal Rastra Bank", "https://www.nrb.org.np/category/statistics/", "financial, monetary, credit, payments, and banking statistics"),
            ("Investment Board Nepal", "https://ibn.gov.np/", "investment projects, sectors, incentives, and business setup context"),
        ],
    },
    {
        "country": "Portugal",
        "region": "Europe",
        "sources": [
            ("Statistics Portugal", "https://www.ine.pt/xportal/xmain?xpgid=ine_main&xpid=INE&xlang=en", "business, labor, prices, trade, population, and national accounts"),
            ("Banco de Portugal", "https://www.bportugal.pt/en/statistics", "financial, banking, credit, payments, and macroeconomic statistics"),
            ("AICEP Portugal Global", "https://www.portugalglobal.pt/en/", "investment, export, sectors, incentives, and business-location context"),
        ],
    },
    {
        "country": "Denmark",
        "region": "Nordics",
        "sources": [
            ("Statistics Denmark", "https://www.dst.dk/en", "business, labor, population, prices, trade, and national accounts"),
            ("Danmarks Nationalbank", "https://www.nationalbanken.dk/en/statistics", "financial, banking, payment, monetary, and macroeconomic statistics"),
            ("Invest in Denmark", "https://investindk.com/", "investment promotion, sectors, incentives, and business setup context"),
        ],
    },
    {
        "country": "Norway",
        "region": "Nordics",
        "sources": [
            ("Statistics Norway", "https://www.ssb.no/en", "enterprise, labor, population, prices, trade, energy, and national accounts"),
            ("Norges Bank", "https://www.norges-bank.no/en/topics/Statistics/", "financial, banking, monetary, payments, and macroeconomic statistics"),
            ("Invest in Norway", "https://investinorway.com/", "investment promotion, sectors, and business-location context"),
        ],
    },
    {
        "country": "Finland",
        "region": "Nordics",
        "sources": [
            ("Statistics Finland", "https://stat.fi/index_en.html", "business, labor, population, prices, trade, and national accounts"),
            ("Bank of Finland", "https://www.suomenpankki.fi/en/Statistics/", "financial, banking, credit, payments, and macroeconomic statistics"),
            ("Business Finland", "https://www.businessfinland.com/", "innovation, investment, export, funding, and sector context"),
        ],
    },
    {
        "country": "Belgium",
        "region": "Benelux",
        "sources": [
            ("Statbel", "https://statbel.fgov.be/en", "business, population, labor, prices, trade, and national statistics"),
            ("National Bank of Belgium", "https://www.nbb.be/en/statistics", "financial, banking, payments, credit, and macroeconomic statistics"),
            ("Belgium Business Portal", "https://business.belgium.be/en", "business setup, permits, enterprise services, and regulatory context"),
        ],
    },
    {
        "country": "Austria",
        "region": "DACH",
        "sources": [
            ("Statistics Austria", "https://www.statistik.at/en", "business, labor, prices, population, trade, and national accounts"),
            ("Oesterreichische Nationalbank", "https://www.oenb.at/en/Statistics.html", "financial, banking, payments, credit, and macroeconomic statistics"),
            ("Austrian Business Agency", "https://investinaustria.at/en/", "investment promotion, sectors, incentives, and business-location context"),
        ],
    },
    {
        "country": "Czech Republic",
        "region": "Central and Eastern Europe",
        "sources": [
            ("Czech Statistical Office", "https://www.czso.cz/csu/czso/home", "enterprise, population, labor, prices, trade, and national statistics"),
            ("Czech National Bank", "https://www.cnb.cz/en/statistics/", "financial, monetary, credit, payments, and banking statistics"),
            ("CzechInvest", "https://www.czechinvest.org/en", "investment promotion, sectors, incentives, and business setup context"),
        ],
    },
    {
        "country": "Romania",
        "region": "Central and Eastern Europe",
        "sources": [
            ("National Institute of Statistics Romania", "https://insse.ro/cms/en", "business, population, labor, prices, trade, and national accounts"),
            ("National Bank of Romania", "https://www.bnr.ro/Statistics-2.aspx", "financial, banking, monetary, payments, and credit statistics"),
            ("InvestRomania", "https://investromania.gov.ro/", "investment promotion, sectors, incentives, and business context"),
        ],
    },
    {
        "country": "Greece",
        "region": "Europe",
        "sources": [
            ("Hellenic Statistical Authority", "https://www.statistics.gr/en/home/", "business, labor, population, prices, tourism, trade, and national accounts"),
            ("Bank of Greece", "https://www.bankofgreece.gr/en/statistics", "financial, banking, payments, credit, and macroeconomic statistics"),
            ("Enterprise Greece", "https://www.enterprisegreece.gov.gr/en/", "investment, export, sectors, and business setup context"),
        ],
    },
    {
        "country": "Morocco",
        "region": "Africa / Middle East",
        "sources": [
            ("High Commission for Planning Morocco", "https://www.hcp.ma/", "population, business, prices, labor, trade, and national statistics"),
            ("Bank Al-Maghrib", "https://www.bkam.ma/en/Statistics", "financial, banking, credit, payments, and macroeconomic statistics"),
            ("AMDIE Morocco", "https://www.morocconow.com/", "investment promotion, sectors, incentives, and business-location context"),
        ],
    },
    {
        "country": "Ghana",
        "region": "West Africa",
        "sources": [
            ("Ghana Statistical Service", "https://statsghana.gov.gh/", "population, business, labor, prices, trade, and national statistics"),
            ("Bank of Ghana", "https://www.bog.gov.gh/economic-data/", "financial, credit, monetary, payments, and banking statistics"),
            ("Ghana Investment Promotion Centre", "https://gipc.gov.gh/", "investment promotion, sectors, incentives, and business setup context"),
        ],
    },
    {
        "country": "Ethiopia",
        "region": "East Africa",
        "sources": [
            ("Ethiopian Statistics Service", "https://www.statsethiopia.gov.et/", "population, labor, prices, agriculture, business, and national statistics"),
            ("National Bank of Ethiopia", "https://nbe.gov.et/statistics/", "financial, monetary, banking, credit, and payments statistics"),
            ("Ethiopian Investment Commission", "https://investethiopia.gov.et/", "investment promotion, sectors, incentives, and business setup context"),
        ],
    },
    {
        "country": "Rwanda",
        "region": "East Africa",
        "sources": [
            ("National Institute of Statistics of Rwanda", "https://www.statistics.gov.rw/", "population, enterprise, labor, prices, trade, and national statistics"),
            ("National Bank of Rwanda", "https://www.bnr.rw/statistics/", "financial, banking, credit, payments, and monetary statistics"),
            ("Rwanda Development Board", "https://rdb.rw/", "investment, business registration, sectors, and incentives context"),
        ],
    },
    {
        "country": "Tanzania",
        "region": "East Africa",
        "sources": [
            ("National Bureau of Statistics Tanzania", "https://www.nbs.go.tz/", "population, enterprise, agriculture, labor, prices, trade, and national accounts"),
            ("Bank of Tanzania", "https://www.bot.go.tz/Statistics", "financial, credit, banking, payments, and monetary statistics"),
            ("Tanzania Investment Centre", "https://www.tic.go.tz/", "investment, sectors, incentives, and business setup context"),
        ],
    },
    {
        "country": "Peru",
        "region": "Andean",
        "sources": [
            ("INEI Peru", "https://www.inei.gob.pe/", "population, enterprise, labor, prices, trade, and national statistics"),
            ("Central Reserve Bank of Peru", "https://www.bcrp.gob.pe/estadisticas.html", "financial, monetary, credit, payments, and macroeconomic statistics"),
            ("ProInversion Peru", "https://www.investinperu.pe/en", "investment promotion, projects, sectors, and business context"),
        ],
    },
    {
        "country": "Uruguay",
        "region": "South America",
        "sources": [
            ("National Institute of Statistics Uruguay", "https://www.ine.gub.uy/", "population, enterprise, labor, prices, trade, and national statistics"),
            ("Central Bank of Uruguay", "https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/Default.aspx", "financial, credit, payments, banking, and macroeconomic statistics"),
            ("Uruguay XXI", "https://www.uruguayxxi.gub.uy/en/", "investment, export, sectors, and business-location context"),
        ],
    },
    {
        "country": "Costa Rica",
        "region": "Central America",
        "sources": [
            ("INEC Costa Rica", "https://www.inec.cr/", "population, enterprise, labor, prices, trade, and national statistics"),
            ("Central Bank of Costa Rica", "https://www.bccr.fi.cr/en", "financial, monetary, payments, credit, and macroeconomic statistics"),
            ("CINDE Costa Rica", "https://www.cinde.org/en", "investment promotion, sectors, talent, and business-location context"),
        ],
    },
    {
        "country": "Panama",
        "region": "Central America",
        "sources": [
            ("INEC Panama", "https://www.inec.gob.pa/", "population, enterprise, prices, labor, trade, and national statistics"),
            ("Superintendency of Banks of Panama", "https://www.superbancos.gob.pa/en/financial-and-statistical-information", "banking, financial, credit, and sector statistics"),
            ("PROPANAMA", "https://propanama.gob.pa/", "investment promotion, sectors, logistics, and business setup context"),
        ],
    },
    {
        "country": "Dominican Republic",
        "region": "Caribbean",
        "sources": [
            ("National Statistics Office Dominican Republic", "https://www.one.gob.do/", "population, enterprise, labor, prices, trade, and national statistics"),
            ("Central Bank of the Dominican Republic", "https://www.bancentral.gov.do/a/d/2539-estadisticas-economicas", "financial, monetary, payments, credit, and macroeconomic statistics"),
            ("ProDominicana", "https://prodominicana.gob.do/", "investment, export, sectors, and business opportunity context"),
        ],
    },
    {
        "country": "Oman",
        "region": "Middle East",
        "sources": [
            ("National Centre for Statistics and Information Oman", "https://www.ncsi.gov.om/", "population, enterprise, prices, labor, trade, and national accounts"),
            ("Central Bank of Oman", "https://cbo.gov.om/Statistics", "financial, banking, credit, payments, and monetary statistics"),
            ("Invest Oman", "https://investoman.om/", "investment promotion, sectors, incentives, and business setup context"),
        ],
    },
    {
        "country": "Bahrain",
        "region": "Middle East",
        "sources": [
            ("Information and eGovernment Authority Bahrain", "https://www.data.gov.bh/", "official open data, population, business, labor, and sector statistics"),
            ("Central Bank of Bahrain", "https://www.cbb.gov.bh/statistics/", "financial, banking, credit, payments, and monetary statistics"),
            ("Bahrain Economic Development Board", "https://www.bahrainedb.com/", "investment promotion, sectors, incentives, and business setup context"),
        ],
    },
    {
        "country": "Kazakhstan",
        "region": "Central Asia",
        "sources": [
            ("Bureau of National Statistics Kazakhstan", "https://stat.gov.kz/en/", "population, enterprise, labor, prices, trade, and national statistics"),
            ("National Bank of Kazakhstan", "https://www.nationalbank.kz/en/news/statistika", "financial, banking, credit, payments, and macroeconomic statistics"),
            ("Kazakh Invest", "https://invest.gov.kz/", "investment promotion, sectors, incentives, and business setup context"),
        ],
    },
    {
        "country": "Uzbekistan",
        "region": "Central Asia",
        "sources": [
            ("Statistics Agency under the President of Uzbekistan", "https://stat.uz/en/", "population, enterprise, prices, labor, trade, and national statistics"),
            ("Central Bank of Uzbekistan", "https://cbu.uz/en/statistics/", "financial, banking, credit, payments, and monetary statistics"),
            ("Invest in Uzbekistan", "https://invest.gov.uz/", "investment promotion, sectors, incentives, and business setup context"),
        ],
    },
]


def _register_expanded_countries() -> None:
    existing = {slug(row["country"]) for row in COUNTRY_CATALOG}
    for row in EXPANDED_COUNTRY_CATALOG:
        key = slug(row["country"])
        if key not in existing:
            COUNTRY_CATALOG.append(row)
            existing.add(key)


_register_expanded_countries()
COUNTRY_BY_NORMALIZED = {slug(row["country"]): row for row in COUNTRY_CATALOG}
COUNTRY_ALIASES.update({
    "czechia": "czech_republic",
    "czech_republic_czechia": "czech_republic",
    "republic_of_korea": "south_korea",
    "ksa": "saudi_arabia",
    "kingdom_of_saudi_arabia": "saudi_arabia",
})
