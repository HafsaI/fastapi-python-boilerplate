"""
Chat service with LangGraph workflow.
"""
from typing import TypedDict, List, Optional
from openai import OpenAI
import uuid
import json
from datetime import datetime

from app.core.config import settings
from app.core.logging import logger
from app.repositories.chat import ChatRepository
from app.services.workflow import WorkflowService
import copy

class ProductInfo(TypedDict):
    product: str
    country: str
    quantity: int


class ExtractedData(TypedDict):
    products: List[ProductInfo]
    status: str


class CustomerSession(TypedDict):
    message: str
    thread_id: str
    customer_id: str
    extracted_data: Optional[ExtractedData]
    is_complete: bool
    customer_session_id: int


class ChatService:
    """Service for handling chat workflows with LangGraph."""
    
    def __init__(self, chat_repository: ChatRepository = None):
        # Initialize OpenAI client
        api_key = settings.OPENAI_API_KEY or "your-openai-api-key"
        self.openai_client = OpenAI(api_key=api_key)
        self.customer_assistant_id = self._create_assistant()
        
        # Initialize chat repository
        self.chat_repository = chat_repository
        
        # Initialize workflow service
        self.workflow_service = WorkflowService()
    
    def _create_assistant(self) -> str:
        """Create OpenAI Assistant for extracting product information"""
        try:
            assistant_name = f"Product Information Extractor"
            
            assistant = self.openai_client.beta.assistants.create(
                name=assistant_name,
                instructions="""You are a helpful assistant that extracts product information from customer messages. 
                    Customers may mention one or multiple products in a single message, sometimes with incomplete details. 
                    Your tone should be natural, polite, and conversational. Avoid being overly formal, robotic, or using emojis. 
                    Keep responses short, clear, and friendly.  

                    Your goals:
                    1. Extract the following for each product mentioned in the customer's message:
                        - product name (e.g., "apples", "laptops", "phones")
                        - country of origin (e.g., "Kenya", "China", "USA")  
                        - quantity (the number requested)

                    2. CRITICAL: When the customer provides complete information for ALL mentioned products (product name, country, AND quantity), you MUST call the save_final_order tool immediately. This is the ONLY way to complete the order.

                    3. If any detail (product, country, or quantity) is missing for one or more products, ask follow-up questions in a conversational way.  
                        Examples:
                        - "I need laptops and phones from China" → "Got it! How many laptops and how many phones would you like from China?"  
                        - "I want to buy 5 laptops" → "Great! Could you let me know which country you'd like the laptops to come from?"  

                    4. Always be friendly and helpful in your responses. Never mention tools or technical details to the user.

                    IMPORTANT: You must call the save_final_order tool when you have all three pieces of information (product, country, quantity) for every product the customer wants to order.""",
                model="gpt-4o-mini",
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "save_final_order",
                        "description": "MANDATORY: Call this function immediately when you have complete information (product name, country, and quantity) for ALL products the customer wants to order. This function MUST be called to complete the order. Do not respond to the user without calling this function when you have all required information.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "items": {
                                    "type": "array",
                                    "description": "The list of ordered items with product, country, and quantity.",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "product": {"type": "string", "description": "The product name"},
                                            "country": {"type": "string", "description": "The country of origin"},
                                            "quantity": {"type": "number", "description": "The quantity requested"},
                                        },
                                        "required": ["product", "country", "quantity"],
                                    },
                                },
                            },
                            "required": ["items"],
                        },
                    },
                }]
            )
            logger.info(f"Created OpenAI assistant: {assistant.id}")
            return assistant.id
        except Exception as e:
            logger.error(f"Error creating assistant: {e}")
            return None
    
    def _parse_messages(self, messages_data):
        """Parse JSONB messages column - handles both string and object formats."""
        if messages_data:
            if isinstance(messages_data, str):
                return json.loads(messages_data)
            else:
                return messages_data
        else:
            return []
    
    def _extract_with_assistant(self, message: str, thread_id: str) -> tuple[dict, str]:
        """Extract information using OpenAI Assistant. Returns (extracted_data, response_text)"""
        try:
            # Use OpenAI thread from socket
            openai_thread_id = thread_id
            logger.info(f"Processing message with assistant {self.customer_assistant_id}: {message}")
            
            # Add message to thread
            self.openai_client.beta.threads.messages.create(
                thread_id=openai_thread_id,
                role="user",
                content=message
            )
            
            # Run the assistant
            run = self.openai_client.beta.threads.runs.create(
                thread_id=openai_thread_id,
                assistant_id=self.customer_assistant_id
            )
            
            # Wait for completion
            while run.status in ['queued', 'in_progress', 'cancelling']:
                run = self.openai_client.beta.threads.runs.retrieve(
                    thread_id=openai_thread_id,
                    run_id=run.id
                )
            
            logger.info(f"Run status after completion: {run.status}")
            
            # Handle tool calls when status is 'requires_action'
            if run.status == 'requires_action':
                logger.info("Tool call detected, processing...")
                # Submit tool outputs to continue the run
                tool_outputs = []
                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    if tool_call.function.name == 'save_final_order':
                        # Parse the tool call arguments
                        try:
                            tool_args = json.loads(tool_call.function.arguments)
                            items = tool_args.get('items', [])
                            
                            # Convert to the expected format
                            extracted_data = {
                                "products": items,
                                "status": "complete"
                            }
                            logger.info(f"Tool call processed successfully with {len(items)} items")
                            
                            # Submit empty tool output (we don't need to return anything to the assistant)
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": "success"
                            })
                            
                            # Continue the run
                            run = self.openai_client.beta.threads.runs.submit_tool_outputs(
                                thread_id=openai_thread_id,
                                run_id=run.id,
                                tool_outputs=tool_outputs
                            )
                            
                            # Wait for completion after submitting tool outputs
                            while run.status in ['queued', 'in_progress', 'cancelling']:
                                run = self.openai_client.beta.threads.runs.retrieve(
                                    thread_id=openai_thread_id,
                                    run_id=run.id
                                )
                            
                            # Get the final response after tool execution
                            if run.status == 'completed':
                                messages = self.openai_client.beta.threads.messages.list(
                                    thread_id=openai_thread_id
                                )
                                
                                if messages.data:
                                    message_content = messages.data[0].content
                                    response_text = ""
                                    
                                    # Look for text response
                                    for content in message_content:
                                        if hasattr(content, 'text') and content.text:
                                            response_text = content.text.value
                                            break
                                    
                                    # If no text response found, use a default
                                    if not response_text:
                                        response_text = "Perfect! I have all the information I need. We'll get back to you shortly with more details and pricing information."
                                    
                                    return extracted_data, response_text
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing tool call arguments: {e}")
                            return None, "I apologize, but I'm having trouble processing your message right now. Please try again."
            
            elif run.status == 'completed':
                # Get the response
                messages = self.openai_client.beta.threads.messages.list(
                    thread_id=openai_thread_id
                )
                
                if messages.data:
                    message_content = messages.data[0].content
                    
                    # Check if there's a tool call
                    tool_call_found = False
                    response_text = ""
                    print('message_content!!', message_content)
                    
                    for content in message_content:
                        # Check for tool calls
                        if hasattr(content, 'tool_calls') and content.tool_calls:
                            tool_call_found = True
                            tool_call = content.tool_calls[0]
                            if tool_call.function.name == 'save_final_order':
                                try:
                                    # Parse the tool call arguments
                                    tool_args = json.loads(tool_call.function.arguments)
                                    items = tool_args.get('items', [])
                                    
                                    # Convert to the expected format
                                    extracted_data = {
                                        "products": items,
                                        "status": "complete"
                                    }
                                    
                                    # Look for text response in other content blocks
                                    for other_content in message_content:
                                        if hasattr(other_content, 'text') and other_content.text:
                                            response_text = other_content.text.value
                                            break
                                    
                                    # If no text response found, use a default
                                    if not response_text:
                                        response_text = "Perfect! I have all the information I need. We'll get back to you shortly with more details and pricing information."
                                    
                                    return extracted_data, response_text
                                    
                                except json.JSONDecodeError as e:
                                    logger.error(f"Error parsing tool call arguments: {e}")
                                    return None, "I apologize, but I'm having trouble processing your message right now. Please try again."
                        
                        # Check for text content
                        elif hasattr(content, 'text') and content.text:
                            response_text = content.text.value
                    
                    # If no tool call was found, return the text response
                    if not tool_call_found and response_text:
                        return None, response_text
            
            return None, "I apologize, but I'm having trouble processing your message right now. Please try again."
            
        except Exception as e:
            logger.error(f"Error using assistant: {e}")
            return None, "I apologize, but I'm having trouble processing your message right now. Please try again."
    
    async def _get_model_response(self, session_info: CustomerSession) -> None:
        """Process message directly without workflow."""
        local_session_info = copy.deepcopy(session_info)
        message = local_session_info["message"]
        thread_id = local_session_info["thread_id"]
        
        try:
            # 1. Save User message to DB
            if self.chat_repository:
                session = await self.chat_repository.get_customer_session(thread_id, int(local_session_info["customer_id"]))
                local_session_info["customer_session_id"] = int(session.id)
                if session:
                    current_messages = self._parse_messages(session.messages)
                    current_messages.append({
                        "role": "user",
                        "content": message,
                    })
                    await self.chat_repository.insert_message(session.id, current_messages)
            
            # Use OpenAI Assistant
            extracted_data, response_text = self._extract_with_assistant(message, thread_id)
            logger.info(f"Assistant response: {response_text[:100]}...")
            
            if extracted_data and extracted_data.get("status") == "complete":
                # All information is available
                local_session_info["extracted_data"] = extracted_data
                local_session_info["response"] = response_text
                local_session_info["is_complete"] = True
                
                # Save ASSISTANT message and product requests
                await self._save_message_and_product_requests(local_session_info, session, role="assistant")
            else:
                # Assistant is asking for more information
                local_session_info["response"] = response_text
                local_session_info["extracted_data"] = extracted_data
                local_session_info["is_complete"] = False
                
                # Save ASSISTANT message
                await self._save_message(local_session_info, session, role="assistant")
        
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            local_session_info["response"] = "I apologize, but I'm having trouble processing your message right now. Please try again."
            local_session_info["extracted_data"] = None
            local_session_info["is_complete"] = False
            
            # Save ASSISTANT error message to DB
            if self.chat_repository:
                session = await self.chat_repository.get_customer_session(thread_id, int(local_session_info["customer_id"]))
                if session:
                    await self._save_message(local_session_info, session, role="assistant")
        return local_session_info
    
    async def _save_message_and_product_requests(self, session_info: CustomerSession, session, role: str = "assistant") -> None:
        """Save message and product requests in db."""
        if self.chat_repository:
            session_status = 2 if session_info["is_complete"] else 1
            current_messages = self._parse_messages(session.messages)
            current_messages.append({
                "role": role,
                "content": session_info["response"],
            })
            await self.chat_repository.insert_message(session.id, current_messages, session_status)
            
            # Insert products into product_requests table
            extracted_data = session_info["extracted_data"]
            if extracted_data and extracted_data.get("status") == "complete":
                products = extracted_data.get("products", [])
                if products:
                    try:
                        product_requests_data = []
                        for product in products:
                            product_request_data = {
                                "customer_session_id": session.id,
                                "product_name": product.get("product"),
                                "quantity": product.get("quantity", 0),
                                "country": product.get("country")
                            }
                            product_requests_data.append(product_request_data)
                        logger.info(f'product_data: {product_requests_data}')
                        created_requests = await self.chat_repository.create_multiple_product_requests(product_requests_data)
                        logger.info(f"Inserted {len(created_requests)} product requests for session {session.id}")
                    except Exception as e:
                        logger.error(f"Error inserting product requests: {e}")
    
    async def _save_message(self, session_info: CustomerSession, session, role: str = "assistant") -> None:
        """Save message in db."""
        if self.chat_repository:
            current_messages = self._parse_messages(session.messages)
            current_messages.append({
                "role": role,
                "content": session_info["response"],
            })
            await self.chat_repository.insert_message(session.id, current_messages)
    
    async def process_customer_message(self, message: str, thread_id: str = None, customer_id: str = None, is_initial: bool = False) -> dict:
        """Process a customer message directly, only invoke workflow when complete."""
                
        #1. Create customer session info
        customer_session_info = CustomerSession(
            message=message,
            thread_id=thread_id,
            customer_id=customer_id,
            extracted_data=None,
            is_complete=False
        )
        
        # 2. Insert new session in DB
        if is_initial and self.chat_repository:
            try:
                result = await self.chat_repository.insert_session(
                    session_status=1,
                    thread_id=thread_id,
                    customer_id=int(customer_id) if customer_id else None
                )
                logger.info(f"Inserted session: {result.id}")
            except Exception as e:
                logger.error(f"Error inserting session: {e}")
        
        # 3. Get Model Response
        session_response = await self._get_model_response(customer_session_info)
        
        # 4. Check if conversation is complete [ Products Data Extracted ]
        if session_response["is_complete"]:
            self.workflow_service.trigger_workflow(session_response)
        
        logger.info(f"Processed message for thread {thread_id}: {session_response['response'][:100]}...")
        
        return {
            "message": session_response["message"],
            "thread_id": session_response["thread_id"],
            "customer_id": session_response["customer_id"],
            "extracted_data": session_response["extracted_data"],
            "response": session_response["response"],
            "is_complete": session_response["is_complete"]
        }

    def create_openai_thread(self) -> str:
        """Create a new one for the session"""        
        openai_thread_id = self.openai_client.beta.threads.create()
        logger.info(f"Created OpenAI thread: {openai_thread_id.id}")
        return openai_thread_id.id

    # GET APIS
    async def get_all_sessions(self, customer_id: str = None):
        """Get customer sessions with optional filtering by customer_id and pagination."""
        if customer_id:
            try:
                customer_id_int = int(customer_id)
                return await self.chat_repository.get_by_customer_id(customer_id_int)
            except ValueError:
                return []
    
    async def get_session_by_id(self, session_id: int):
        """Get a specific session by ID."""
        return await self.chat_repository.get(session_id)