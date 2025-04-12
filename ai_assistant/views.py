import httpx
from django.shortcuts import render, redirect, get_object_or_404
import json
import requests
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db import models  # For aggregation queries
from .models import ChatSession, ChatMessage
from projects.models import Project, Skill, Category
import asyncio
from asgiref.sync import async_to_sync


# -------------------------
# Constants and Helper Functions
# -------------------------

PROJECT_CHARTER = """
Topic in Three Languages
ScholarHub. The ScholarHub is a website designed to connect students, researchers, and professionals based on their interests, expertise, and ongoing projects.
ScholarHub. ScholarHub — это веб-сайт, предназначенный для соединения студентов, исследователей и профессионалов на основе их интересов, экспертизы и текущих проектов.
ScholarHub. ScholarHub — бұл студенттерді, зерттеушілер мен мамандарды олардың қызығушылықтары, тәжірибесі және ағымдағы жобалары негізінде байланыстыратын веб-сайт.

Project Mission
The ScholarHub aims to address the challenges faced by researchers and professionals in the fragmented research ecosystem. By providing an AI-powered platform for collaboration, the project will break down geographic and disciplinary barriers, facilitate the discovery of suitable collaborators, and promote efficient knowledge sharing. This project aligns with ScholarHub’s mission to enhance the global research community's efficiency and innovation.

Project Objectives
- To develop an AI-powered researcher matching system that connects users based on interests, expertise, and project needs.
- To create a dynamic research project marketplace for sharing and discovering research opportunities.
- To build a resource hub offering curated tools, datasets, and tutorials to support research activities.
- To promote interdisciplinary and global collaboration, breaking down geographic and disciplinary barriers.
"""
import os
api_key = os.getenv("OPENROUTER_API_KEY")

def get_project_context_if_relevant(user_message: str) -> str:
    lower_msg = user_message.lower()
    keywords = ['scholarhub', 'project', 'research', 'collaborat', 'match']
    if any(keyword in lower_msg for keyword in keywords):
        return PROJECT_CHARTER
    return ""

def handle_db_query(message: str) -> str:
    lower_msg = message.lower()
    if "topic" in lower_msg and ("trend" in lower_msg or "hype" in lower_msg):
        trending_categories = Category.objects.annotate(
            project_count=models.Count('project')
        ).order_by('-project_count')[:5]
        if trending_categories:
            topics = ", ".join([cat.name for cat in trending_categories])
            return f"Trending topics: {topics}"
        else:
            return "No trending topics found."
    if "skill" in lower_msg and ("need" in lower_msg or "require" in lower_msg):
        needed_skills = Skill.objects.all().order_by('-id')[:5]
        if needed_skills:
            skills = ", ".join([skill.name for skill in needed_skills])
            return f"Top needed skills: {skills}"
        else:
            return "No skills data found."
    if "project" in lower_msg and ("new" in lower_msg or "latest" in lower_msg):
        new_projects = Project.objects.filter(is_active=True).order_by('-created_at')[:5]
        if new_projects:
            titles = ", ".join([proj.title for proj in new_projects])
            return f"New active projects: {titles}"
        else:
            return "No new projects found."
    return ""

