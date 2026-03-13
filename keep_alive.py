import os
import requests
import sys

def ping_render():
    render_url = os.environ.get("RENDER_URL")
    if not render_url:
        print("Error: RENDER_URL environment variable not set.")
        sys.exit(1)
    
    try:
        print(f"Pinging Render URL: {render_url}")
        response = requests.get(render_url, timeout=30)
        # We don't necessarily care about the status code as long as the request reached Render
        # because Render will wake up the service once it receives a request.
        print(f"Response status code: {response.status_code}")
        print("Successfully pinged Render.")
    except Exception as e:
        print(f"Error pinging Render: {e}")
        # sys.exit(1) # Optional: don't fail the whole action just if one ping fails

if __name__ == "__main__":
    ping_render()
