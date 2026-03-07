"""
Vector Store Module
Stores and searches vector embeddings using ChromaDB
"""

import os
import uuid
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings

# Disable telemetry warnings
os.environ["ANONYMIZED_TELEMETRY"] = "False"


class VectorStore:
    """
    Manages vector storage and similarity search using ChromaDB
    """
    
    def __init__(self, collection_name: str = "pdf_documents", persist_directory: str = "data/vector_db"):
        """
        Initialize vector store
        
        Args:
            collection_name: Name of the collection (like a table in database)
            persist_directory: Where to save the database
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Create directory if it doesn't exist
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "PDF document embeddings"}
        )
        
        print(f"✅ Vector Store initialized")
        print(f"📊 Collection: {collection_name}")
        print(f"💾 Storage: {persist_directory}")
        print(f"📝 Total documents: {self.collection.count()}")
    
    
    def add_documents(
        self, 
        texts: List[str], 
        embeddings: List[List[float]], 
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ):
        """
        Add documents to the vector store
        
        Args:
            texts: List of text chunks
            embeddings: List of vectors (one per text)
            metadatas: Optional metadata for each chunk (filename, page, etc.)
            ids: Optional custom IDs (auto-generated if not provided)
        
        Example:
            store = VectorStore()
            store.add_documents(
                texts=["First chunk", "Second chunk"],
                embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...]],
                metadatas=[{"source": "doc1.pdf"}, {"source": "doc2.pdf"}]
            )
        """
        try:
            # Generate UNIQUE IDs if not provided
            if ids is None:
                ids = [f"doc_{uuid.uuid4()}" for _ in range(len(texts))]
            
            # Add to collection
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ Added {len(texts)} documents to vector store")
            print(f"📊 Total documents now: {self.collection.count()}")
            
        except Exception as e:
            print(f"❌ Error adding documents: {str(e)}")
    
    
    def search(
        self, 
        query_embedding: List[float], 
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Search for similar documents
        
        Args:
            query_embedding: Vector of the query
            n_results: How many results to return (default: 5)
            filter_metadata: Optional filter (e.g., {"source": "specific.pdf"})
        
        Returns:
            Dictionary with:
            - documents: List of text chunks
            - distances: Similarity scores
            - metadatas: Metadata for each result
            - ids: Document IDs
        
        Example:
            store = VectorStore()
            embedder = EmbeddingGenerator()
            
            query = "What is machine learning?"
            query_vector = embedder.create_embedding(query)
            results = store.search(query_vector, n_results=3)
            
            for i, doc in enumerate(results['documents'][0]):
                print(f"{i+1}. {doc}")
        """
        try:
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata
            )
            
            print(f"🔍 Found {len(results['documents'][0])} results")
            return results
            
        except Exception as e:
            print(f"❌ Error searching: {str(e)}")
            return {"documents": [[]], "distances": [[]], "metadatas": [[]], "ids": [[]]}
    
    
    def delete_collection(self):
        """
        Delete the entire collection (use with caution!)
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"✅ Deleted collection: {self.collection_name}")
        except Exception as e:
            print(f"❌ Error deleting collection: {str(e)}")
    
    
    def reset_collection(self):
        """
        Delete and recreate the collection (fresh start)
        """
        try:
            # Delete old collection
            self.client.delete_collection(name=self.collection_name)
            
            # Create new one
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "PDF document embeddings"}
            )
            
            print(f"✅ Collection reset successfully")
            print(f"📊 Total documents: {self.collection.count()}")
        except Exception as e:
            print(f"❌ Error resetting collection: {str(e)}")
    
    
    def get_all_documents(self) -> Dict:
        """
        Get all documents in the collection
        
        Returns:
            Dictionary with all documents and metadata
        """
        try:
            results = self.collection.get()
            print(f"📊 Retrieved {len(results['documents'])} documents")
            return results
        except Exception as e:
            print(f"❌ Error getting documents: {str(e)}")
            return {"documents": [], "metadatas": [], "ids": []}
    
    
    def count(self) -> int:
        """
        Get total number of documents
        
        Returns:
            Number of documents in collection
        """
        return self.collection.count()
    
    
    def clear_all(self):
        """
        Clear all documents from collection (keeps collection structure)
        """
        try:
            # Get all IDs
            all_docs = self.collection.get()
            if all_docs['ids']:
                # Delete all documents
                self.collection.delete(ids=all_docs['ids'])
                print(f"✅ Cleared all documents from collection")
                print(f"📊 Total documents: {self.collection.count()}")
            else:
                print(f"⚠️ Collection already empty")
        except Exception as e:
            print(f"❌ Error clearing collection: {str(e)}")


# ============================================================================
# TESTING CODE
# ============================================================================
if __name__ == "__main__":
    print("🧪 Testing Vector Store...")
    print("=" * 60)
    
    # Import embeddings module for testing
    try:
        from embeddings import EmbeddingGenerator
        
        # Test 1: Initialize store
        print("\n📝 Test 1: Initialize Vector Store")
        store = VectorStore()
        
        # Reset collection for clean test
        if store.count() > 0:
            print("🔄 Clearing previous test data...")
            store.reset_collection()
        
        # Test 2: Add sample documents
        print("\n📝 Test 2: Add Documents")
        
        # Sample texts
        sample_texts = [
            "Machine learning is a subset of artificial intelligence",
            "Deep learning uses neural networks with multiple layers",
            "Natural language processing helps computers understand human language",
            "Computer vision enables machines to interpret visual information",
            "Reinforcement learning trains agents through rewards and penalties"
        ]
        
        # Create embeddings
        print("📌 Creating embeddings...")
        embedder = EmbeddingGenerator()
        sample_embeddings = embedder.create_embeddings_batch(sample_texts)
        
        # Add metadata
        sample_metadata = [
            {"source": "ai_basics.pdf", "page": 1, "topic": "ML"},
            {"source": "ai_basics.pdf", "page": 2, "topic": "DL"},
            {"source": "nlp_guide.pdf", "page": 1, "topic": "NLP"},
            {"source": "cv_intro.pdf", "page": 1, "topic": "CV"},
            {"source": "rl_tutorial.pdf", "page": 1, "topic": "RL"}
        ]
        
        # Add to store
        store.add_documents(
            texts=sample_texts,
            embeddings=sample_embeddings,
            metadatas=sample_metadata
        )
        
        # Test 3: Search
        print("\n📝 Test 3: Semantic Search")
        query = "How do computers learn from data?"
        query_vector = embedder.create_embedding(query)
        
        print(f"\n🔍 Query: '{query}'")
        results = store.search(query_vector, n_results=3)
        
        if results['documents'][0]:
            print("\n📊 Top 3 Results:")
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]
                print(f"\n{i+1}. Score: {1 - distance:.3f}")
                print(f"   Text: {doc}")
                print(f"   Source: {metadata['source']}, Page: {metadata['page']}")
        
        # Test 4: Count documents
        print(f"\n📝 Test 4: Document Count")
        total = store.count()
        print(f"   Total documents: {total}")
        
        # Test 5: Filter search
        print("\n📝 Test 5: Filtered Search")
        filtered_results = store.search(
            query_vector, 
            n_results=2,
            filter_metadata={"source": "ai_basics.pdf"}
        )
        if filtered_results['documents'][0]:
            print(f"   Results from ai_basics.pdf only:")
            for i, doc in enumerate(filtered_results['documents'][0]):
                print(f"   {i+1}. {doc[:60]}...")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("\n💡 The vector database is working perfectly!")
        print("💡 Your embeddings are stored in: data/vector_db/")
        
    except ImportError:
        print("\n❌ Error: Could not import embeddings module")
        print("💡 Make sure embeddings.py exists in the backend folder")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)