from openai import OpenAI
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def call_ai_model(user_message: str, conversation_history: list, image_file=None, image_url=None) -> dict:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key = api_key
    )

    # Build base message
    user_content = [{"type": "text", "text": user_message}]

    # Handle uploaded image
    if image_file:
        image_path = default_storage.save(f"chat_uploads/{image_file.name}", ContentFile(image_file.read()))
        full_image_url = default_storage.url(image_path)
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": full_image_url
            }
        })
    elif image_url:
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": image_url
            }
        })

    system_prompt = {
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": (
                    "You are ScholarHub Assistant — a personal AI research assistant built to support users of the ScholarHub platform. "
                    "Your purpose is to help students, researchers, and professionals with research guidance, collaboration matching, and navigating ScholarHub’s tools. "
                    "Always respond as ScholarHub Assistant, not DeepSeek or any other provider. If asked who you are, say:\n\n"
                    "'I'm your personal ScholarHub Assistant, here to help you with your research journey — from exploring trending topics to finding collaborators and tools.'"
                )
            }
        ]
    }
    print("🔐 DEBUG - API Key Loaded:", api_key)
    print("🔐 DEBUG - Referer:", os.getenv("OPENROUTER_REFERER"))
    if not api_key:
        return {"error": "OPENROUTER_API_KEY not set on server"}
    referer_header = os.getenv("OPENROUTER_REFERER", "https://scholarhub.kz/")

    full_history = [system_prompt] + conversation_history
    full_history.append({
        "role": "user",
        "content": user_content
    })

    try:
        completion = client.chat.completions.create(
            model="google/gemini-2.0-flash-001",  # or any OpenRouter-supported model
            messages=full_history,
            extra_headers={
                "HTTP-Referer": referer_header,
                "X-Title": "ScholarHub"
            }
        )
        return {
            "choices": [{
                "message": {
                    "content": completion.choices[0].message.content
                }
            }]
        }

    except Exception as e:
        return {"error": str(e)}

# -------------------------
# Views
# -------------------------

@login_required
def ai_home(request):
    chat_sessions = ChatSession.objects.filter(user=request.user).order_by('-started_at')
    current_session = ChatSession.objects.filter(user=request.user).last()
    chat_history = current_session.messages.order_by('timestamp') if current_session else []

    context = {
        'chat_sessions': chat_sessions,
        'chat_history': chat_history,
    }
    return render(request, 'ai_home.html', context)

@login_required
def load_chat(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    messages = session.messages.order_by('timestamp').values(
        'content', 'sender', 'timestamp'
    )
    return JsonResponse({
        'messages': list(messages)
    })

@login_required
def new_chat(request):
    ChatSession.objects.create(user=request.user)
    return redirect('ai_assistant:ai_home')

@csrf_exempt
@require_POST
@login_required
def research_assistant_chat(request):
    user_message = request.POST.get('message', '')
    image_url = request.POST.get('image_url')
    image_file = request.FILES.get('image')

    if not user_message and not image_url and not image_file:
        return JsonResponse({"error": "No message or image provided."}, status=400)

    chat_session = ChatSession.objects.filter(user=request.user).order_by('-started_at').first()
    if not chat_session:
        chat_session = ChatSession.objects.create(user=request.user)

    ChatMessage.objects.create(session=chat_session, sender='user', content=user_message)

    conversation_history = []
    project_context = get_project_context_if_relevant(user_message)
    if project_context:
        conversation_history.append({
            "role": "system",
            "content": [{"type": "text", "text": project_context}]
        })

    for msg in chat_session.messages.order_by('timestamp'):
        conversation_history.append({
            "role": msg.sender,
            "content": [{"type": "text", "text": msg.content}]
        })

    response_data = call_ai_model(user_message, conversation_history, image_file=image_file, image_url=image_url)
    content = response_data.get("choices", [{}])[0].get("message", {}).get("content") or response_data.get("error", "No reply received")

    ChatMessage.objects.create(session=chat_session, sender='assistant', content=content)
    return JsonResponse({"message": content})

@csrf_exempt
@login_required
def research_assistant_stream(request):
    if request.method != 'POST':
        return StreamingHttpResponse("Only POST allowed", status=405)

    user_message = request.POST.get('message', '')
    if not user_message:
        return StreamingHttpResponse("No message provided", status=400)

    async def async_event_stream():
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream("POST", "https://openrouter.ai/api/v1/chat/completions", json={
                    "model": "deepseek/deepseek-r1:free",
                    "stream": True,
                    "messages": [{"role": "user", "content": user_message}]
                }, headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                yield "data: [DONE]\n\n"
                                return
                            try:
                                obj = json.loads(data_str)
                                token = obj["choices"][0].get("delta", {}).get("content", "")
                                if token:
                                    yield f"data: {json.dumps(token)}\n\n"
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                yield f"data: {json.dumps('Error: ' + str(e))}\n\n"

    # ✅ Convert async generator into sync-compatible
    sync_stream = async_to_sync(lambda: async_event_stream())()
    return StreamingHttpResponse(sync_stream, content_type='text/event-stream')