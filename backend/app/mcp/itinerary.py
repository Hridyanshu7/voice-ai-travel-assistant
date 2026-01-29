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
    
    # 2. Ensure enough unique POIs (No "Explore City" loops)
    # We need roughly 2 attractions per day (Morning/Afternoon) + 1 dinner spot
    needed_attractions = request.days * 2
    
    if len(pois) < needed_attractions:
        missing_count = needed_attractions - len(pois)
        logger.info(f"Insufficient POIs ({len(pois)}/{needed_attractions}). Generating {missing_count} more via Claude.")
        
        try:
            from app.services.claude_api import generate_pois_with_claude
            from app.mcp.travel_data import transform_raw_to_pois
            
            # Ask Claude specifically for 'hidden gems' or 'top rated' to fill gaps
            generated_data = await generate_pois_with_claude(
                request.city, 
                interests=request.interests, 
                category="attractions"
            )
            
            if generated_data:
                new_pois = transform_raw_to_pois(generated_data, "generated")
                # Filter out duplicates by name
                existing_names = {p.name.lower() for p in pois}
                for p in new_pois:
                    if p.name.lower() not in existing_names:
                        pois.append(p)
                        if len(pois) >= needed_attractions:
                            break
        except Exception as e:
            logger.error(f"Failed to generate backup POIs: {e}")

    # Fallback: If still empty (API down + Claude fail), use a generic list but distinct ones
    if not pois:
        pois = [
            POI(id="fb1", name=f"Old Town {request.city}", category="walking", description="Historic center walk", location=GeoPoint(lat=0,lon=0)),
            POI(id="fb2", name=f"{request.city} City Park", category="nature", description="Central park visit", location=GeoPoint(lat=0,lon=0)),
            POI(id="fb3", name=f"{request.city} Museum", category="culture", description="Main cultural museum", location=GeoPoint(lat=0,lon=0))
        ]

    # 3. Distribute POIs across days
    try:
        restaurants = await search_pois(city=request.city, interests=request.interests, category="restaurants")
        # If no restaurants, generate some!
        if not restaurants:
             from app.services.claude_api import generate_pois_with_claude
             from app.mcp.travel_data import transform_raw_to_pois
             r_data = await generate_pois_with_claude(request.city, interests=["local food"], category="restaurants")
             if r_data:
                 restaurants = transform_raw_to_pois(r_data, "generated-food")
    except:
        restaurants = []
        
    days: List[DayItinerary] = []
    
    # Create a safe iterator that doesn't repeat until exhausted
    poi_iter = iter(pois * (request.days + 1)) # Extend list just in case
    rest_iter = iter(restaurants * (request.days + 1)) if restaurants else None
    
    for d in range(1, request.days + 1):
        blocks = []
        time_slots = ["Morning", "Afternoon", "Evening"]
        
        for slot in time_slots:
            current_poi = None
            
            if slot == "Evening":
                if rest_iter:
                    try:
                        current_poi = next(rest_iter)
                    except StopIteration:
                        pass
                
                # If no restaurant, try to grab a night attraction or fallback
                if not current_poi:
                     current_poi = POI(id=f"dinner-{d}", name="Local Dinner Experience", category="food", description="Enjoy local cuisine at a nearby rated restaurant.", location=GeoPoint(lat=0,lon=0))
            else:
                # Morning / Afternoon
                try:
                    current_poi = next(poi_iter)
                except StopIteration:
                    # Should unlikely happen due to list extension, but safe fallback
                    current_poi = pois[0] if pois else None
            
            if current_poi:
                blocks.append(ItineraryBlock(
                    time_block=slot,
                    poi=current_poi,
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
