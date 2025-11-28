from django.http import JsonResponse
from coreliaOS.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from django.core.exceptions import ValidationError
import json
from .models import CreateGroupModel
from .langgraph.agent_router import process_tagged_message
from knowledge_base.models import AIAgent, Conversation
from knowledge_base.views import agent_executor
from django.contrib.auth.models import User
from django.db.models import Q
import logging
from .serializers import *
from django.db import transaction
from django.shortcuts import get_object_or_404
import re

logger = logging.getLogger(__name__)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_agent_group(request):
    """Create a new agent group for the logged-in user"""
    try:
        data = json.loads(request.body)

        # Validate required fields
        required_fields = ['name', 'agent_labels']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)

        # Validate agent_labels is a list
        agent_labels = data['agent_labels']
        if not isinstance(agent_labels, list):
            return JsonResponse({
                'success': False,
                'error': 'agent_labels must be a list'
            }, status=400)

        # Fetch user agents with case-insensitive matching
        user_agents = AIAgent.objects.filter(user=request.user)
        valid_agent_names = set(user_agents.values_list('name', flat=True))
        
        # Perform case-insensitive validation
        invalid_labels = []
        for label in agent_labels:
            if not any(label.lower() == name.lower() for name in valid_agent_names):
                invalid_labels.append(label)
        
        if invalid_labels:
            return JsonResponse({
                'success': False,
                'error': f'Invalid agent labels: {", ".join(invalid_labels)}',
                'debug': {
                    'provided_labels': agent_labels,
                    'valid_agent_names': list(valid_agent_names),
                    'username': request.user.username
                }
            }, status=400)

        # Create the agent group
        group = CreateGroupModel.objects.create(
            user=request.user,
            name=data['name'],
            agent_labels=agent_labels,
        )

        return JsonResponse({
            'success': True,
            'data': model_to_dict(group, fields=['grp_id', 'name', 'agent_labels', 'created_at', 'updated_at']),
            'message': 'Agent group created successfully'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def get_agent_group(request):
    """
    Retrieve details of an agent group by grp_id for the logged-in user.
    Expects JSON payload: {"grp_id": "363a004e-f5f9-4297-a9a1-27a3dd5d31e3"}
    Returns: {"grp_id": "<uuid>", "name": "<name>", "agents": ["agent1", "agent2"]}
    """
    try:
        data = json.loads(request.body)
        logger.info(f"Request data: {data}")

        serializer = GetGroupSerializer(data=data, context={'request': request})
        if not serializer.is_valid():
            logger.error(f"Serializer errors: {serializer.errors}")
            return JsonResponse({
                'success': False,
                'error': serializer.errors
            }, status=400)

        group_data = serializer.get_group_data()
        logger.info(f"Group data retrieved: {group_data}")

        return JsonResponse({
            'success': True,
            'data': group_data,
            'message': 'Agent group retrieved successfully'
        })

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in get_agent_group: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def send_group_message(request):
    """
    Send a message to all agents in a group or a specific tagged agent using LangGraph.
    Expects JSON payload: {"grp_id": "<uuid>", "message": "<text or @agent_name text>", "conversation_id": "<uuid> (optional)"}
    Returns aggregated responses from group agents or a single tagged agent's response.
    """
    try:
        data = json.loads(request.body)
        grp_id = data.get('grp_id')
        message = data.get('message')
        conversation_id = data.get('conversation_id')

        if not grp_id or not message:
            logger.info("Missing grp_id or message in send_group_message request")
            return JsonResponse({
                'success': False,
                'error': 'Group ID and message are required'
            }, status=400)

        # Retrieve the group
        group = get_object_or_404(CreateGroupModel, grp_id=grp_id, user=request.user)
        logger.info(f"Found group {grp_id} for user {request.user.id}")

        # Check if the message contains an @agent_name tag
        tagged_agent = re.search(r'@(\w+)', message)
        if tagged_agent:
            # Use LangGraph flow for tagged messages
            logger.info(f"Detected tagged message: {message}")
            response = process_tagged_message(
                user_id=str(request.user.id),
                message=message,
                conversation_id=conversation_id
            )
            logger.info(f"Tagged message response: {response}")

            # Validate that the tagged agent is in the group
            agent_name = response.get('agent_name')
            if agent_name and agent_name.lower() not in [name.lower() for name in group.agent_labels]:
                logger.error(f"Tagged agent {agent_name} not in group {grp_id}")
                return JsonResponse({
                    'success': False,
                    'error': f"Agent {agent_name} is not in the group"
                }, status=400)

            return JsonResponse({
                'success': not response.get('error'),
                'data': {
                    'agent_name': response.get('agent_name'),
                    'response': response.get('response', ''),
                    'conversation_id': response.get('conversation_id'),
                    'context_docs': response.get('context_docs', []),
                    'usage': response.get('usage', {}),
                    'response_time': response.get('response_time', 0)
                },
                'error': response.get('error')
            })

        # Get agents from agent_labels
        agents = AIAgent.objects.filter(user=request.user, name__in=group.agent_labels, is_active=True)
        if not agents:
            logger.info(f"No valid agents found for group {grp_id}")
            return JsonResponse({
                'success': False,
                'error': 'No valid agents found in the group'
            }, status=400)

        # Check for existing conversation or create a new one
        conversation = None
        if conversation_id:
            conversation = get_object_or_404(
                Conversation, id=conversation_id, user=request.user
            )
            logger.info(f"Found conversation {conversation_id} for user {request.user.id}")
        else:
            with transaction.atomic():
                conversation = Conversation.objects.create(
                    user=request.user,
                    agent=agents[0],  # Link to the first agent
                    title=f"Group Chat: {group.name}"
                )
            logger.info(f"Created new conversation {conversation.id} for group {grp_id}")

        # Execute message for each agent
        responses = []
        for agent in agents:
            logger.info(f"Executing agent request for agent {agent.name}")
            response = agent_executor.execute_agent_request(agent, message, conversation)
            responses.append({
                'agent_name': agent.name,
                'response': response.get('content', ''),
                'error': response.get('error'),
                'context_docs': response.get('context_docs', []),
                'usage': response.get('usage', {}),
                'response_time': response.get('response_time', 0)
            })

        logger.info(f"Group responses for user {request.user.id}: {len(responses)} responses")

        return JsonResponse({
            'success': True,
            'data': {
                'agent_name': group.name,  # Use group name instead of agent_name
                'response': [r['response'] for r in responses],  # Aggregate responses
                'conversation_id': str(conversation.id),
                'context_docs': [doc for r in responses for doc in r['context_docs']],
                'usage': {agent.name: r['usage'] for agent in agents for r in responses if r['agent_name'] == agent.name},
                'response_time': sum(r['response_time'] for r in responses) / len(responses) if responses else 0
            },
            'error': None
        })

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in send_group_message: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)