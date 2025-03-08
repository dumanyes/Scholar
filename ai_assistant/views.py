from django.shortcuts import render, redirect
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db import models  # For aggregation queries
from .models import ChatSession, ChatMessage
from projects.models import Project, Skill, Category

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

Project Scope/Deliverables:
- Development of the ScholarHub website.
- Integration of AI-powered matching algorithms using machine learning and NLP techniques.
- Creation of a project marketplace for collaboration opportunities.
- Development of a comprehensive resource hub for research tools, tutorials, and datasets.
- User authentication, profile management, and collaboration features.

Project Exclusions/Out-Of-Scope Items:
- Advanced analytics and AI beyond the matching system.
- Integration with external academic databases or publication platforms.
- Development of mobile app.

Project Roadmap:
- Project Planning & Requirements Gathering
- Platform Design & Prototyping
- Development of Core Features
- Testing & Refinement
- Presentation Preparation & Documentation

Assumptions:
- All team members have access to necessary resources.
- Team members will be available throughout the project timeline.
- The academic supervisor will provide necessary guidance.

Risks:
- Project timeline constraints due to academic responsibilities.
- Technical challenges with the AI matching system.
- Ambition exceeding available resources.
- Communication issues within the team.
"""

def get_project_context_if_relevant(user_message: str) -> str:
    """
    If the user's message seems related to ScholarHub project details,
    return a system prompt containing the full project charter.
    Otherwise, return an empty string.
    """
    lower_msg = user_message.lower()
    keywords = ['scholarhub', 'project', 'research', 'collaborat', 'match']
    if any(keyword in lower_msg for keyword in keywords):
        return PROJECT_CHARTER
    return ""

def handle_db_query(message: str) -> str:
    """
    Checks if the user message is asking for a known operation on the database.
    Returns a string result if an operation is matched; otherwise returns an empty string.
    """
    lower_msg = message.lower()

    # Example: "What topics are trending?" (interpreted as trending categories)
    if "topic" in lower_msg and ("trend" in lower_msg or "hype" in lower_msg):
        trending_categories = Category.objects.annotate(
            project_count=models.Count('project')
        ).order_by('-project_count')[:5]
        if trending_categories:
            topics = ", ".join([cat.name for cat in trending_categories])
            return f"Trending topics: {topics}"
        else:
            return "No trending topics found."

    # Example: "What skills are needed?" – from the Skill model.
    if "skill" in lower_msg and ("need" in lower_msg or "require" in lower_msg):
        needed_skills = Skill.objects.all().order_by('-id')[:5]  # Change ordering as needed.
        if needed_skills:
            skills = ", ".join([skill.name for skill in needed_skills])
            return f"Top needed skills: {skills}"
        else:
            return "No skills data found."

    # Example: "Show me new projects" – latest active projects.
    if "project" in lower_msg and ("new" in lower_msg or "latest" in lower_msg):
        new_projects = Project.objects.filter(is_active=True).order_by('-created_at')[:5]
        if new_projects:
            titles = ", ".join([proj.title for proj in new_projects])
            return f"New active projects: {titles}"
        else:
            return "No new projects found."

    return ""

def call_ai_model(user_message: str, conversation_history: list) -> JsonResponse:
    """
    Sends the conversation history (including the user message) to the external AI API.
    """
    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": conversation_history
    }
    api_key = "YOUR_API_KEY"  # Replace with your actual API key.
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Referer": "http://localhost:8000",  # Update with your actual domain if needed.
        "X-Title": "ScholarHub"
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

# -------------------------
# Views
# -------------------------

@login_required
def ai_home(request):
    """
    Renders the AI Assistant home page, loading the current chat history.
    """
    chat_history = []
    try:
        session = ChatSession.objects.get(user=request.user)
        chat_history = session.messages.order_by('timestamp')
    except ChatSession.DoesNotExist:
        pass
    context = {
        'current_time': datetime.now().strftime('%I:%M %p'),
        'chat_history': chat_history,
    }
    return render(request, 'ai_home.html', context)

@login_required
def new_chat(request):
    """
    Creates a new chat session for the user by deleting any existing session.
    Then redirects the user to the chat home page.
    """
    # Delete any existing chat session(s) for the user.
    ChatSession.objects.filter(user=request.user).delete()
    # Create a new session.
    ChatSession.objects.create(user=request.user)
    return redirect('ai_home')

@csrf_exempt  # For testing only – ensure proper CSRF protection in production!
@require_POST
@login_required
def gemini_flash_chat(request):
    """
    Processes the user’s chat message.
    1. Checks if the query matches a known database operation.
    2. If matched, queries the database directly and returns the result.
    3. Otherwise, constructs the conversation history (with optional project context)
       and sends it to the external AI API.
    """
    user_message = request.POST.get('message', '').strip()
    if not user_message:
        return JsonResponse({"error": "No message provided."}, status=400)

    # Check for known database operations.
    db_result = handle_db_query(user_message)
    if db_result:
        chat_session, _ = ChatSession.objects.get_or_create(user=request.user)
        ChatMessage.objects.create(session=chat_session, sender='user', content=user_message)
        ChatMessage.objects.create(session=chat_session, sender='assistant', content=db_result)
        return JsonResponse({
            "choices": [{
                "message": {
                    "content": db_result
                }
            }]
        })

    # Proceed with AI processing.
    chat_session, _ = ChatSession.objects.get_or_create(user=request.user)
    ChatMessage.objects.create(session=chat_session, sender='user', content=user_message)
    messages_qs = chat_session.messages.order_by('timestamp')

    # Optionally inject project context.
    project_context = get_project_context_if_relevant(user_message)

    conversation_history = []
    if project_context:
        conversation_history.append({
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": project_context
                }
            ]
        })

    # Append historical messages.
    for msg in messages_qs:
        conversation_history.append({
            "role": msg.sender,  # 'user' or 'assistant'
            "content": [
                {
                    "type": "text",
                    "text": msg.content
                }
            ]
        })

    # Attach an image if provided.
    image_url = request.POST.get('image_url', None)
    if image_url and conversation_history:
        conversation_history[-1]["content"].append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })

    # Send the conversation payload to the AI model.
    response_json = call_ai_model(user_message, conversation_history)
    # Extract assistant's reply (adjust based on actual API response structure).
    assistant_reply = response_json.json().get("reply", "No reply received")
    ChatMessage.objects.create(session=chat_session, sender='assistant', content=assistant_reply)
    return response_json
