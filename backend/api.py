

import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pdf_processor import PDFProcessor
from embeddings import EmbeddingGenerator
from vector_store import VectorStore
from chat import ChatEngine




class QuestionRequest(BaseModel):
    question: str
    n_results: Optional[int] = 3


class QuestionResponse(BaseModel):
    answer: str
    sources: List[dict]


class StatusResponse(BaseModel):
    total_documents: int
    indexed_pdfs: dict
    status: str



app = FastAPI(
    title="AI Knowledge Workspace API",
    description="RAG system for PDF document Q&A",
    version="1.0.0"
)

# Enable CORS (allow React to call this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# INITIALIZE RAG SYSTEM
# ============================================================================

# Global instances (initialized on startup)
pdf_processor = None
embedder = None
vector_store = None
chat_engine = None
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Serve React build folder
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

# Serve main React index.html
@app.get("/")
def serve_react():
    return FileResponse("frontend/dist/index.html")
@app.on_event("startup")
async def startup_event():

    global pdf_processor, embedder, vector_store, chat_engine
    
    print("🚀 Initializing AI Knowledge Workspace...")
    
    pdf_processor = PDFProcessor()
    embedder = EmbeddingGenerator()
    vector_store = VectorStore()
    chat_engine = ChatEngine()
    
    print("✅ Server ready!")


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """
    Health check endpoint
    """
    return {
        "message": "AI Knowledge Workspace API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get system status and database info
    """
    try:
        total_docs = vector_store.count()
        
        # Get indexed PDFs
        indexed_pdfs = {}
        if total_docs > 0:
            all_docs = vector_store.get_all_documents()
            for meta in all_docs['metadatas']:
                if meta and 'source' in meta:
                    source = meta['source']
                    indexed_pdfs[source] = indexed_pdfs.get(source, 0) + 1
        
        return StatusResponse(
            total_documents=total_docs,
            indexed_pdfs=indexed_pdfs,
            status="ready" if total_docs > 0 else "no_documents"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF file
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save uploaded file
        upload_path = os.path.join("data/uploads", file.filename)
        
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process PDF
        print(f"📄 Processing: {file.filename}")
        
        # Extract text
        text = pdf_processor.extract_text_from_pdf(upload_path)
        
        if not text:
            raise HTTPException(status_code=400, detail="Failed to extract text from PDF")
        
        # Chunk text
        chunks = chunk_text(text, chunk_size=1000, overlap=200)
        
        # Create embeddings
        embeddings = embedder.create_embeddings_batch(chunks)
        
        # Store in vector database
        metadata = [
            {
                "source": file.filename,
                "chunk_id": i,
                "total_chunks": len(chunks)
            }
            for i in range(len(chunks))
        ]
        
        vector_store.add_documents(
            texts=chunks,
            embeddings=embeddings,
            metadatas=metadata
        )
        
        return {
            "message": f"Successfully processed {file.filename}",
            "filename": file.filename,
            "chunks_created": len(chunks),
            "total_documents": vector_store.count()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):

    try:
     
        if vector_store.count() == 0:
            raise HTTPException(
                status_code=400,
                detail="No documents in database. Please upload PDFs first."
            )

        query_embedding = embedder.create_embedding(request.question)
        
  
        results = vector_store.search(query_embedding, n_results=request.n_results)
        
        if not results['documents'][0]:
            raise HTTPException(
                status_code=404,
                detail="No relevant information found"
            )

        context_chunks = results['documents'][0]
        answer = chat_engine.ask(request.question, context_chunks)
        
        sources = []
        if results.get('metadatas') and results['metadatas'][0]:
            for i, metadata in enumerate(results['metadatas'][0]):
                if metadata:
                    distance = results['distances'][0][i] if results.get('distances') else None
                    relevance = max(0, 1 - abs(distance)) if distance is not None else 0
                    
                    sources.append({
                        "source": metadata.get('source', 'Unknown'),
                        "chunk_id": metadata.get('chunk_id', 0),
                        "relevance": round(relevance * 100, 1)
                    })
        
        return QuestionResponse(
            answer=answer,
            sources=sources
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/clear")
async def clear_database():

    try:
        vector_store.reset_collection()
        return {
            "message": "Database cleared successfully",
            "total_documents": vector_store.count()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pdfs")
async def list_pdfs():
 
    try:
        upload_folder = "data/uploads"
        if not os.path.exists(upload_folder):
            return {"pdfs": []}
        
        pdf_files = [f for f in os.listdir(upload_folder) if f.endswith('.pdf')]
        
        return {
            "pdfs": pdf_files,
            "count": len(pdf_files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        if chunk.strip():
            chunks.append(chunk)
        
        start += (chunk_size - overlap)
    
    return chunks


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)