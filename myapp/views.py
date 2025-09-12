from django.shortcuts import render, redirect, get_object_or_404
from django.http import StreamingHttpResponse, JsonResponse
from .models import ChatSession, Message
import google.generativeai as genai
import os
import json
import re

# Configure Gemini API
try:
    genai.configure(api_key="AIzaSyAJOqc2wcbilqPeq5NOXqMThoMYEVvjNaA")
except Exception as e:
    print(f"Error configuring Gemini API: {e}")

# ---------------------- NEW CHAT SESSION ----------------------
def new_chat_session(request):
    chat_session = ChatSession.objects.create()
    return redirect('chat_view', session_id=chat_session.id)

# ---------------------- CHAT VIEW ----------------------
def chat_view(request, session_id):
    chat_session = get_object_or_404(ChatSession, id=session_id)
    messages = chat_session.messages.all()
    message_history = [
        {"role": msg.role, "parts": [{"text": msg.content}]} for msg in messages
    ]
    return render(request, 'myapp/chat.html', {
        'session_id': session_id,
        'message_history_json': json.dumps(message_history)
    })

# ---------------------- GET RESPONSE ----------------------
def get_response(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message_content = data.get('message')
            session_id = data.get('session_id')
            history = data.get('history', [])

            if not all([user_message_content, session_id]):
                return JsonResponse({'error': 'Message or session ID missing'}, status=400)

            chat_session = get_object_or_404(ChatSession, id=session_id)

            # Save user message
            Message.objects.create(session=chat_session, role='user', content=user_message_content)

            # Add ChatMCA system identity
            system_instruction = {
                "role": "user",
                "parts": [{"text": "From now on, you are ChatMCA, an AI assistant developed by Prachi. Always refer to yourself as ChatMCA."}]
            }

            # Start chat with history + system role
            model = genai.GenerativeModel('gemini-1.5-flash')
            chat = model.start_chat(history=[system_instruction] + history)

            # Stream response
            response_stream = chat.send_message(user_message_content, stream=True)

            def stream_generator():
                full_bot_response = ""
                for chunk in response_stream:
                    if chunk.text:
                        full_bot_response += chunk.text
                        yield f"data: {json.dumps({'text': chunk.text})}\n\n"

                if full_bot_response:
                    Message.objects.create(session=chat_session, role='model', content=full_bot_response)

            return StreamingHttpResponse(stream_generator(), content_type='text/event-stream')

        except Exception as e:
            print(f"Error in get_response stream: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

# ---------------------- GET SUGGESTIONS ----------------------
def get_suggestions(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            history = data.get('history', [])

            if not history:
                return JsonResponse({'suggestions': []})

            # Add ChatMCA identity here too
            model = genai.GenerativeModel('gemini-2.5-pro')
            prompt = ("You are ChatMCA,developed and trained by Prachi. an AI assistant. ")

            full_prompt = [{"role": "user", "parts": [{"text": prompt}]}]
            response = model.generate_content(full_prompt + history)

            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                suggestions_str = json_match.group(0)
                suggestions = json.loads(suggestions_str)
                return JsonResponse({'suggestions': suggestions})
            else:
                return JsonResponse({'suggestions': []})

        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)