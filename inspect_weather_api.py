import httpx, asyncio

async def sample():
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.weather.gov/alerts/active", headers={"User-Agent": "test@example.com"})
        data = r.json()
        print(data["features"][0]["properties"].keys())

asyncio.run(sample())