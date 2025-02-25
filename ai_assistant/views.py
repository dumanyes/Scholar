# ai_assistant/views.py

from django.shortcuts import render
import json
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime


def ai_home(request):
    """
    Renders the AI Assistant home page.
    """
    context = {
        'current_time': datetime.now().strftime('%I:%M %p')
    }
    return render(request, 'ai_home.html', context)


@csrf_exempt  # For testing only—ensure proper CSRF protection in production!
@require_POST
def gemini_flash_chat(request):
    """
    A view that sends a chat message (with optional image URL) to the Gemini Flash2 model
    via OpenRouter and returns the response.
    """
    # Get the user's message from POST data
    user_message = request.POST.get('message', '').strip()
    if not user_message:
        return JsonResponse({"error": "No message provided."}, status=400)

    # Check if an image URL is provided (optional)
    image_url = request.POST.get('image_url', None)
    if image_url:
        content = [
            {
                "type": "text",
                "text": user_message
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": image_url
                }
            }
        ]
    else:
        content = [
            {
                "type": "text",
                "text": user_message
            }
        ]

    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ]
    }

    # API key and headers (update HTTP-Referer and X-Title as needed)
    api_key = "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"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://scholar-d6c0.onrender.com/",  # Update with your actual site URL
        "X-Title": "ScholarHub"  # Optional: your site name
    }

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid response from Gemini Flash2."}, status=500)

    return JsonResponse(data)