# Location Calculation & Google Search Fix

## 🔍 Current Implementation

The system includes `google_search` as a built-in Gemini tool:

```python
# From backend/TARS.py line 183
tools = [{'google_search': {}}, {"function_declarations": [...]}]
```

This is a **built-in Gemini feature** that allows the AI to search Google for information.

## ⚠️ The Problem

**Location calculation** might not be working because:

1. **Google Search Tool Limitations**: The basic `google_search` tool may not have access to location-based APIs
2. **No Google Maps Integration**: The system doesn't currently include Google Maps API for geolocation
3. **Missing API Key**: If location features require Google Maps API, you need a separate API key

## 🔑 API Key Requirements

### For Basic Google Search
- **Status**: ✅ **Works with just GEMINI_API_KEY**
- The `google_search` tool is included in Gemini and works with your existing `GEMINI_API_KEY`
- No additional setup needed

### For Location/Geolocation Features
- **Status**: ❌ **Requires Google Maps API Key**
- If you need actual location calculations, distances, maps, etc., you need:
  - **Google Maps API Key** (separate from Gemini API key)
  - Enable these APIs in Google Cloud Console:
    - Geocoding API
    - Maps JavaScript API
    - Places API (if needed)
    - Distance Matrix API (for distance calculations)

## 🛠️ How to Fix Location Calculation

### Option 1: Use Google Search (Current - No Extra Setup)

The `google_search` tool can answer location questions, but it's limited:

**What it CAN do:**
- Search for "distance between New York and Los Angeles"
- Find "restaurants near me" (if location is in search query)
- General location information

**What it CANNOT do:**
- Calculate precise distances between coordinates
- Get your current location automatically
- Real-time geolocation services
- Map rendering

### Option 2: Add Google Maps API (Recommended for Location Features)

If you need actual location calculations, add Google Maps API:

#### Step 1: Get Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable these APIs:
   - **Geocoding API** (convert addresses ↔ coordinates)
   - **Maps JavaScript API** (optional, for frontend maps)
   - **Distance Matrix API** (calculate distances)
   - **Places API** (find places, if needed)

4. Create API Key:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy the key

5. (Optional) Restrict the key to specific APIs for security

#### Step 2: Add to .env File

Add to your `.env` file in project root:

```bash
# Existing
GEMINI_API_KEY=your_gemini_key_here

# Add this for location features
GOOGLE_MAPS_API_KEY=your_maps_api_key_here
```

#### Step 3: Create Location Agent (Optional)

Create `backend/location_agent.py`:

```python
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

class LocationAgent:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            print("[LOCATION] Warning: GOOGLE_MAPS_API_KEY not set")
    
    async def geocode(self, address: str):
        """Convert address to coordinates."""
        if not self.api_key:
            return None
        
        url = f"https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                if data["status"] == "OK" and data["results"]:
                    location = data["results"][0]["geometry"]["location"]
                    return {
                        "lat": location["lat"],
                        "lng": location["lng"],
                        "formatted_address": data["results"][0]["formatted_address"]
                    }
        return None
    
    async def calculate_distance(self, origin: str, destination: str):
        """Calculate distance between two locations."""
        if not self.api_key:
            return None
        
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": origin,
            "destinations": destination,
            "key": self.api_key,
            "units": "imperial"  # or "metric"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                if data["status"] == "OK" and data["rows"]:
                    element = data["rows"][0]["elements"][0]
                    if element["status"] == "OK":
                        return {
                            "distance": element["distance"]["text"],
                            "duration": element["duration"]["text"],
                            "distance_meters": element["distance"]["value"]
                        }
        return None
```

#### Step 4: Add Tool Definition

In `backend/TARS.py`, add:

