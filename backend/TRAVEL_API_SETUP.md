# Travel API Integration Setup Guide

## Required API Keys

### 1. Google Places API (Recommended - Best POI Data)
**Get your key:**
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable "Places API" and "Geocoding API"
4. Go to Credentials → Create API Key
5. Copy the key to `.env` as `GOOGLE_PLACES_API_KEY`

**Pricing:** $17/1000 requests (first $200/month free)

### 2. OpenTripMap API (Free - Tourist Attractions)
**Get your key:**
1. Go to https://opentripmap.io/product
2. Sign up for free account
3. Get API key from dashboard
4. Copy to `.env` as `OPENTRIPMAP_API_KEY`

**Pricing:** FREE (5000 requests/day)

### 3. Amadeus Travel API (Hotels & Flights)
**Get your key:**
1. Go to https://developers.amadeus.com/
2. Create free account
3. Create a new app in "My Self-Service Workspace"
4. Copy API Key and API Secret to `.env`

**Pricing:** FREE tier (2000 requests/month)

## Setup Instructions

1. **Update `.env` file:**
```bash
GOOGLE_PLACES_API_KEY=your_google_key_here
OPENTRIPMAP_API_KEY=your_opentripmap_key_here
AMADEUS_API_KEY=your_amadeus_key_here
AMADEUS_API_SECRET=your_amadeus_secret_here
```

2. **Install required package:**
```bash
pip install httpx
```

3. **Restart backend server**

## What Each API Provides

- **Google Places:** Restaurants, hotels, attractions, ratings, reviews, photos
- **OpenTripMap:** Historical sites, museums, monuments, cultural attractions
- **Amadeus:** Hotels, flights, booking information

## Fallback Strategy

The system will:
1. Try real APIs first
2. If API keys missing or quota exceeded → Use AI generation
3. Always provide data to the user

## Cost Estimate

For 1000 itineraries:
- Google Places: ~$10-20
- OpenTripMap: FREE
- Amadeus: FREE (within limits)

**Total: ~$10-20/month for production use**
