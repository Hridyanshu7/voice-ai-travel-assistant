"""
FREE Travel Data APIs Integration:
- OpenStreetMap (Overpass API) - Comprehensive POI data
- Wikivoyage/Wikipedia - Travel guides and tips
- Open-Meteo - Weather forecasts
All completely FREE with no API keys required!
"""

import os
import logging
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.mcp.models import POI, GeoPoint

logger = logging.getLogger(__name__)


class FreeTravelDataService:
    """Service using completely FREE travel APIs - no keys required!"""
    
    async def search_overpass_pois(self, city: str, category: str = "tourism") -> List[Dict]:
        """
        Search OpenStreetMap via Overpass API for POIs.
        Categories: tourism, amenity, shop, leisure, historic
        """
        try:
            # First, geocode the city using Nominatim (OSM's geocoder)
            async with httpx.AsyncClient(timeout=30.0) as client:
                nominatim_url = "https://nominatim.openstreetmap.org/search"
                nominatim_params = {
                    "q": city,
                    "format": "json",
                    "limit": 1
                }
                headers = {"User-Agent": "TravelPlannerApp/1.0"}
                
                geocode_response = await client.get(nominatim_url, params=nominatim_params, headers=headers)
                if geocode_response.status_code != 200 or not geocode_response.json():
                    logger.error(f"Geocoding failed for {city}")
                    return []
                
                location = geocode_response.json()[0]
                lat, lon = float(location["lat"]), float(location["lon"])
                
                # Build Overpass query based on category
                if category in ["attractions", "sightseeing", "tourist_spots"]:
                    tags = ["tourism=attraction", "tourism=museum", "tourism=viewpoint", "historic=monument"]
                elif category in ["restaurants", "food", "dining"]:
                    tags = ["amenity=restaurant", "amenity=cafe", "amenity=fast_food"]
                elif category in ["hotels", "accommodation"]:
                    tags = ["tourism=hotel", "tourism=hostel", "tourism=guest_house"]
                elif category in ["shopping", "malls"]:
                    tags = ["shop=mall", "shop=department_store", "amenity=marketplace"]
                else:
                    tags = [f"{category}"]
                
                # Overpass query (search within 5km radius)
                overpass_query = f"""
                [out:json][timeout:25];
                (
                  node[{tags[0]}](around:5000,{lat},{lon});
                  way[{tags[0]}](around:5000,{lat},{lon});
                  relation[{tags[0]}](around:5000,{lat},{lon});
                );
                out center 50;
                """
                
                # Query Overpass API
                overpass_url = "https://overpass-api.de/api/interpreter"
                overpass_response = await client.post(
                    overpass_url,
                    data={"data": overpass_query},
                    headers=headers
                )
                
                if overpass_response.status_code != 200:
                    logger.error(f"Overpass API error: {overpass_response.status_code}")
                    return []
                
                data = overpass_response.json()
                elements = data.get("elements", [])
                
                # Transform to our format
                pois = []
                for element in elements[:20]:  # Limit to 20
                    tags_data = element.get("tags", {})
                    
                    # Get coordinates
                    if element["type"] == "node":
                        poi_lat, poi_lon = element["lat"], element["lon"]
                    elif "center" in element:
                        poi_lat, poi_lon = element["center"]["lat"], element["center"]["lon"]
                    else:
                        continue
                    
                    name = tags_data.get("name", tags_data.get("name:en", "Unknown"))
                    if name == "Unknown":
                        continue
                    
                    poi = {
                        "name": name,
                        "category": category,
                        "rating": 4.0,  # OSM doesn't have ratings
                        "location": {
                            "lat": poi_lat,
                            "lng": poi_lon
                        },
                        "details": {
                            "address": tags_data.get("addr:street", ""),
                            "website": tags_data.get("website", ""),
                            "phone": tags_data.get("phone", ""),
                            "opening_hours": tags_data.get("opening_hours", ""),
                            "cuisine": tags_data.get("cuisine", ""),
                            "description": tags_data.get("description", ""),
                            "wikipedia": tags_data.get("wikipedia", "")
                        }
                    }
                    pois.append(poi)
                
                logger.info(f"Found {len(pois)} POIs from OpenStreetMap for {city}")
                return pois
                
        except Exception as e:
            logger.error(f"Overpass API error: {e}")
            return []
    
    async def get_wikivoyage_guide(self, city: str) -> Dict[str, str]:
        """
        Fetch travel guide from Wikivoyage.
        Returns sections like: See, Do, Eat, Sleep, Safety, etc.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Search for the city page
                search_url = "https://en.wikivoyage.org/w/api.php"
                search_params = {
                    "action": "query",
                    "list": "search",
                    "srsearch": city,
                    "format": "json",
                    "srlimit": 1
                }
                
                search_response = await client.get(search_url, params=search_params)
                if search_response.status_code != 200:
                    return {}
                
                search_data = search_response.json()
                if not search_data.get("query", {}).get("search"):
                    return {}
                
                page_title = search_data["query"]["search"][0]["title"]
                
                # Get page content
                content_params = {
                    "action": "parse",
                    "page": page_title,
                    "format": "json",
                    "prop": "text|sections"
                }
                
                content_response = await client.get(search_url, params=content_params)
                if content_response.status_code != 200:
                    return {}
                
                content_data = content_response.json()
                
                # Extract sections
                sections = content_data.get("parse", {}).get("sections", [])
                guide = {
                    "title": page_title,
                    "sections": {}
                }
                
                for section in sections:
                    section_name = section.get("line", "")
                    if section_name in ["See", "Do", "Eat", "Drink", "Sleep", "Stay safe", "Get around"]:
                        guide["sections"][section_name] = section.get("index", "")
                
                logger.info(f"Retrieved Wikivoyage guide for {city}")
                return guide
                
        except Exception as e:
            logger.error(f"Wikivoyage API error: {e}")
            return {}
    
    async def get_wikipedia_summary(self, city: str) -> str:
        """Get Wikipedia summary/extract for a city."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + city.replace(" ", "_")
                
                response = await client.get(url)
                if response.status_code != 200:
                    return ""
                
                data = response.json()
                summary = data.get("extract", "")
                
                logger.info(f"Retrieved Wikipedia summary for {city}")
                return summary
                
        except Exception as e:
            logger.error(f"Wikipedia API error: {e}")
            return ""
    
    async def get_weather_forecast(self, city: str, days: int = 7) -> Dict[str, Any]:
        """
        Get weather forecast using Open-Meteo API.
        Returns temperature, precipitation, weather codes for next N days.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # First geocode with Nominatim
                nominatim_url = "https://nominatim.openstreetmap.org/search"
                nominatim_params = {
                    "q": city,
                    "format": "json",
                    "limit": 1
                }
                headers = {"User-Agent": "TravelPlannerApp/1.0"}
                
                geocode_response = await client.get(nominatim_url, params=nominatim_params, headers=headers)
                if geocode_response.status_code != 200 or not geocode_response.json():
                    return {}
                
                location = geocode_response.json()[0]
                lat, lon = float(location["lat"]), float(location["lon"])
                
                # Get weather forecast
                weather_url = "https://api.open-meteo.com/v1/forecast"
                weather_params = {
                    "latitude": lat,
                    "longitude": lon,
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
                    "timezone": "auto",
                    "forecast_days": days
                }
                
                weather_response = await client.get(weather_url, params=weather_params)
                if weather_response.status_code != 200:
                    return {}
                
                weather_data = weather_response.json()
                daily = weather_data.get("daily", {})
                
                # Weather code meanings
                weather_codes = {
                    0: "Clear sky",
                    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                    45: "Foggy", 48: "Foggy",
                    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                    95: "Thunderstorm", 96: "Thunderstorm with hail"
                }
                
                forecast = {
                    "city": city,
                    "days": []
                }
                
                for i in range(len(daily.get("time", []))):
                    day_forecast = {
                        "date": daily["time"][i],
                        "temp_max": daily["temperature_2m_max"][i],
                        "temp_min": daily["temperature_2m_min"][i],
                        "precipitation": daily["precipitation_sum"][i],
                        "weather": weather_codes.get(daily["weathercode"][i], "Unknown")
                    }
                    forecast["days"].append(day_forecast)
                
                logger.info(f"Retrieved {days}-day weather forecast for {city}")
                return forecast
                
        except Exception as e:
            logger.error(f"Open-Meteo API error: {e}")
            return {}
    
    async def search_pois_comprehensive(self, city: str, interests: List[str] = None, category: str = "attractions") -> List[POI]:
        """
        Comprehensive POI search using all free APIs.
        """
        all_pois = []
        
        # Get POIs from OpenStreetMap
        osm_pois = await self.search_overpass_pois(city, category)
        all_pois.extend(osm_pois)
        
        # Get city guide from Wikivoyage (for context)
        guide = await self.get_wikivoyage_guide(city)
        
        # Get Wikipedia summary (for city description)
        wiki_summary = await self.get_wikipedia_summary(city)
        
        # Get weather forecast
        weather = await self.get_weather_forecast(city)
        
        # Convert to POI objects
        poi_objects = []
        for i, poi_data in enumerate(all_pois):
            try:
                # Enrich with guide and weather data
                poi_data["details"]["city_guide"] = guide.get("title", "")
                poi_data["details"]["city_description"] = wiki_summary[:200] if wiki_summary else ""
                poi_data["details"]["weather_summary"] = f"{weather['days'][0]['weather']} - {weather['days'][0]['temp_max']}°C" if weather.get("days") else ""
                
                loc_data = poi_data.get("location", {})
                lat = loc_data.get("lat", 0.0)
                lon = loc_data.get("lon") or loc_data.get("lng") or 0.0
                
                description = poi_data["details"].get("description") or poi_data["details"].get("city_description") or ""

                poi = POI(
                    id=f"free-poi-{i}",
                    name=poi_data["name"],
                    category=poi_data["category"],
                    description=description,
                    rating=poi_data.get("rating", 4.0),
                    location=GeoPoint(lat=lat, lon=lon),
                    details=poi_data.get("details", {})
                )
                poi_objects.append(poi)
            except Exception as e:
                logger.error(f"Error creating POI: {e}")
                continue
        
        return poi_objects


# Global instance
free_travel_service = FreeTravelDataService()


async def search_pois_free(city: str, interests: List[str] = None, category: str = "attractions") -> List[POI]:
    """
    Main entry point using FREE APIs - no API keys required!
    """
    pois = await free_travel_service.search_pois_comprehensive(city, interests, category)
    
    if pois:
        logger.info(f"Found {len(pois)} POIs using FREE APIs for {city}")
        return pois
    
    # Fallback to AI generation if needed
    logger.warning(f"No data from free APIs for {city}, using AI generation")
    return []