```python
location_tool = {
    "name": "calculate_location",
    "description": "Calculates distances between locations or converts addresses to coordinates using Google Maps.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "operation": {
                "type": "STRING",
                "description": "Operation: 'geocode' (address to coordinates) or 'distance' (distance between two places)"
            },
            "address": {
                "type": "STRING",
                "description": "Address for geocoding (for 'geocode' operation)"
            },
            "origin": {
                "type": "STRING",
                "description": "Starting location (for 'distance' operation)"
            },
            "destination": {
                "type": "STRING",
                "description": "Destination location (for 'distance' operation)"
            }
        },
        "required": ["operation"]
    }
}

# Add to tools list (line 183)
tools = [
    {'google_search': {}}, 
    {"function_declarations": [
        generate_cad, run_web_agent, ..., location_tool  # ADD HERE
    ] + tools_list[0]['function_declarations'][1:]}
]
```

#### Step 5: Add Handler

In `backend/TARS.py` `receive_audio()` method, add handler:

```python
elif fc.name == "calculate_location":
    operation = fc.args.get("operation")
    
    if operation == "geocode":
        address = fc.args.get("address")
        result = await self.location_agent.geocode(address)
        if result:
            result_msg = f"Location: {result['formatted_address']} ({result['lat']}, {result['lng']})"
        else:
            result_msg = f"Could not find location for: {address}"
    
    elif operation == "distance":
        origin = fc.args.get("origin")
        destination = fc.args.get("destination")
        result = await self.location_agent.calculate_distance(origin, destination)
        if result:
            result_msg = f"Distance: {result['distance']}, Duration: {result['duration']}"
        else:
            result_msg = f"Could not calculate distance between {origin} and {destination}"
    
    function_response = types.FunctionResponse(
        id=fc.id, name=fc.name, response={"result": result_msg}
    )
    function_responses.append(function_response)
```

#### Step 6: Initialize Agent

In `backend/TARS.py` `AudioLoop.__init__()`:

```python
from location_agent import LocationAgent

# In __init__:
self.location_agent = LocationAgent()
```

## 🧪 Testing

### Test Google Search (Current)
```
You: "What's the distance between New York and Los Angeles?"
TARS: [Uses google_search tool, provides answer from search results]
```

### Test Location Agent (After Setup)
```
You: "Calculate the distance between New York and Los Angeles"
TARS: [Uses calculate_location tool, gets precise distance from Google Maps API]
```

## 💰 Cost Considerations

### Google Search (via Gemini)
- ✅ **Free** - Included with Gemini API
- Uses your existing `GEMINI_API_KEY`

### Google Maps API
- 💵 **Paid** - But has free tier
- **Free Tier**: $200 credit/month (covers ~40,000 requests)
- **Pricing**: 
  - Geocoding: $5 per 1,000 requests
  - Distance Matrix: $5 per 1,000 requests
  - Most users stay within free tier

## 🔍 Troubleshooting

### Issue: "Location calculation not working"

**Check:**
1. Is `GOOGLE_MAPS_API_KEY` set in `.env`?
2. Are the required APIs enabled in Google Cloud Console?
3. Is the API key restricted? (Try removing restrictions temporarily)
4. Check API quotas in Google Cloud Console

### Issue: "Google Search works but location doesn't"

**Solution:**
- Google Search ≠ Google Maps API
- You need separate API key for location calculations
- Follow Option 2 above

### Issue: "API key invalid"

**Solution:**
1. Verify key is copied correctly (no extra spaces)
2. Check API is enabled in Google Cloud Console
3. Check billing is enabled (required even for free tier)
4. Verify key restrictions allow your IP/domain

## 📝 Summary

- **Current**: `google_search` works with just `GEMINI_API_KEY` (basic search)
- **For Location**: Need `GOOGLE_MAPS_API_KEY` + Location Agent implementation
- **Cost**: Google Search = Free, Maps API = Free tier available
- **Setup**: Add Maps API key to `.env` and implement Location Agent (optional)

The `google_search` tool is already working - if you need actual location calculations, you'll need to add Google Maps API support as described above.


