# Scrapers package for permit leads
from .houston_city import HoustonCityScraper

# Available scrapers
SCRAPERS = {
    "city_of_houston": HoustonCityScraper,
}