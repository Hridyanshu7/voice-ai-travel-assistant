import logging
from typing import List
from app.mcp.models import BuildItineraryRequest, Itinerary, DayItinerary, ItineraryBlock, POI, GeoPoint
from app.mcp.travel_data import search_pois

logger = logging.getLogger(__name__)

async def build_itinerary(request: BuildItineraryRequest) -> Itinerary:
    """
    Constructs a day-wise itinerary based on constraints.
    """
    if not request.city:
        logger.error("No city provided for itinerary")
        request.city = "Unknown City"
    
    if not request.days or request.days < 1:
        logger.warning(f"Invalid duration {request.days}, defaulting to 1 day")
        request.days = 1
        
    # 1. Fetch Candidates (Prioritizing must-visit places)
    weather_info = "Not available"
    city_summary = ""
    
    try:
        logger.info(f"Generating itinerary for {request.city} - {request.days} days")
        
        # Pre-fetch weather and context for Claude
        from app.services.free_travel_api import free_travel_service
        try:
            weather_data = await free_travel_service.get_weather_forecast(request.city, days=request.days)
            if weather_data and "days" in weather_data:
                weather_info = ", ".join([f"{d['date']}: {d['weather']} ({d['temp_max']}°C)" for d in weather_data["days"][:3]])
            
            city_summary = await free_travel_service.get_wikipedia_summary(request.city)
        except Exception as we:
            logger.warning(f"Could not fetch weather/summary: {we}")

        # Search for general attractions
        pois = await search_pois(city=request.city, interests=request.interests, category="attractions")
        
        # If user has specific must-visit places, ensure they are included or added
        if request.must_visit:
            logger.info(f"Including specific must-visit places: {request.must_visit}")
            # We can use Claude or a targeted search to find these specific POIs
            from app.services.claude_api import generate_pois_with_claude
            must_visit_pois_data = await generate_pois_with_claude(request.city, interests=request.must_visit, category="attractions")
            if must_visit_pois_data:
                from app.mcp.travel_data import transform_raw_to_pois
                must_visit_pois = transform_raw_to_pois(must_visit_pois_data, "must-visit")
                # Put must-visit places at the beginning
                pois = must_visit_pois + pois
                
    except Exception as e:
        logger.error(f"Error fetching POIs: {e}")
        pois = []
    
    # 2. Create a fallback POI if we have no POIs at all
    if not pois or len(pois) == 0:
        logger.warning(f"No POIs found for {request.city}, using fallback")
        fallback_poi = POI(
            id="fallback-1",
            name=f"Explore {request.city}",
            category="exploration",
            description=f"Free time to explore {request.city} at your own pace. Discover local hidden gems and enjoy the atmosphere.",
            location=GeoPoint(lat=0.0, lon=0.0),
            average_duration_minutes=120,
            rating=4.5,
            details={"cost": "Free", "tips": "Try local street food!"}
        )
        pois = [fallback_poi]
    
    # 3. Distribute POIs across days (Initial draft)
    try:
        # Also fetch some dining options for the Evening slots
        restaurants = await search_pois(city=request.city, interests=request.interests, category="restaurants")
    except:
        restaurants = []
        
    days: List[DayItinerary] = []
    attraction_index = 0
    restaurant_index = 0
    
    for d in range(1, request.days + 1):
        blocks = []
        time_slots = ["Morning", "Afternoon", "Evening"]
        
        for slot in time_slots:
            if slot == "Evening" and restaurants:
                poi = restaurants[restaurant_index % len(restaurants)]
                restaurant_index += 1
            else:
                poi = pois[attraction_index % len(pois)]
                attraction_index += 1
                
            blocks.append(ItineraryBlock(
                time_block=slot,
                poi=poi,
                start_time="09:00 AM" if slot == "Morning" else "01:00 PM" if slot == "Afternoon" else "07:00 PM",
                end_time="12:00 PM" if slot == "Morning" else "05:00 PM" if slot == "Afternoon" else "10:00 PM",
                travel_time_from_previous="30 mins" if slot != "Morning" else None
            ))
        days.append(DayItinerary(day_number=d, blocks=blocks))

    # 4. Optional: Use Claude to curate the final result
    try:
        from app.services.claude_api import curate_itinerary_with_claude
        curated_itinerary = await curate_itinerary_with_claude(request, days, weather_info, city_summary)
        if curated_itinerary:
            logger.info("Successfully curated itinerary with Claude")
            return curated_itinerary
    except Exception as e:
        logger.error(f"Claude curation failed, using draft: {e}")

    logger.info(f"Successfully built draft itinerary with {len(days)} days")
    return Itinerary(
        trip_title=f"{request.days}-Day Adventure in {request.city}",
        summary_rationale="Initial draft based on your interests.",
        weather_forecast=weather_info,
        days=days,
        total_cost_estimate=request.budget
    )
