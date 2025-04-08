import os
from anthropic import Anthropic
from typing import List, Dict, Any
import uuid

class DocumentQABot:
    def __init__(self, api_key: str = None):
        """Initialize the Document QA Bot with Anthropic client."""
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-3-7-sonnet-20250219"  # Using Claude 3.7 Sonnet with MCP support
        self.messages = []
        self.documents = {}  # Store document references
        self.context_entities = []  # Track active context entities
        
    def add_document(self, document_content: str, document_name: str = None) -> str:
        """Add a document to the context."""
        doc_id = str(uuid.uuid4())
        doc_name = document_name or f"Document-{doc_id[:8]}"
        
        # Create document entity
        document_entity = {
            "type": "document",
            "document": {
                "id": doc_id,
                "name": doc_name,
                "content": document_content
            }
        }
        
        # Store document reference
        self.documents[doc_id] = document_entity["document"]
        
        # Add to active context entities
        self.context_entities.append(document_entity)
        
        # Notify the model about the new document via a system message
        self.messages.append({
            "role": "assistant",
            "content": f"I've added the document '{doc_name}' to my context and can now answer questions about it."
        })
        
        return doc_id
    
    def ask(self, question: str) -> str:
        """Ask a question about the documents in context."""
        # Add user question to message history
        self.messages.append({
            "role": "user",
            "content": question
        })
        
        # Create a copy of messages to avoid modifying the original
        messages_for_request = self.messages.copy()
        
        # Get completion with document context using Model Context Protocol
        response = self.client.messages.create(
            model=self.model,
            messages=messages_for_request,
            context=self.context_entities if self.context_entities else None,
            max_tokens=1000
        )
        
        answer = response.content[0].text
        
        # Add response to message history
        self.messages.append({
            "role": "assistant",
            "content": answer
        })
        
        return answer
    
    def list_documents(self) -> List[Dict[str, str]]:
        """List all documents in the context."""
        return [{"id": doc["id"], "name": doc["name"]} for doc in [entity["document"] for entity in self.context_entities if entity["type"] == "document"]]
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the context."""
        for i, entity in enumerate(self.context_entities):
            if entity["type"] == "document" and entity["document"]["id"] == doc_id:
                doc_name = entity["document"]["name"]
                
                # Remove from context entities
                self.context_entities.pop(i)
                
                # Remove from documents dictionary
                if doc_id in self.documents:
                    del self.documents[doc_id]
                
                # Notify about document removal
                self.messages.append({
                    "role": "assistant",
                    "content": f"I've removed the document '{doc_name}' from my context."
                })
                return True
        return False


# Example usage
if __name__ == "__main__":
    bot = DocumentQABot()
    
    # Add a document
    doc1_id = bot.add_document("""
    # Company Overview
    Acme Corporation was founded in 2010 and specializes in AI solutions for healthcare.
    Our annual revenue reached $50 million in 2023, with a 25% year-over-year growth.
    
    ## Products
    - MedAssist: AI diagnostic tool
    - HealthTracker: Patient monitoring system
    - DocFlow: Medical documentation automation
    
    ## Leadership
    - CEO: Jane Smith
    - CTO: John Davis
    - CFO: Michael Johnson
    """, "Acme Company Overview")
    
    # Add another document
    doc2_id = bot.add_document("""
    # Q4 2023 Financial Report
    
    Acme Corporation closed Q4 with strong performance:
    - Revenue: $15.2 million (30% increase from Q3)
    - New customers: 45 hospitals and 120 clinics
    - MedAssist adoption up 40%
    
    ## Challenges
    - Supply chain issues delayed HealthTracker 2.0 release
    - Increasing competition in the medical AI space
    
    ## 2024 Outlook
    Planning IPO in Q3 2024 with estimated valuation of $500M
    """, "Q4 Financial Report")
    
    # Ask questions
    print("Asking first question...")
    answer1 = bot.ask("What products does Acme offer?")
    print(f"Q: What products does Acme offer?\nA: {answer1}\n")
    
    print("Asking second question...")
    answer2 = bot.ask("When is the company planning to go public and what's the expected valuation?")
    print(f"Q: When is the company planning to go public?\nA: {answer2}\n")
    
    # Remove a document and ask again
    print("Removing financial report document...")
    bot.remove_document(doc2_id)
    answer3 = bot.ask("What's Acme's IPO plan?")
    print(f"Q: What's Acme's IPO plan?\nA: {answer3}")