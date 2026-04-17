"""Configuration constants for search-keyword-revenue.
No other module should hardcode these values.
"""

from types import SimpleNamespace

SEARCH_ENGINES = {"google.com": "q", "yahoo.com": "p", "bing.com": "q", "msn.com": "q"}

REQUIRED_COLUMNS = [
    "hit_time_gmt",
    "date_time",
    "user_agent",
    "ip",
    "event_list",
    "geo_city",
    "geo_region",
    "geo_country",
    "pagename",
    "page_url",
    "product_list",
    "referrer",
]

# To store data as attributes instead of dict keys.
EVENT_TYPES = SimpleNamespace(
    purchase="1", product_view="2", cart_open="10", cart_checkout="11", cart_add="12", cart_remove="13", cart_view="14"
)
