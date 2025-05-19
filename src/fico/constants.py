import pycountry

from fico.utils import format_currency

EXCLUDED_CURRENCIES = [
    "XAU",  # gold
    "XAG",  # silver
    "XPD",  # palladium
    "XPT",  # platinum
    "XBA",  # European Composite Unit (EURCO) (bond market unit)
    "XBB",  # European Monetary Unit (E.M.U.-6) (bond market unit)
    "XBC",  # European Unit of Account 9 (E.U.A.-9) (bond market unit)
    "XBD",  # European Unit of Account 17 (E.U.A.-17) (bond market unit)
    "XDR",  # Special drawing rights (International Monetary Fund)
    "XSU",  # Unified System for Regional Compensation (SUCRE)
    "XTS",  # reserved for testign
    "XXX",  # No currency
]
CURRENCIES = [
    (format_currency(currency.alpha_3), currency.alpha_3)
    for currency in pycountry.currencies
    if currency.alpha_3 not in EXCLUDED_CURRENCIES
]
APIS = [
    (
        "https://cloudspend.velasuci.com/ops/v1",
        "https://cloudspend.velasuci.com/ops/v1",
    ),
    (
        "https://api.finops.s1.today/ops/v1",
        "https://api.finops.s1.today/ops/v1",
    ),
    (
        "https://api.finops.s1.show/ops/v1",
        "https://api.finops.s1.show/ops/v1",
    ),
    (
        "https://api.finops.s1.live/ops/v1",
        "https://api.finops.s1.live/ops/v1",
    ),
    (
        "https://api.finops.softwareone.com/ops/v1",
        "https://api.finops.softwareone.com/ops/v1",
    ),
]

DEFAULT_API = "https://api.finops.softwareone.com/ops/v1"
