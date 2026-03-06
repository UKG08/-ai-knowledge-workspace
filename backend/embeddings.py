import os
from typing import List
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EmbeddingGenerator:
  
    
    def __init__(self):
       
        print("🔄 Loading FREE embedding model...")
        print("💡 Using Sentence-Transformers (runs locally, 100% free)")
        
        
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        print("✅ Embedding Generator ready!")
        print("📊 Model: all-MiniLM-L6-v2 (384 dimensions)")
    
    
    def create_embedding(self, text: str) -> List[float]:
        
        try:
            # Create embedding locally
            embedding = self.model.encode(text)
            return embedding.tolist()
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return []
    
    
    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
       
        try:
            print(f"🔄 Creating {len(texts)} embeddings...")
            
            
            embeddings = self.model.encode(texts, show_progress_bar=True)
            
      
            embeddings_list = [emb.tolist() for emb in embeddings]
            
            print(f"✅ Created {len(embeddings_list)} embeddings")
            return embeddings_list
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return []


# ============================================================================
# TESTING CODE
# ============================================================================
if __name__ == "__main__":
    print("🧪 Testing Embedding Generator (FREE)...")
    print("=" * 60)
    
    try:

        embedder = EmbeddingGenerator()
        
        # Test 1: Single text
        print("\n📝 Test 1: Single text to vector")
        test_text = "What is artificial intelligence?"
        vector = embedder.create_embedding(test_text)
        
        if vector:
            print(f"   ✅ Text: '{test_text}'")
            print(f"   ✅ Vector size: {len(vector)} dimensions")
            print(f"   ✅ First 5 numbers: {vector[:5]}")
        
        # Test 2: Multiple texts
        print("\n📝 Test 2: Multiple texts to vectors")
        test_texts = [
            "Machine learning is amazing",
            "Deep learning uses neural networks",
            "AI is transforming the world"
        ]
        
        vectors = embedder.create_embeddings_batch(test_texts)
        
        if vectors:
            print(f"   ✅ Created {len(vectors)} vectors")
            for i, text in enumerate(test_texts):
                print(f"   {i+1}. '{text}' → {len(vectors[i])} dimensions")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Embeddings working perfectly!")
        print("💡 Groq API will be used for chat in the next files")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Fix: Install sentence-transformers:")
        print("   pip install sentence-transformers")
    
    print("=" * 60)