import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from urllib.parse import quote_plus
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Ab ye keys environment variables se aayengi
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "e68520eebb703f9f4031cc028428c420")  # tera weather key
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "f5b16d735a2f4d1fa36bcd035984106d")  # agar news API use karna ho

class GoalInput(BaseModel):
    goal: str
    locale: str = "IN"

@app.get("/manifest.json")
def get_manifest():
    manifest_path = os.path.join(os.path.dirname(__file__), "manifest.json")
    return FileResponse(manifest_path)

@app.get("/")
def read_root():
    return {"message": "GoalAction MCP Server is running!"}

def detect_goal_type(goal_text: str):
    text = goal_text.lower()
    if any(w in text for w in ["trip", "goa", "flight", "hotel", "travel", "vacation", "itinerary"]):
        return "travel"
    if any(w in text for w in ["learn", "course", "python", "java", "js", "programming", "study"]):
        return "learning"
    if any(w in text for w in ["lose weight", "diet", "workout", "exercise", "fitness"]):
        return "health"
    if any(w in text for w in ["news", "update", "headlines"]):
        return "news"
    return "general"

def get_weather_for_city(city: str):
    if not OPENWEATHER_KEY:
        return None
    try:
        q = quote_plus(city)
        url = f"https://api.openweathermap.org/data/2.5/weather?q={q}&units=metric&appid={OPENWEATHER_KEY}"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            return {"desc": desc, "temp_c": temp}
    except Exception:
        return None
    return None

def get_news_headlines():
    # Example using NewsAPI.org free plan (adjust URL as per your news provider)
    if not NEWS_API_KEY:
        return None
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            articles = data.get("articles", [])[:5]
            headlines = [{"title": a["title"], "url": a["url"]} for a in articles]
            return headlines
    except Exception:
        return None
    return None

def make_search_links_for_travel(origin: str, dest: str, locale="IN"):
    q_flights = f"https://www.google.com/travel/flights?q=flights+from+{quote_plus(origin)}+to+{quote_plus(dest)}"
    q_skyscanner = f"https://www.skyscanner.net/transport/flights/{quote_plus(origin)}/{quote_plus(dest)}"
    q_hotels = f"https://www.booking.com/searchresults.html?ss={quote_plus(dest)}"
    q_make_my_trip = f"https://www.makemytrip.com/flights/"
    return {
        "google_flights": q_flights,
        "skyscanner": q_skyscanner,
        "hotels_booking": q_hotels,
        "makemytrip": q_make_my_trip
    }

def youtube_search_link(query: str):
    return f"https://www.youtube.com/results?search_query={quote_plus(query)}"

@app.post("/plan")
def create_plan(data: GoalInput):
    goal = data.goal.strip()
    locale = (data.locale or "IN").upper()
    gtype = detect_goal_type(goal)

    response = {"goal": goal, "type": gtype, "plan": []}

    if gtype == "travel":
        parts = goal.split()
        dest = None
        for p in parts[::-1]:
            if p.lower() not in ("my","plan","trip","to","for","a","the","in","from"):
                dest = p
                break
        if not dest:
            dest = "Goa"

        weather = get_weather_for_city(dest)
        if weather:
            response["plan"].append({
                "step": f"Check current weather in {dest}",
                "info": f"{weather['desc']}, {weather['temp_c']}°C",
                "link": f"https://openweathermap.org/find?q={quote_plus(dest)}"
            })
        else:
            response["plan"].append({
                "step": f"Check weather in {dest}",
                "info": "Weather API not configured or unavailable",
                "link": f"https://www.google.com/search?q=weather+{quote_plus(dest)}"
            })

        origin = "Delhi" if locale == "IN" else "New York"
        links = make_search_links_for_travel(origin, dest, locale=locale)
        response["plan"].append({
            "step": "Search cheapest flights",
            "info": f"Search flights from {origin} to {dest}",
            "links": links
        })
        response["plan"].append({
            "step": "Find hotels near popular spots",
            "info": "Check Booking/Google for hotels and ratings",
            "link": links["hotels_booking"]
        })

        itinerary = [
            {"day": "Day 1", "plan": f"Arrive {dest}, relax at the main beach, local dinner"},
            {"day": "Day 2", "plan": "Sightseeing: old churches, spice plantation or option for water sports"},
            {"day": "Day 3", "plan": "Local markets, shopping & departure"}
        ]
        response["plan"].append({"step": "Suggested 3-day itinerary", "itinerary": itinerary})

        checklist = ["Sunscreen", "Light clothes", "Swimwear", "ID/Passport", "Phone charger"]
        response["plan"].append({"step": "Packing checklist", "items": checklist})

    elif gtype == "learning":
        text = goal.lower()
        subject = None
        for s in ("python","java","c++","data","sql","machine learning","ml","react","javascript"):
            if s in text:
                subject = s
                break
        if not subject:
            subject = "programming basics"

        resources = [
            {"title": f"Free course to learn {subject} (start here)", "link": youtube_search_link(f"{subject} tutorial for beginners")},
            {"title": "Recommended free text tutorial", "link": f"https://www.google.com/search?q={quote_plus(subject+' tutorial')}"}
        ]
        schedule = [
            {"day": 1, "task": f"Intro to {subject}: basics & setup, 2 hours"},
            {"day": 2, "task": "Core syntax & small examples, 3 hours"},
            {"day": 3, "task": "Practice problems & mini project, 3-4 hours"}
        ]
        response["plan"].append({"step": f"Recommended resources for {subject}", "resources": resources})
        response["plan"].append({"step": "Suggested 3-day schedule", "schedule": schedule})

    elif gtype == "health":
        response["plan"].append({"step": "Initial check", "info": "Note: This is general advice. For medical guidance consult a professional."})
        response["plan"].append({"step": "Diet (sample)", "info": "High protein breakfast, light carbs lunch, salad & protein dinner"})
        response["plan"].append({"step": "Workout (sample)", "info": "Day-wise split: Cardio + Core + Strength training (30-45 mins)"})
        response["plan"].append({"step": "Track progress", "tools": {"calorie_tracker": "https://www.google.com/search?q=calorie+calculator"}})

    elif gtype == "news":
        headlines = get_news_headlines()
        if headlines:
            response["plan"].append({"step": "Today's top news headlines", "headlines": headlines})
        else:
            response["plan"].append({"step": "News headlines unavailable", "info": "News API key missing or error."})

    else:
        response["plan"].append({"step": "Clarify the goal", "info": "Try to be specific: example 'Plan my Goa trip for 3 days with budget 15000'"})
        response["plan"].append({"step": "Quick web search", "link": f"https://www.google.com/search?q={quote_plus(goal)}"})
        response["plan"].append({"step": "Suggested next step", "info": "If you want I can generate a 5-step plan — ask again with more details."})

    return response
