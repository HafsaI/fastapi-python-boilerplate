"""
Workflow service for handling LangGraph workflows.
"""
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from app.core.logging import logger


class ProductInfo(TypedDict):
    product: str
    country: str
    quantity: int


class ChatbotState(TypedDict):
    customer_product_requests: List[ProductInfo]
    thread_id: str
    customer_id: str
    customer_session_id: int


class WorkflowService:
    """Service for handling LangGraph workflows."""
    
    def __init__(self):
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for completion handling only."""
        workflow = StateGraph(ChatbotState)
        
        # Add completion-specific nodes
        workflow.add_node("handle_scraping", self._handle_scraping)
        workflow.add_node("searching", self._searching)
        
        # Set entry point
        workflow.set_entry_point("handle_scraping")
        
        # Flow: scraping → searching → END
        workflow.add_edge("handle_scraping", "searching")
        workflow.add_edge("searching", END)
        
        return workflow.compile()
    
    def _handle_scraping(self, state: ChatbotState) -> ChatbotState:
        """Scraping Node:Handle Scraping Logic for the products requests."""
        try:
            thread_id = state["thread_id"]
            customer_session_id = state["customer_session_id"]
            logger.info(f"Scraping for thread_id={thread_id} and customer_session_id={customer_session_id}")
        except Exception as e:
            logger.error(f"Error in update_final_status: {e}")
        return state

    def _searching(self, state: ChatbotState) -> ChatbotState:
        """Post-process node: Vector DB Searching"""
        try:
            logger.info(f"Searching node: conversation completed. Products Requests::={state.get('customer_product_requests')}")
        except Exception as e:
            logger.error(f"Error in searching: {e}")
        return state
        
    def trigger_workflow(self, session_response: dict) -> None:
        """Trigger workflow when customer conversation is complete."""
        try:
            initial_state = ChatbotState(
                customer_product_requests=session_response.get('extracted_data').get('products'),
                thread_id=session_response.get('thread_id'),
                customer_id=session_response.get('customer_id'),
                customer_session_id=session_response.get('customer_session_id')
            )
            
            self.workflow.invoke(initial_state)
            logger.info(f"Completion workflow executed for thread_id={session_response.get('thread_id')}")
            
        except Exception as e:
            logger.error(f"Error in completion workflow: {e}")



##Workflow gets triggered only when customer conversation is complete.
##Entry Node: Scraping
##Second Node: Searching