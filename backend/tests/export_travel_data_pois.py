import sys
import os
import csv
import asyncio

# Add the backend directory to sys.path
start_path = os.path.dirname(os.path.abspath(__file__)) 
backend_path = os.path.dirname(start_path)            
sys.path.append(backend_path)

try:
    from app.mcp.travel_data import search_pois
    from app.mcp.models import POISearchRequest

    async def export_pois():
        # Cities defined in the mock DB
        cities = ["paris", "tokyo", "delhi", "jaipur"]
        
        filename = "travel_data_pois_export.csv"
        output_path = os.path.join(start_path, filename)
        
        print(f"Exporting POIs for: {', '.join(cities)}...")

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['city', 'id', 'name', 'category', 'rating', 'duration_min', 'description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for city in cities:
                # We need to call search_pois possibly with empty interests to get defaults?
                # The mock implementation returns everything for the city mostly, but let's check.
                # In mock implementation: it filters by city, interests are used for filtering? 
                # Actually looking at the code in previous turn (Step 430), it ignores interests for the main dict return:
                # `return mock_db[city]`
                # So we just need a valid request object.
                
                req = POISearchRequest(city=city, interests=[])
                try:
                    pois = await search_pois(req)
                    
                    for p in pois:
                        writer.writerow({
                            'city': city,
                            'id': p.id,
                            'name': p.name,
                            'category': p.category,
                            'rating': p.rating,
                            'duration_min': p.average_duration_minutes,
                            'description': p.description
                        })
                except Exception as e:
                    print(f"Error fetching {city}: {e}")

        print(f"Successfully exported POIs to: {output_path}")

    if __name__ == "__main__":
        asyncio.run(export_pois())

except Exception as e:
    print(f"Error setting up export: {e}")
