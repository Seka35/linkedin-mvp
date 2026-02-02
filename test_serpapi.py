#!/usr/bin/env python3
"""Test SerpAPI connection"""
import os
import sys
sys.path.insert(0, '/app')

from dotenv import load_dotenv
import requests

load_dotenv('/app/.env')

serp_api_key = os.getenv('SERP_API_KEY')
print(f"SERP_API_KEY: {serp_api_key}")

if serp_api_key:
    print("🚀 Test SearchAPI.io...")
    url = "https://www.searchapi.io/api/v1/search"
    params = {
        "engine": "google",
        "q": "site:linkedin.com/in/ CEO Paris",
        "api_key": serp_api_key,
        "num": 5
    }
    try:
        response = requests.get(url, params=params, timeout=20)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                print(f"❌ API Error: {data['error']}")
            elif "organic_results" in data:
                print(f"✅ Found {len(data['organic_results'])} results")
                for r in data['organic_results'][:3]:
                    print(f"  - {r.get('link', 'N/A')}")
            else:
                print(f"⚠️ No organic_results in response")
                print(f"Keys: {list(data.keys())}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ SERP_API_KEY not found")
