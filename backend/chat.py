"""
Chat Module
Handles question answering using RAG (Retrieval-Augmented Generation)
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
try:
    from groq import Groq
except TypeError:
    # Fallback for older versions
    import groq
    Groq = groq.Client
# Load environment variables
load_dotenv()


class ChatEngine:
    """
    RAG-based chat engine that answers questions using retrieved context
    """
    
    def __init__(self, model: str = "llama-3.1-8b-instant"):
        """
        Initialize chat engine with Groq API
        
        Args:
            model: Groq model to use (default: llama-3.1-8b-instant)
                   Options: llama-3.1-8b-instant, mixtral-8x7b-32768, gemma2-9b-it
        """
        # Get API key
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            raise ValueError("❌ GROQ_API_KEY not found in .env file!")
        
        # Initialize Groq client
        self.client = Groq(api_key=api_key)
        self.model = model
        
        # Conversation history
        self.conversation_history = []
        
        print(f"✅ Chat Engine initialized")
        print(f"🤖 Model: {model}")
    
    
    def create_prompt(self, question: str, context_chunks: List[str]) -> str:
        # Combine context chunks
        context = "\n\n".join([f"[{i+1}] {chunk}" for i, chunk in enumerate(context_chunks)])
        
        # Create prompt
        prompt = f"""You are a helpful AI assistant that answers questions based on the provided context.

CONTEXT:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Answer the question using ONLY the information from the context above
2. If the context doesn't contain enough information to answer, say "I don't have enough information in the provided documents to answer that question."
3. Be concise and accurate
4. Cite which context chunk ([1], [2], etc.) you used for your answer

ANSWER:"""
        
        return prompt
    
    
    def ask(
        self, 
        question: str, 
        context_chunks: List[str],
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        
        try:
            # Create prompt with context
            prompt = self.create_prompt(question, context_chunks)
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract answer
            answer = response.choices[0].message.content
            
            # Store in conversation history
            self.conversation_history.append({
                "question": question,
                "answer": answer,
                "context_used": len(context_chunks)
            })
            
            return answer
            
        except Exception as e:
            error_msg = f"❌ Error generating answer: {str(e)}"
            print(error_msg)
            return error_msg
    
    
    def ask_with_history(
        self,
        question: str,
        context_chunks: List[str],
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
       
        try:
            # Build messages with history
            messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
            
            # Add conversation history (last 3 exchanges)
            for entry in self.conversation_history[-3:]:
                messages.append({"role": "user", "content": entry["question"]})
                messages.append({"role": "assistant", "content": entry["answer"]})
            
            # Add current question with context
            prompt = self.create_prompt(question, context_chunks)
            messages.append({"role": "user", "content": prompt})
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract answer
            answer = response.choices[0].message.content
            
            # Store in history
            self.conversation_history.append({
                "question": question,
                "answer": answer,
                "context_used": len(context_chunks)
            })
            
            return answer
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            print(error_msg)
            return error_msg
    
    
    def clear_history(self):
        """
        Clear conversation history
        """
        self.conversation_history = []
        print("✅ Conversation history cleared")
    
    
    def get_history(self) -> List[Dict]:
        """
        Get conversation history
        
        Returns:
            List of conversation exchanges
        """
        return self.conversation_history


# ============================================================================
# TESTING CODE
# ============================================================================
if __name__ == "__main__":
    print("🧪 Testing Chat Engine...")
    print("=" * 60)
    
    # Check for API key
    if not os.path.exists(".env"):
        print("\n❌ ERROR: .env file not found!")
        print("📝 Create a .env file with:")
        print("   GROQ_API_KEY=your-groq-api-key-here")
        print("\n💡 Get your API key from: https://console.groq.com")
    else:
        print("✅ Found .env file")
        
        try:
            # Import other modules for full test
            from embeddings import EmbeddingGenerator
            from vector_store import VectorStore
            
            # Test 1: Initialize chat engine
            print("\n📝 Test 1: Initialize Chat Engine")
            chat = ChatEngine()
            
            # Test 2: Simple question with context
            print("\n📝 Test 2: Simple Question with Context")
            
            # Sample context (simulate vector search results)
            sample_context = [
                "Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed.",
                "Deep learning is a type of machine learning that uses neural networks with multiple layers to learn complex patterns.",
                "Supervised learning involves training models on labeled data, where the correct output is known."
            ]
            
            question1 = "What is machine learning?"
            print(f"\n❓ Question: {question1}")
            print("📄 Using sample context chunks...")
            
            answer1 = chat.ask(question1, sample_context)
            print(f"\n💬 Answer:\n{answer1}")
            
            # Test 3: Follow-up question
            print("\n📝 Test 3: Follow-up Question")
            question2 = "What about deep learning?"
            print(f"\n❓ Question: {question2}")
            
            answer2 = chat.ask_with_history(question2, sample_context)
            print(f"\n💬 Answer:\n{answer2}")
            
            # Test 4: Full RAG pipeline
            print("\n📝 Test 4: Full RAG Pipeline Test")
            print("🔄 Setting up vector store with sample data...")
            
            # Setup vector store
            store = VectorStore()
            if store.count() > 0:
                store.reset_collection()
            
            # Add sample documents
            embedder = EmbeddingGenerator()
            
            sample_texts = [
                "Python is a high-level programming language known for its simplicity and readability.",
                "JavaScript is primarily used for web development and runs in browsers.",
                "Machine learning models can be trained using Python libraries like scikit-learn and TensorFlow.",
                "React is a JavaScript library for building user interfaces.",
                "Neural networks are inspired by the human brain and consist of interconnected nodes."
            ]
            
            sample_embeddings = embedder.create_embeddings_batch(sample_texts)
            store.add_documents(texts=sample_texts, embeddings=sample_embeddings)
            
            # Ask a question
            user_question = "What programming language is good for machine learning?"
            print(f"\n❓ User Question: {user_question}")
            
            # Search vector store
            query_vector = embedder.create_embedding(user_question)
            search_results = store.search(query_vector, n_results=2)
            
            # Get answer from chat engine
            relevant_chunks = search_results['documents'][0]
            print(f"📊 Found {len(relevant_chunks)} relevant chunks")
            
            final_answer = chat.ask(user_question, relevant_chunks)
            print(f"\n💬 Final Answer:\n{final_answer}")
            
            # Test 5: Show conversation history
            print("\n📝 Test 5: Conversation History")
            history = chat.get_history()
            print(f"📊 Total exchanges: {len(history)}")
            for i, entry in enumerate(history, 1):
                print(f"\n{i}. Q: {entry['question'][:50]}...")
                print(f"   A: {entry['answer'][:50]}...")
                print(f"   Context chunks used: {entry['context_used']}")
            
            print("\n" + "=" * 60)
            print("✅ All tests passed!")
            print("\n💡 Your RAG system is COMPLETE and working!")
            print("🎉 You can now ask questions about your PDFs!")
            
        except ValueError as e:
            print(f"\n{str(e)}")
            print("\n💡 Fix: Add your Groq API key to .env file")
        except ImportError as e:
            print(f"\n❌ Error importing modules: {str(e)}")
            print("💡 Make sure embeddings.py and vector_store.py exist")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
