from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any
from knowledge_base.models import AIAgent, Conversation
from knowledge_base.views import agent_executor
import re
import logging

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    user_id: str
    message: str
    conversation_id: str
    agent_name: str
    response: Dict[str, Any]

def extract_agent_name(state: AgentState) -> AgentState:
    """
    Extract agent name from message using @agent_name pattern.
    """
    logger.info(f"Extracting agent name from message: {state['message']}")
    match = re.search(r'@(\w+)', state['message'])
    if match:
        state['agent_name'] = match.group(1)
        # Remove @agent_name from message
        state['message'] = re.sub(r'@\w+', '', state['message']).strip()
    else:
        state['agent_name'] = None
    logger.info(f"Extracted agent_name: {state['agent_name']}")
    return state

def validate_agent(state: AgentState) -> AgentState:
    """
    Validate the extracted agent name exists for the user.
    """
    logger.info(f"Validating agent: {state['agent_name']}")
    if not state['agent_name']:
        state['response'] = {
            'error': 'No agent tagged in the message. Use @agent_name format.',
            'content': '',
            'context_docs': [],
            'usage': {},
            'response_time': 0
        }
        return state

    try:
        agent = AIAgent.objects.get(
            user_id=state['user_id'],
            name__iexact=state['agent_name'],
            is_active=True
        )
        logger.info(f"Found agent: {agent.name}")
        return state
    except AIAgent.DoesNotExist:
        logger.error(f"Agent {state['agent_name']} not found or inactive for user {state['user_id']}")
        state['response'] = {
            'error': f"Agent {state['agent_name']} not found or inactive",
            'content': '',
            'context_docs': [],
            'usage': {},
            'response_time': 0
        }
        return state

def route_to_agent(state: AgentState) -> AgentState:
    """
    Route the message to the specified agent using agent_executor.
    """
    if state.get('response') and state['response'].get('error'):
        return state

    logger.info(f"Routing to agent: {state['agent_name']}")
    agent = AIAgent.objects.get(
        user_id=state['user_id'],
        name__iexact=state['agent_name'],
        is_active=True
    )
    conversation = None
    if state['conversation_id']:
        conversation = Conversation.objects.get(
            id=state['conversation_id'],
            user_id=state['user_id'],
            agent=agent
        )
    else:
        conversation = Conversation.objects.create(
            user_id=state['user_id'],
            agent=agent,
            title=f"Chat with {agent.name}"
        )
        state['conversation_id'] = str(conversation.id)

    response = agent_executor.execute_agent_request(agent, state['message'], conversation)
    state['response'] = {
        'agent_name': agent.name,
        'response': response.get('content', ''),
        'error': response.get('error'),
        'context_docs': response.get('context_docs', []),
        'usage': response.get('usage', {}),
        'response_time': response.get('response_time', 0),
        'conversation_id': str(conversation.id)
    }
    logger.info(f"Agent response: {state['response']}")
    return state

def build_graph():
    """
    Build the LangGraph flow for agent tagging.
    """
    graph = StateGraph(AgentState)
    graph.add_node("extract_agent_name", extract_agent_name)
    graph.add_node("validate_agent", validate_agent)
    graph.add_node("route_to_agent", route_to_agent)

    graph.set_entry_point("extract_agent_name")
    graph.add_edge("extract_agent_name", "validate_agent")
    graph.add_edge("validate_agent", "route_to_agent")
    graph.add_edge("route_to_agent", END)

    return graph.compile()

# Initialize the graph
agent_router_graph = build_graph()

def process_tagged_message(user_id: str, message: str, conversation_id: str = None) -> Dict[str, Any]:
    """
    Process a message with @agent_name tag and return the response.
    """
    state = AgentState(
        user_id=user_id,
        message=message,
        conversation_id=conversation_id,
        agent_name=None,
        response={}
    )
    result = agent_router_graph.invoke(state)
    return result['response']