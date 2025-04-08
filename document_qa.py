import os
from openai import OpenAI
from typing import List, Dict, Any
import uuid

class DocumentQABot:
    def __init__(self, api_key: str = None):
        """Initialize the Document QA Bot with OpenAI client."""
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # Using GPT-4o which supports advanced context features
        self.messages = []
        self.documents = {}  # Store document references
        
    def add_document(self, document_content: str, document_name: str = None) -> str:
        """Add a document to the context."""
        doc_id = str(uuid.uuid4())
        doc_name = document_name or f"Document-{doc_id[:8]}"
        
        # Create document entity
        self.documents[doc_id] = {
            "id": doc_id,
            "name": doc_name,
            "content": document_content
        }
        
        # Notify the model about the new document via a system message
        self.messages.append({
            "role": "system",
            "content": f"Document '{doc_name}' (ID: {doc_id}) has been added to the context.",
            "context": [{
                "type": "document",
                "document": {
                    "id": doc_id,
                    "name": doc_name,
                    "content": document_content
                }
            }]
        })
        
        return doc_id
    
    def ask(self, question: str) -> str:
        """Ask a question about the documents in context."""
        # Add user question to message history
        self.messages.append({
            "role": "user",
            "content": question
        })
        
        # Collect all document context entities
        document_entities = []
        for doc_id, doc in self.documents.items():
            document_entities.append({
                "type": "document",
                "document": {
                    "id": doc_id,
                    "name": doc["name"],
                    "content": doc["content"]
                }
            })
        
        # Get completion with document context
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            context=document_entities if document_entities else None
        )
        
        answer = response.choices[0].message.content
        
        # Add response to message history
        self.messages.append({
            "role": "assistant",
            "content": answer
        })
        
        return answer
    
    def list_documents(self) -> List[Dict[str, str]]:
        """List all documents in the context."""
        return [{"id": doc_id, "name": doc["name"]} for doc_id, doc in self.documents.items()]
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the context."""
        if doc_id in self.documents:
            doc_name = self.documents[doc_id]["name"]
            del self.documents[doc_id]
            
            # Notify the model about document removal
            self.messages.append({
                "role": "system",
                "content": f"Document '{doc_name}' (ID: {doc_id}) has been removed from the context."
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
    answer1 = bot.ask("What products does Acme offer?")
    print(f"Q: What products does Acme offer?\nA: {answer1}\n")
    
    answer2 = bot.ask("When is the company planning to go public and what's the expected valuation?")
    print(f"Q: When is the company planning to go public?\nA: {answer2}\n")
    
    # Remove a document and ask again
    bot.remove_document(doc2_id)
    answer3 = bot.ask("What's Acme's IPO plan?")
    print(f"Q: What's Acme's IPO plan?\nA: {answer3}")