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

def call_ai_model(user_message: str, conversation_history: list) -> JsonResponse:
    """
    Sends the conversation history to the external AI API using DeepSeek R1 (free)
    for research assistance.
    """
    research_system_prompt = {
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": (
                    "You are ScholarHub Assistant — a personal AI research assistant built to support users of the ScholarHub platform. "
                    "Your purpose is to help students, researchers, and professionals with research guidance, collaboration matching, and navigating ScholarHub's tools. "
                    "Always respond as ScholarHub Assistant, not DeepSeek or any other provider. If asked who you are, say:\n\n"
                    "'I'm your personal ScholarHub Assistant, here to help you with your research journey — from exploring trending topics to finding collaborators and tools.'\n\n"
                    "Keep responses helpful, encouraging, and context-aware with regard to ScholarHub’s mission."
                )
            }
        ]
    }

    conversation = conversation_history.copy()
    conversation.insert(0, research_system_prompt)

    payload = {
        "model": "deepseek/deepseek-r1:free",
        "messages": conversation
    }
    api_key = "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"  # Replace with your actual API key.
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",  # Update with your actual site URL.
        "X-Title": "ScholarHub"
    }
    print("Payload being sent:", json.dumps(payload, indent=2))
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
        return JsonResponse({"error": "Invalid response from DeepSeek R1."}, status=500)
    return JsonResponse(data)

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
    # Create new session without deleting old ones
    ChatSession.objects.create(user=request.user)
    return redirect('ai_assistant:ai_home')


@csrf_exempt
@require_POST
@login_required
def research_assistant_chat(request):
    """
    Processes the user's chat message for research assistance using DeepSeek R1 (free).
    """
    user_message = request.POST.get('message', '').strip()
    if not user_message:
        return JsonResponse({"error": "No message provided."}, status=400)

    try:
        # Get the most recent chat session
        chat_session = ChatSession.objects.filter(user=request.user).latest('started_at')
    except ChatSession.DoesNotExist:
        # Create new session if none exists
        chat_session = ChatSession.objects.create(user=request.user)

    # Check for database queries first
    db_result = handle_db_query(user_message)
    if db_result:
        ChatMessage.objects.create(session=chat_session, sender='user', content=user_message)
        ChatMessage.objects.create(session=chat_session, sender='assistant', content=db_result)
        return JsonResponse({
            "choices": [{
                "message": {
                    "content": db_result
                }
            }]
        })

    # Process normal chat message
    ChatMessage.objects.create(session=chat_session, sender='user', content=user_message)

    # Build conversation history
    messages_qs = chat_session.messages.order_by('timestamp')
    conversation_history = []

    # Add project context if relevant
    project_context = get_project_context_if_relevant(user_message)
    if project_context:
        conversation_history.append({
            "role": "system",
            "content": [{"type": "text", "text": project_context}]
        })

    # Add historical messages
    for msg in messages_qs:
        conversation_history.append({
            "role": msg.sender,
            "content": [{"type": "text", "text": msg.content}]
        })

    # Handle image attachments
    image_url = request.POST.get('image_url', None)
    if image_url and conversation_history:
        conversation_history[-1]["content"].append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })

    # Call AI model
    response_json = call_ai_model(user_message, conversation_history)
    data = json.loads(response_json.content.decode('utf-8'))

    # Process response
    choices = data.get("choices", [])
    if choices:
        message_data = choices[0].get("message", {})
        content = message_data.get("content", "No reply received")
        assistant_reply = content
    else:
        assistant_reply = "No reply received"

    # Store and return response
    ChatMessage.objects.create(session=chat_session, sender='assistant', content=assistant_reply)
    return JsonResponse(data)

@csrf_exempt
@login_required
def research_assistant_stream(request):
    """
    Streams the AI model's chain-of-thought in real time using SSE (Server-Sent Events).
    """
    if request.method != 'POST':
        return StreamingHttpResponse("Only POST allowed", status=405)

    user_message = request.POST.get('message', '')
    if not user_message:
        # We can SSE a quick error, or just return 400
        return StreamingHttpResponse("No message provided", status=400)

    # SSE generator function
    def sse_stream():
        # Build your OpenRouter payload with stream=True
        payload = {
            "model": "deepseek/deepseek-r1:free",  # or any other streaming-capable model
            "stream": True,
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }
        headers = {
            "Authorization": "Bearer <OPENROUTER_API_KEY>",
            "Content-Type": "application/json"
        }

        try:
            # Make the streaming request
            with requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                stream=True  # requests will let us iterate chunk by chunk
            ) as r:
                r.raise_for_status()

                buffer = ""
                # We read partial lines as they come in
                for chunk in r.iter_content(chunk_size=1024, decode_unicode=True):
                    if not chunk:
                        continue
                    buffer += chunk

                    # We attempt to parse SSE lines from 'buffer'
                    while True:
                        line_end = buffer.find('\n')
                        if line_end == -1:
                            break

                        line = buffer[:line_end].strip()
                        buffer = buffer[line_end + 1:]

                        # SSE lines might start with 'data: '
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str == '[DONE]':
                                # The model finished streaming
                                yield "data: [DONE]\n\n"
                                return

                            # Attempt JSON parse
                            try:
                                data_obj = json.loads(data_str)
                                # The partial token might be in data_obj["choices"][0]["delta"]["content"]
                                # or data_obj["choices"][0]["delta"]["reasoning"] depending on your model
                                partial_token = ""
                                delta = data_obj["choices"][0]["delta"]

                                # If there's chain-of-thought or content
                                if "reasoning" in delta:
                                    # You can prefix or combine them
                                    partial_token += f"\n[Thinking: {delta['reasoning']}]"

                                if "content" in delta:
                                    partial_token += delta["content"]

                                if partial_token:
                                    # SSE send
                                    # Format: data: <partial_text>\n\n
                                    yield f"data: {json.dumps(partial_token)}\n\n"

                            except json.JSONDecodeError:
                                # Could be keep-alive or SSE comment
                                pass

        except requests.RequestException as e:
            # If there's a network error or 4xx/5xx from the AI
            # SSE an error message
            yield f"data: {json.dumps('Error: ' + str(e))}\n\n"

    # Return SSE
    response = StreamingHttpResponse(sse_stream(), content_type='text/event-stream')
    # SSE best practices
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
