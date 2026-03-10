"""
Main Application
Complete RAG pipeline for PDF question answering
"""

import os
from pdf_processor import PDFProcessor
from embeddings import EmbeddingGenerator
from vector_store import VectorStore
from chat import ChatEngine


class RAGSystem:
    """
    Complete RAG system that processes PDFs and answers questions
    """
    
    def __init__(self):
        """
        Initialize all components
        """
        print("🚀 Initializing AI Knowledge Workspace...")
        print("=" * 60)
        
        # Initialize components
        self.pdf_processor = PDFProcessor()
        self.embedder = EmbeddingGenerator()
        self.vector_store = VectorStore()
        self.chat_engine = ChatEngine()
        
        print("=" * 60)
        print("✅ System ready!\n")
    
    
    def process_pdf(self, pdf_path: str, chunk_size: int = 1000, overlap: int = 200):
        """
        Process a PDF file and add to vector database
        
        Args:
            pdf_path: Path to PDF file
            chunk_size: Size of text chunks (default: 1000 chars)
            overlap: Overlap between chunks (default: 200 chars)
        """
        print(f"\n📄 Processing: {os.path.basename(pdf_path)}")
        print("-" * 60)
        
        # Step 1: Extract text
        print("1️⃣ Extracting text from PDF...")
        text = self.pdf_processor.extract_text_from_pdf(pdf_path)
        
        if not text:
            print("❌ Failed to extract text from PDF")
            return False
        
        print(f"   ✅ Extracted {len(text)} characters")
        
        # Step 2: Chunk text
        print("2️⃣ Splitting text into chunks...")
        chunks = self._chunk_text(text, chunk_size, overlap)
        print(f"   ✅ Created {len(chunks)} chunks")
        
        # Step 3: Create embeddings
        print("3️⃣ Creating embeddings...")
        embeddings = self.embedder.create_embeddings_batch(chunks)
        
        if not embeddings:
            print("❌ Failed to create embeddings")
            return False
        
        # Step 4: Store in vector database
        print("4️⃣ Storing in vector database...")
        metadata = [
            {
                "source": os.path.basename(pdf_path),
                "chunk_id": i,
                "total_chunks": len(chunks)
            }
            for i in range(len(chunks))
        ]
        
        self.vector_store.add_documents(
            texts=chunks,
            embeddings=embeddings,
            metadatas=metadata
        )
        
        print("-" * 60)
        print(f"✅ Successfully processed: {os.path.basename(pdf_path)}")
        print(f"📊 Total documents in database: {self.vector_store.count()}\n")
        
        return True
    
    
    def process_all_pdfs(self, folder: str = "data/uploads"):
        """
        Process all PDFs in a folder
        
        Args:
            folder: Path to folder containing PDFs
        """
        print(f"\n📂 Processing all PDFs in: {folder}")
        print("=" * 60)
        
        # Get all PDF files
        if not os.path.exists(folder):
            print(f"❌ Folder not found: {folder}")
            return
        
        pdf_files = [f for f in os.listdir(folder) if f.endswith('.pdf')]
        
        if not pdf_files:
            print(f"⚠️  No PDF files found in {folder}")
            print(f"💡 Please add PDF files to the {folder} folder\n")
            return
        
        print(f"Found {len(pdf_files)} PDF file(s)\n")
        
        # Process each PDF
        success_count = 0
        for pdf_file in pdf_files:
            pdf_path = os.path.join(folder, pdf_file)
            if self.process_pdf(pdf_path):
                success_count += 1
        
        print("=" * 60)
        print(f"✅ Processed {success_count}/{len(pdf_files)} PDFs successfully")
        print("=" * 60)
    
    
    def ask_question(self, question: str, n_results: int = 3, show_sources: bool = True):
        """
        Ask a question and get an answer
        
        Args:
            question: User's question
            n_results: Number of context chunks to retrieve
            show_sources: Whether to show source information
            
        Returns:
            Answer string
        """
        print(f"\n❓ Question: {question}")
        print("-" * 60)
        
        # Check if database has documents
        if self.vector_store.count() == 0:
            print("❌ No documents in the knowledge base!")
            print("💡 Process PDFs first using option 1 or 2\n")
            return "No documents in knowledge base."
        
        # Step 1: Create query embedding
        print("🔍 Searching knowledge base...")
        query_embedding = self.embedder.create_embedding(question)
        
        # Step 2: Search vector database
        results = self.vector_store.search(query_embedding, n_results=n_results)
        
        if not results['documents'][0]:
            print("❌ No relevant information found in the knowledge base.")
            print("💡 Try rephrasing your question or add more PDFs\n")
            return "No relevant information found."
        
        # Step 3: Get answer from AI
        print(f"💭 Generating answer using {len(results['documents'][0])} context chunks...")
        context_chunks = results['documents'][0]
        answer = self.chat_engine.ask(question, context_chunks)
        
        print("-" * 60)
        print(f"💬 Answer:\n{answer}\n")
        
        # Show sources if requested
        if show_sources:
            try:
                if results.get('metadatas') and results['metadatas'][0]:
                    print("📚 Sources:")
                    for i, metadata in enumerate(results['metadatas'][0]):
                        if metadata and isinstance(metadata, dict):
                            source = metadata.get('source', 'Unknown')
                            chunk_id = metadata.get('chunk_id', '?')
                            distance = results['distances'][0][i] if results.get('distances') else None
                            
                            # Show relevance score
                            if distance is not None:
                                relevance = max(0, 1 - abs(distance))
                                print(f"   [{i+1}] {source} (chunk {chunk_id}) - Relevance: {relevance:.1%}")
                            else:
                                print(f"   [{i+1}] {source} (chunk {chunk_id})")
                        else:
                            print(f"   [{i+1}] Source information unavailable")
                    print()
            except Exception as e:
                print(f"⚠️  Could not display source information: {str(e)}\n")
        
        return answer
    
    
    def interactive_mode(self):
        """
        Start interactive Q&A session
        """
        print("\n" + "=" * 60)
        print("🤖 INTERACTIVE MODE")
        print("=" * 60)
        print("Ask questions about your PDFs!")
        print("\nCommands:")
        print("  • Type your question to get an answer")
        print("  • 'quit' or 'exit' - Exit interactive mode")
        print("  • 'clear' - Clear conversation history")
        print("  • 'status' - Show database statistics")
        print("  • 'help' - Show this help message")
        print("=" * 60 + "\n")
        
        while True:
            try:
                # Get user input
                question = input("❓ Your question: ").strip()
                
                if not question:
                    continue
                
                # Check for commands
                if question.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if question.lower() == 'clear':
                    self.chat_engine.clear_history()
                    continue
                
                if question.lower() == 'status':
                    total_docs = self.vector_store.count()
                    history_count = len(self.chat_engine.get_history())
                    print(f"\n📊 Status:")
                    print(f"   Documents in database: {total_docs}")
                    print(f"   Questions asked: {history_count}")
                    
                    if total_docs > 0:
                        # Show sample of what's in database
                        all_docs = self.vector_store.get_all_documents()
                        sources = set()
                        for meta in all_docs['metadatas']:
                            if meta and 'source' in meta:
                                sources.add(meta['source'])
                        print(f"   PDF files indexed: {', '.join(sources)}")
                    print()
                    continue
                
                if question.lower() == 'help':
                    print("\n📖 Available Commands:")
                    print("   • Type any question to get an answer")
                    print("   • 'quit' or 'exit' - Exit")
                    print("   • 'clear' - Clear history")
                    print("   • 'status' - Database info")
                    print("   • 'help' - This message\n")
                    continue
                
                # Ask question
                self.ask_question(question)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
    
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Don't add empty chunks
            if chunk.strip():
                chunks.append(chunk)
            
            start += (chunk_size - overlap)
        
        return chunks
    
    
    def show_database_info(self):
        """
        Display information about the vector database
        """
        print("\n" + "=" * 60)
        print("📊 DATABASE INFORMATION")
        print("=" * 60)
        
        total_docs = self.vector_store.count()
        print(f"Total documents: {total_docs}")
        
        if total_docs > 0:
            all_docs = self.vector_store.get_all_documents()
            
            # Get unique sources
            sources = {}
            for meta in all_docs['metadatas']:
                if meta and 'source' in meta:
                    source = meta['source']
                    sources[source] = sources.get(source, 0) + 1
            
            print(f"\nIndexed PDFs:")
            for source, count in sources.items():
                print(f"  • {source}: {count} chunks")
            
            # Show sample content
            print(f"\nSample content (first 3 chunks):")
            for i, (doc, meta) in enumerate(zip(all_docs['documents'][:3], all_docs['metadatas'][:3])):
                source = meta.get('source', 'Unknown') if meta else 'Unknown'
                chunk_id = meta.get('chunk_id', '?') if meta else '?'
                preview = doc[:100] + "..." if len(doc) > 100 else doc
                print(f"\n  [{i+1}] {source} (chunk {chunk_id})")
                print(f"      {preview}")
        else:
            print("\n⚠️  Database is empty")
            print("💡 Use option 1 or 2 to process PDFs")
        
        print("\n" + "=" * 60 + "\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    """
    Main function - runs the complete RAG system
    """
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "🔥 AI KNOWLEDGE WORKSPACE 🔥" + " " * 19 + "║")
    print("║" + " " * 12 + "RAG System for PDF Documents" + " " * 18 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Initialize system
    rag = RAGSystem()
    
    # Check if there are PDFs to process
    upload_folder = "data/uploads"
    pdf_files = []
    
    if os.path.exists(upload_folder):
        pdf_files = [f for f in os.listdir(upload_folder) if f.endswith('.pdf')]
    
    # Show initial status
    current_docs = rag.vector_store.count()
    if current_docs > 0:
        print(f"📊 Current database: {current_docs} documents indexed\n")
    
    # Menu
    print("📋 What would you like to do?\n")
    print("1. Process all PDFs in data/uploads/")
    print("2. Process a specific PDF")
    print("3. Ask questions (interactive mode)")
    print("4. Ask a single question")
    print("5. Show database information")
    print("6. Clear database")
    print("7. Exit")
    
    while True:
        try:
            choice = input("\n👉 Enter your choice (1-7): ").strip()
            
            if choice == "1":
                rag.process_all_pdfs()
                
            elif choice == "2":
                pdf_path = input("📄 Enter PDF path: ").strip()
                if os.path.exists(pdf_path):
                    rag.process_pdf(pdf_path)
                else:
                    print(f"❌ File not found: {pdf_path}")
            
            elif choice == "3":
                if rag.vector_store.count() == 0:
                    print("\n⚠️  No documents in database. Process PDFs first (option 1 or 2)")
                else:
                    rag.interactive_mode()
            
            elif choice == "4":
                if rag.vector_store.count() == 0:
                    print("\n⚠️  No documents in database. Process PDFs first (option 1 or 2)")
                else:
                    question = input("\n❓ Your question: ").strip()
                    if question:
                        rag.ask_question(question)
            
            elif choice == "5":
                rag.show_database_info()
            
            elif choice == "6":
                confirm = input("⚠️  Clear entire database? (yes/no): ").strip().lower()
                if confirm == "yes":
                    rag.vector_store.reset_collection()
                    print("✅ Database cleared!")
                else:
                    print("❌ Cancelled")
            
            elif choice == "7":
                print("\n👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1-7")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()5