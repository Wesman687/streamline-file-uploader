"""
FastAPI Integration Example
==========================

This example shows how to integrate the Stream-Line file server
with a FastAPI application.
"""

import os
import tempfile
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import the Stream-Line client (copy streamline_file_client.py to your project)
from streamline_file_client import StreamLineFileClient, StreamLineFileManager

app = FastAPI(title="Stream-Line File Server Integration", version="1.0.0")

# Configuration
STREAMLINE_SERVICE_TOKEN = os.getenv('STREAMLINE_SERVICE_TOKEN', 
                                   'ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340')

# Initialize clients
file_client = StreamLineFileClient(STREAMLINE_SERVICE_TOKEN)
file_manager = StreamLineFileManager(file_client)

# Pydantic models
class UploadResponse(BaseModel):
    success: bool
    public_url: str
    file_key: str
    original_name: str
    size: int
    mime: Optional[str] = None

class FileListResponse(BaseModel):
    files: List[dict]
    total_count: int
    total_size: int

class HealthResponse(BaseModel):
    status: str
    disk_free_gb: float
    writable: bool

# Mock authentication (replace with your auth system)
async def get_current_user(user_id: str = "demo-user") -> str:
    """Get current user ID (replace with your auth system)."""
    return user_id

@app.post("/api/upload/profile-picture", response_model=UploadResponse)
async def upload_profile_picture(
    picture: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """
    Upload a user's profile picture.
    """
    if not picture.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        content = await picture.read()
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        # Upload to Stream-Line file server
        profile_url = file_manager.upload_profile_picture(
            user_id=user_id,
            image_path=temp_path
        )
        
        # Here you would typically save profile_url to your database
        # await update_user_profile_picture(user_id, profile_url)
        
        return UploadResponse(
            success=True,
            public_url=profile_url,
            file_key="",  # You might want to store this separately
            original_name=picture.filename,
            size=len(content)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temp file
        os.unlink(temp_path)


@app.post("/api/upload/document", response_model=UploadResponse)
async def upload_document(
    document: UploadFile = File(...),
    document_type: str = Form("general"),
    user_id: str = Depends(get_current_user)
):
    """
    Upload a document for the user.
    """
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{document.filename}') as temp_file:
        content = await document.read()
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        # Upload to Stream-Line file server
        result = file_manager.upload_document(
            user_id=user_id,
            doc_path=temp_path,
            doc_type=document_type
        )
        
        # Here you would typically save document info to your database
        # await save_document_record(user_id, result)
        
        return UploadResponse(
            success=True,
            public_url=result['public_url'],
            file_key=result['file_key'],
            original_name=result['original_name'],
            size=result['size'],
            mime=result['mime']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temp file
        os.unlink(temp_path)


@app.post("/api/upload/media", response_model=UploadResponse)
async def upload_media(
    media: UploadFile = File(...),
    media_type: str = Form("general"),
    user_id: str = Depends(get_current_user)
):
    """
    Upload media files (photos, videos, audio).
    """
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{media.filename}') as temp_file:
        content = await media.read()
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        # Upload to Stream-Line file server
        result = file_manager.upload_media(
            user_id=user_id,
            media_path=temp_path,
            media_type=media_type
        )
        
        return UploadResponse(
            success=True,
            public_url=result['public_url'],
            file_key=result['file_key'],
            original_name=result['original_name'],
            size=result['size'],
            mime=result['mime']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temp file
        os.unlink(temp_path)


@app.get("/api/files", response_model=FileListResponse)
async def list_user_files(
    folder: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Get all files for the authenticated user."""
    try:
        files = file_client.list_user_files(user_id, folder=folder)
        return FileListResponse(**files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/files/{file_key}")
async def delete_file(
    file_key: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a file by its key."""
    try:
        success = file_client.delete_file(file_key)
        if success:
            # Here you would also delete from your database
            # await delete_file_record(file_key)
            return {"success": True, "message": "File deleted"}
        else:
            raise HTTPException(status_code=500, detail="File deletion failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/profile")
async def get_user_profile(user_id: str = Depends(get_current_user)):
    """Get user profile information."""
    try:
        profile_picture_url = file_manager.get_user_profile_picture(user_id)
    except:
        profile_picture_url = None
    
    return {
        "user_id": user_id,
        "profile_picture_url": profile_picture_url
    }


@app.get("/api/documents")
async def get_user_documents(
    doc_type: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Get user's documents."""
    try:
        documents = file_manager.get_user_documents(user_id, doc_type=doc_type)
        return {
            "documents": documents,
            "count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/media")
async def get_user_media(
    media_type: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Get user's media files."""
    try:
        media = file_manager.get_user_media(user_id, media_type=media_type)
        return {
            "media": media,
            "count": len(media)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check file server health."""
    try:
        health = file_client.get_health_status()
        return HealthResponse(**health)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Example database models (using SQLAlchemy)
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    profile_picture_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    documents = relationship("UserDocument", back_populates="user")

class UserDocument(Base):
    __tablename__ = "user_documents"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_type = Column(String(20), default="general")
    file_key = Column(String(255), nullable=False)
    public_url = Column(String(500), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="documents")

# Database operations
async def update_user_profile_picture(user_id: str, profile_url: str):
    # Update user's profile picture URL in database
    pass

async def save_document_record(user_id: str, result: dict):
    # Save document record to database
    pass

async def delete_file_record(file_key: str):
    # Delete file record from database
    pass
"""

# Example HTML page for testing
@app.get("/")
async def index():
    """Simple test page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FastAPI Stream-Line File Server Test</title>
    </head>
    <body>
        <h1>FastAPI Stream-Line File Server Integration Test</h1>
        
        <div>
            <h2>Upload Profile Picture</h2>
            <form id="profileForm" enctype="multipart/form-data">
                <input type="file" name="picture" accept="image/*" required>
                <button type="submit">Upload Profile Picture</button>
            </form>
        </div>
        
        <div>
            <h2>Upload Document</h2>
            <form id="documentForm" enctype="multipart/form-data">
                <input type="file" name="document" required>
                <select name="document_type">
                    <option value="general">General</option>
                    <option value="contract">Contract</option>
                    <option value="invoice">Invoice</option>
                    <option value="receipt">Receipt</option>
                </select>
                <button type="submit">Upload Document</button>
            </form>
        </div>
        
        <div>
            <h2>Upload Media</h2>
            <form id="mediaForm" enctype="multipart/form-data">
                <input type="file" name="media" accept="image/*,video/*,audio/*" required>
                <select name="media_type">
                    <option value="general">General</option>
                    <option value="photos">Photos</option>
                    <option value="videos">Videos</option>
                    <option value="audio">Audio</option>
                </select>
                <button type="submit">Upload Media</button>
            </form>
        </div>
        
        <div>
            <h2>File Operations</h2>
            <button onclick="listFiles()">List All Files</button>
            <button onclick="getProfile()">Get Profile</button>
            <button onclick="getDocuments()">Get Documents</button>
            <button onclick="getMedia()">Get Media</button>
            <button onclick="checkHealth()">Check Health</button>
        </div>
        
        <div>
            <h2>Results</h2>
            <pre id="output"></pre>
        </div>
        
        <script>
            // Handle form submissions
            document.getElementById('profileForm').onsubmit = async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const response = await fetch('/api/upload/profile-picture', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                updateOutput('Profile Upload Result:', result);
            };
            
            document.getElementById('documentForm').onsubmit = async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const response = await fetch('/api/upload/document', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                updateOutput('Document Upload Result:', result);
            };
            
            document.getElementById('mediaForm').onsubmit = async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const response = await fetch('/api/upload/media', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                updateOutput('Media Upload Result:', result);
            };
            
            // API calls
            async function listFiles() {
                const response = await fetch('/api/files');
                const result = await response.json();
                updateOutput('Files:', result);
            }
            
            async function getProfile() {
                const response = await fetch('/api/profile');
                const result = await response.json();
                updateOutput('Profile:', result);
            }
            
            async function getDocuments() {
                const response = await fetch('/api/documents');
                const result = await response.json();
                updateOutput('Documents:', result);
            }
            
            async function getMedia() {
                const response = await fetch('/api/media');
                const result = await response.json();
                updateOutput('Media:', result);
            }
            
            async function checkHealth() {
                const response = await fetch('/health');
                const result = await response.json();
                updateOutput('Health:', result);
            }
            
            function updateOutput(title, data) {
                const output = document.getElementById('output');
                output.textContent += `\\n${title}\\n${JSON.stringify(data, null, 2)}\\n\\n`;
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
