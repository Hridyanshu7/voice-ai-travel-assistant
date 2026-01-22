"""
Real-time travel data integration using multiple APIs:
- Google Places API for POIs, restaurants, hotels
- OpenTripMap for tourist attractions
- Amadeus for flights and hotels
"""

import os
import logging
import httpx
from typing import List, Dict, Any, Optional
from app.mcp.models import POI

logger = logging.getLogger(__name__)


class TravelDataService:
    """Unified service for fetching real-time travel data from multiple APIs."""
    
    def __init__(self):
        self.google_places_key = os.getenv("GOOGLE_PLACES_API_KEY")
        self.opentripmap_key = os.getenv("OPENTRIPMAP_API_KEY")
        self.amadeus_key = os.getenv("AMADEUS_API_KEY")
        self.amadeus_secret = os.getenv("AMADEUS_API_SECRET")
        self.amadeus_token = None
    
    async def get_amadeus_token(self) -> Optional[str]:
        """Get Amadeus API access token."""
        if not self.amadeus_key or not self.amadeus_secret:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://test.api.amadeus.com/v1/security/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.amadeus_key,
                        "client_secret": self.amadeus_secret
                    }
                )
                if response.status_code == 200:
                    self.amadeus_token = response.json()["access_token"]
                    return self.amadeus_token
        except Exception as e:
            logger.error(f"Amadeus token error: {e}")
        return None
    
    async def search_google_places(self, city: str, query: str, place_type: str = None) -> List[Dict]:
        """Search Google Places API for POIs."""
        if not self.google_places_key:
            logger.warning("Google Places API key not configured")
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                # First, geocode the city to get coordinates
                geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
                geocode_params = {
                    "address": city,
                    "key": self.google_places_key
                }
                
                geocode_response = await client.get(geocode_url, params=geocode_params)
                if geocode_response.status_code != 200:
                    return []
                
                geocode_data = geocode_response.json()
                if not geocode_data.get("results"):
                    return []
                
                location = geocode_data["results"][0]["geometry"]["location"]
                
                # Now search for places
                search_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                search_params = {
                    "location": f"{location['lat']},{location['lng']}",
                    "radius": 5000,  # 5km radius
                    "keyword": query,
                    "key": self.google_places_key
                }
                
                if place_type:
                    search_params["type"] = place_type
                
                search_response = await client.get(search_url, params=search_params)
                if search_response.status_code != 200:
                    return []
                
                results = search_response.json().get("results", [])
                
                # Transform to our format
                pois = []
                for place in results[:10]:  # Limit to top 10
                    poi = {
                        "name": place.get("name"),
                        "category": place.get("types", ["attraction"])[0],
                        "rating": place.get("rating", 4.0),
                        "location": {
                            "lat": place["geometry"]["location"]["lat"],
                            "lng": place["geometry"]["location"]["lng"]
                        },
                        "details": {
                            "address": place.get("vicinity", ""),
                            "price_level": "$" * place.get("price_level", 2),
                            "open_now": place.get("opening_hours", {}).get("open_now", True),
                            "user_ratings_total": place.get("user_ratings_total", 0)
                        }
                    }
                    pois.append(poi)
                
                return pois
                
        except Exception as e:
            logger.error(f"Google Places API error: {e}")
            return []
    
    async def search_opentripmap(self, city: str, category: str = "interesting_places") -> List[Dict]:
        """Search OpenTripMap for tourist attractions."""
        if not self.opentripmap_key:
            logger.warning("OpenTripMap API key not configured")
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                # First geocode the city
                geocode_url = f"https://api.opentripmap.com/0.1/en/places/geoname"
                geocode_params = {
                    "name": city,
                    "apikey": self.opentripmap_key
                }
                
                geocode_response = await client.get(geocode_url, params=geocode_params)
                if geocode_response.status_code != 200:
                    return []
                
                geo_data = geocode_response.json()
                lat, lon = geo_data["lat"], geo_data["lon"]
                
                # Search for places
                search_url = "https://api.opentripmap.com/0.1/en/places/radius"
                search_params = {
                    "radius": 5000,
                    "lon": lon,
                    "lat": lat,
                    "kinds": category,
                    "limit": 20,
                    "apikey": self.opentripmap_key
                }
                
                search_response = await client.get(search_url, params=search_params)
                if search_response.status_code != 200:
                    return []
                
                results = search_response.json().get("features", [])
                
                # Get details for each place
                pois = []
                for feature in results[:10]:
                    xid = feature["properties"]["xid"]
                    
                    # Get place details
                    details_url = f"https://api.opentripmap.com/0.1/en/places/xid/{xid}"
                    details_params = {"apikey": self.opentripmap_key}
                    
                    details_response = await client.get(details_url, params=details_params)
                    if details_response.status_code == 200:
                        details = details_response.json()
                        
                        poi = {
                            "name": details.get("name", "Unknown"),
                            "category": category,
                            "rating": 4.0,  # OpenTripMap doesn't provide ratings
                            "location": {
                                "lat": details["point"]["lat"],
                                "lng": details["point"]["lon"]
                            },
                            "details": {
                                "description": details.get("wikipedia_extracts", {}).get("text", ""),
                                "kinds": details.get("kinds", ""),
                                "image": details.get("preview", {}).get("source", "")
                            }
                        }
                        pois.append(poi)
                
                return pois
                
        except Exception as e:
            logger.error(f"OpenTripMap API error: {e}")
            return []
    
    async def search_hotels_amadeus(self, city: str) -> List[Dict]:
        """Search for hotels using Amadeus API."""
        if not await self.get_amadeus_token():
            logger.warning("Amadeus API not configured")
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                # Search for hotels by city
                url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
                headers = {"Authorization": f"Bearer {self.amadeus_token}"}
                params = {"cityCode": city[:3].upper()}  # Use first 3 letters as city code
                
                response = await client.get(url, headers=headers, params=params)
                if response.status_code != 200:
                    return []
                
                hotels = response.json().get("data", [])
                
                pois = []
                for hotel in hotels[:10]:
                    poi = {
                        "name": hotel.get("name"),
                        "category": "hotel",
                        "rating": 4.0,
                        "location": {
                            "lat": hotel.get("geoCode", {}).get("latitude", 0),
                            "lng": hotel.get("geoCode", {}).get("longitude", 0)
                        },
                        "details": {
                            "hotel_id": hotel.get("hotelId"),
                            "iata_code": hotel.get("iataCode")
                        }
                    }
                    pois.append(poi)
                
                return pois
                
        except Exception as e:
            logger.error(f"Amadeus API error: {e}")
            return []
    
    async def search_pois(self, city: str, interests: List[str] = None, category: str = "attractions") -> List[POI]:
        """
        Unified search across all APIs for comprehensive POI data.
        """
        all_pois = []
        
        # Determine search strategy based on category
        if category in ["attractions", "sightseeing", "tourist_spots"]:
            # Use OpenTripMap for attractions
            opentripmap_results = await self.search_opentripmap(city, "interesting_places")
            all_pois.extend(opentripmap_results)
            
            # Also use Google Places
            google_results = await self.search_google_places(city, "tourist attraction", "tourist_attraction")
            all_pois.extend(google_results)
        
        elif category in ["restaurants", "food", "dining"]:
            google_results = await self.search_google_places(city, "restaurant", "restaurant")
            all_pois.extend(google_results)
        
        elif category in ["hotels", "accommodation", "lodging"]:
            # Try Amadeus first
            amadeus_results = await self.search_hotels_amadeus(city)
            if amadeus_results:
                all_pois.extend(amadeus_results)
            else:
                # Fallback to Google Places
                google_results = await self.search_google_places(city, "hotel", "lodging")
                all_pois.extend(google_results)
        
        elif category in ["shopping", "malls"]:
            google_results = await self.search_google_places(city, "shopping", "shopping_mall")
            all_pois.extend(google_results)
        
        else:
            # General search
            google_results = await self.search_google_places(city, category)
            all_pois.extend(google_results)
        
        # Convert to POI objects
        poi_objects = []
        for i, poi_data in enumerate(all_pois):
            try:
                loc_data = poi_data.get("location", {})
                lat = loc_data.get("lat", 0.0)
                lon = loc_data.get("lon") or loc_data.get("lng") or 0.0
                
                description = poi_data["details"].get("description") or ""

                poi = POI(
                    id=f"paid-poi-{i}",
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
travel_service = TravelDataService()


async def search_pois(city: str, interests: List[str] = None, category: str = "attractions") -> List[POI]:
    """
    Main entry point for POI search - uses real APIs when available, falls back to AI generation.
    """
    # Try real APIs first
    real_pois = await travel_service.search_pois(city, interests, category)
    
    if real_pois:
        logger.info(f"Found {len(real_pois)} real POIs for {city}")
        return real_pois
    
    # Fallback to AI generation (existing code)
    logger.warning(f"No real API data for {city}, using AI generation")
    from app.mcp.travel_data import search_pois as ai_search_pois
    return ai_search_pois(city, interests, category)
