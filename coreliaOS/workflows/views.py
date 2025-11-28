from django.shortcuts import get_object_or_404
from coreliaOS.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.core.serializers import serialize
import openai
import json
import os
import base64


@require_http_methods(["GET"])
def helloworld(request):
    """Workflow hello world API"""
    try:
        user = request.user
        
        return JsonResponse({
            'success': True,
            'data': {
                'message': 'Hello, world!',
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    

@require_http_methods(["POST"])
@csrf_exempt
@login_required
def marketing_workflow(request):
    """Knowledge base dashboard API"""
    try:
        user = request.user
        payload = json.loads(request.body.decode("utf-8"))

        # Extract user input and brand details from payload
        user_input = payload.get("user_input", "")
        brand_details = payload.get("brand_details", "")

        # Construct system prompt
        system_prompt = (
            "##Role:\n"
            "You are a visual branding expert and prompt engineer who creates highly effective image generation prompts for OpenAI Image Generation. "
            "Your job is to turn a brand’s visual identity and a user’s content goal into a precise, clean prompt that generates an Instagram post image.\n\n"
            "You avoid gibberish text by clearly specifying any real text as embedded in the scene and explicitly instructing not to generate illegible or filler text.\n\n"
            "You always preserve the brand’s identity (colors, tone, layout style) and use simple, visual language that can be understood.\n\n"
            "##Instructions:\n"
            "Using the user content goal and brand info below, generate a  detailed prompt describing the image to be created. Include:\n\n"
            "- Place text clearly in visual elements like signs, speech bubbles, posters, or titles\n"
            "- Layout (e.g. two-section infographic, quote card, list post, photo-style ad, etc.)\n"
            "- Clear visual composition\n"
            "- Scene description and tone (e.g. clean, modern, bold)\n"
            "- Any **real text** that should appear (in quotes, and not too much)\n"
            "- Ensure all real text has correct grammar and spelling. Never paraphrase or auto-generate key terms (e.g. \"illiquidity\", \"secondary sales\") — use them exactly as provided.\n"
            "- Include only 2-3 pieces of text, in double quotes. Keep them short and simple.\n"
            "- Clearly state: “no fake or gibberish text”\n"
            "- Use only clean props like a person at a desk or person holding a document — avoid too many icons like arrows, or graphs unless explicitly needed.\n\n"
            "-Make sure the prompt ends up producing a clean, minimal Instagram-style post that looks branded and aligned to the content goal.\n"
            "-Make sure you generate unique prompts for each image generation\n\n"
            f"##User Input\nContent goal:   {user_input}\nBrand details:    {brand_details}\n"
        )

        # Prepare OpenAI API call
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": 'Generate a prompt for an Instagram post based on the user input and brand details provided.'}
            ],
            max_tokens=512,
            temperature=0.7,
        )

        ai_reply = response.choices[0].message.content.strip()

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=ai_reply,
            tools=[{"type": "image_generation"}],
        )

        # Save the image to a file
        image_data = [
            output.result
            for output in response.output
            if output.type == "image_generation_call"
        ]
            
        if image_data:
            image_base64 = image_data[0]
            with open("otter.png", "wb") as f:
                f.write(base64.b64decode(image_base64))

        return JsonResponse({
            'success': True,
            'data': {
                'message': ai_reply,
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
