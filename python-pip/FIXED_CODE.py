from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from api.auth import get_current_user, get_current_admin
from database.models import FileUpload, Job, User
from config import config
import requests
import base64
import logging
import os
from dotenv import load_dotenv

# Import the new SDK
try:
    from streamline_file_uploader import StreamlineFileUploader
    SDK_AVAILABLE = True
    print("✅ StreamlineFileUploader SDK loaded successfully")
except ImportError as e:
    print(f"❌ streamline-file-uploader SDK not available: {e}, falling back to legacy implementation")
    SDK_AVAILABLE = False

load_dotenv()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/file-upload")

# File server configuration (using config module for consistency)
FILE_SERVER_BASE_URL = config.UPLOAD_BASE_URL
SERVICE_TOKEN = config.AUTH_SERVICE_TOKEN

class FileServerService:
    """Service for interacting with Stream-Line file server"""
    
    @staticmethod
    async def upload_file_to_stream_line(user_email: str, file_data: bytes, filename: str, mime_type: str, folder: str = None):
        """Upload a file to Stream-Line file server using SDK or fallback to legacy API"""
        try:
            if SDK_AVAILABLE:
                # Use the new SDK - FIXED: using user_email instead of user_id
                logger.info(f"🚀 Using StreamlineFileUploader SDK for {filename}")
                async with StreamlineFileUploader(
                    base_url=config.UPLOAD_BASE_URL,
                    service_token=config.AUTH_SERVICE_TOKEN,
                    default_user_email=user_email  # FIXED: was default_user_id
                ) as uploader:
                    result = await uploader.upload_file(
                        file_content=file_data,
                        filename=filename,
                        folder=folder or "uploads",
                        user_email=user_email  # FIXED: was user_id
                    )
                    
                    # FIXED: The result object structure is different
                    logger.info(f"✅ SDK upload successful: {result.file_key}")
                    return {
                        "success": True,
                        "file_key": result.file_key,
                        "public_url": result.public_url,
                        "file_id": result.file_key  # Use file_key as file_id
                    }
            else:
                # Fallback to legacy implementation
                logger.info(f"🔄 Using legacy upload for {filename}")
                return await FileServerService._legacy_upload(user_email, file_data, filename, mime_type, folder)
                
        except Exception as e:
            logger.error(f"Upload to Stream-Line failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def _legacy_upload(user_email: str, file_data: bytes, filename: str, mime_type: str, folder: str = None):
        """Legacy upload implementation for fallback"""
        try:
            # Step 1: Initialize upload
            init_data = {
                "mode": "single",
                "files": [{
                    "name": filename,
                    "size": len(file_data),
                    "mime": mime_type
                }],
                "meta": {
                    "user_email": user_email,
                    "user_id": user_email  # File server expects user_id for authentication
                }
            }
            
            if folder:
                init_data["folder"] = folder
            
            response = requests.post(
                f"{FILE_SERVER_BASE_URL}/v1/files/init",
                headers={
                    "X-Service-Token": SERVICE_TOKEN,
                    "Content-Type": "application/json"
                },
                json=init_data
            )
            
            if response.status_code != 200:
                logger.error(f"File server init failed: {response.status_code} - {response.text}")
                raise Exception(f"File server init failed: {response.status_code}")
            
            upload_session = response.json()
            upload_id = upload_session["uploadId"]
            
            # Step 2: Upload the file data
            file_b64 = base64.b64encode(file_data).decode('utf-8')
            
            complete_data = {
                "uploadId": upload_id,
                "parts": [{"data": file_b64}],
                "meta": {
                    "user_email": user_email,
                    "user_id": user_email  # File server expects user_id for authentication
                },
                "folder": folder
            }
            
            response = requests.post(
                f"{FILE_SERVER_BASE_URL}/v1/files/complete",
                headers={
                    "X-Service-Token": SERVICE_TOKEN,
                    "Content-Type": "application/json"
                },
                json=complete_data
            )
            
            if response.status_code != 200:
                logger.error(f"File server complete failed: {response.status_code} - {response.text}")
                raise Exception(f"File server complete failed: {response.status_code}")
            
            result = response.json()
            
            # Generate public URL based on folder structure
            if folder:
                public_url = f"{FILE_SERVER_BASE_URL}/storage/{user_email}/{folder}/{result['fileKey'].split('_', 1)[1]}"
            else:
                public_url = f"{FILE_SERVER_BASE_URL}/storage/{user_email}/{result['fileKey'].split('_', 1)[1]}"
            
            return {
                "file_key": result["fileKey"],
                "public_url": public_url,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Legacy upload failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_user_files(user_email: str, folder: str = None):
        """Get all files for a user from the file server"""
        try:
            params = {"user_email": user_email}  # FIXED: was user_id
            if folder:
                params["folder"] = folder
            
            response = requests.get(
                f"{FILE_SERVER_BASE_URL}/v1/files/all",
                headers={
                    "X-Service-Token": SERVICE_TOKEN
                },
                params=params
            )
            
            if response.status_code != 200:
                logger.error(f"File server list failed: {response.status_code} - {response.text}")
                return {"success": False, "error": f"File server list failed: {response.status_code}"}
            
            return {"success": True, "data": response.json()}
            
        except Exception as e:
            logger.error(f"Error getting user files: {str(e)}")
            return {"success": False, "error": str(e)}

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    upload_type: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    job_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Upload a file to the Stream-Line file server"""
    try:
        logger.info(f"📁 File upload request: {file.filename}, type: {upload_type}, size: {file.size}, user: {current_user.get('email')}")
        # Validate file size (max 50MB)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size too large. Maximum size is 50MB.")
        
        # Read file data
        file_data = await file.read()
        
        # Get customer email for file server
        customer_email = current_user.get('email')
        
        # Determine folder structure based on upload type and job_id
        if job_id:
            # Job-specific files go to /documents/{job_id}
            folder = f"documents/{job_id}"
        elif upload_type in ["logo", "project", "reference"]:
            # Job-related files without specific job_id go to main documents
            folder = "documents/main"
        else:
            # Other files use the existing mapping
            folder_mapping = {
                "profile_picture": "main/pictures",
                "project_file": "projects",
                "document": "documents/main",
                "image": "images",
                "video": "videos",
                "audio": "audio"
            }
            folder = folder_mapping.get(upload_type, "uploads")
        
        # Upload to file server - use customer email as user_email for file server
        file_server_result = await FileServerService.upload_file_to_stream_line(
            user_email=customer_email,  # FIXED: File server expects email address
            file_data=file_data,
            filename=file.filename,
            mime_type=file.content_type or "application/octet-stream",
            folder=folder
        )
        
        if not file_server_result["success"]:
            raise HTTPException(status_code=500, detail=f"File server upload failed: {file_server_result.get('error', 'Unknown error')}")
        
        # Store file metadata in our database
        file_upload = FileUpload(
            user_id=current_user.get('user_id'),
            customer_id=current_user.get('user_id') if current_user.get('user_type') == 'customer' else None,
            job_id=job_id,
            file_key=file_server_result["file_key"],
            filename=file_server_result["file_key"].split('_', 1)[1] if '_' in file_server_result["file_key"] else file_server_result["file_key"],
            original_filename=file.filename,
            file_size=len(file_data),
            mime_type=file.content_type or "application/octet-stream",
            upload_type=upload_type,
            description=description,
            tags=tags,
            file_server_url=file_server_result["public_url"],
            folder=folder
        )
        
        db.add(file_upload)
        db.commit()
        db.refresh(file_upload)
        
        return {
            "message": "File uploaded successfully",
            "file_id": file_upload.id,
            "filename": file_upload.filename,
            "file_url": file_upload.file_server_url,
            "upload_type": file_upload.upload_type,
            "public_url": file_server_result["public_url"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/files")
async def get_user_files(
    upload_type: Optional[str] = None,
    folder: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get files for the current user from both our database and file server"""
    try:
        user_id = str(current_user.get('user_id'))
        
        # Get files from our database first
        query = db.query(FileUpload).filter(
            FileUpload.is_active == True,
            FileUpload.is_deleted == False
        )
        
        if current_user.get('user_type') == 'admin':
            query = query.filter(FileUpload.user_id == current_user.get('user_id'))
        else:
            query = query.filter(FileUpload.customer_id == current_user.get('user_id'))
        
        if upload_type:
            query = query.filter(FileUpload.upload_type == upload_type)
        
        if folder:
            query = query.filter(FileUpload.folder == folder)
        
        db_files = query.order_by(FileUpload.uploaded_at.desc()).all()
        
        # Also get files from file server for completeness - use email as user_email
        file_server_result = await FileServerService.get_user_files(current_user.get('email'), folder)
        
        return {
            "files": [
                {
                    "id": f.id,
                    "filename": f.filename,
                    "original_filename": f.original_filename,
                    "file_size": f.file_size,
                    "mime_type": f.mime_type,
                    "upload_type": f.upload_type,
                    "description": f.description,
                    "tags": f.tags,
                    "uploaded_at": f.uploaded_at.isoformat(),
                    "file_url": f.file_server_url,
                    "folder": f.folder
                }
                for f in db_files
            ],
            "file_server_status": "success" if file_server_result["success"] else "error",
            "file_server_error": file_server_result.get("error") if not file_server_result["success"] else None
        }
        
    except Exception as e:
        logger.error(f"Error getting user files: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/files/{file_id}")
async def get_file_info(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get information about a specific file"""
    try:
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.is_active == True,
            FileUpload.is_deleted == False
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if user has access to this file
        if (file_upload.user_id != current_user.get('user_id') and 
            file_upload.customer_id != current_user.get('user_id') and
            current_user.get('user_type') != 'admin'):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "id": file_upload.id,
            "filename": file_upload.filename,
            "original_filename": file_upload.original_filename,
            "file_size": file_upload.file_size,
            "mime_type": file_upload.mime_type,
            "upload_type": file_upload.upload_type,
            "description": file_upload.description,
            "tags": file_upload.tags,
            "uploaded_at": file_upload.uploaded_at.isoformat(),
            "file_url": file_upload.file_server_url,
            "folder": file_upload.folder,
            "public_url": file_upload.file_server_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a file (mark as deleted in database)"""
    try:
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.is_active == True,
            FileUpload.is_deleted == False
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if user has access to this file
        if (file_upload.user_id != current_user.get('user_id') and 
            file_upload.customer_id != current_user.get('user_id') and
            current_user.get('user_type') != 'admin'):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Mark as deleted (soft delete)
        file_upload.is_deleted = True
        db.commit()
        
        return {"message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/customer/upload")
async def customer_upload_file(
    file: UploadFile = File(...),
    upload_type: str = Form(...),
    description: Optional[str] = Form(None),
    job_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Customer-specific file upload with proper folder structure"""
    try:
        # Validate file size (max 50MB)
        if file.size and file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size too large. Maximum size is 50MB.")
        
        # Read file data
        file_data = await file.read()
        
        # Get customer email for file server
        customer_email = current_user.get('email')
        
        # Determine folder structure for customer uploads
        if job_id:
            # Job-specific files go to /documents/{job_id}
            folder = f"documents/{job_id}"
        elif upload_type in ["logo", "project", "reference"]:
            # Job-related files without specific job_id go to main documents
            folder = "documents/main"
        else:
            # Default to main documents folder
            folder = "documents/main"
        
        # Upload to file server
        file_server_result = await FileServerService.upload_file_to_stream_line(
            user_email=customer_email,
            file_data=file_data,
            filename=file.filename,
            mime_type=file.content_type or "application/octet-stream",
            folder=folder
        )
        
        if not file_server_result["success"]:
            raise HTTPException(status_code=500, detail=f"File server upload failed: {file_server_result.get('error', 'Unknown error')}")
        
        # Store file metadata in our database
        file_upload = FileUpload(
            user_id=current_user.get('user_id'),
            customer_id=current_user.get('user_id'),
            job_id=job_id,
            file_key=file_server_result["file_key"],
            filename=file_server_result["file_key"].split('_', 1)[1] if '_' in file_server_result["file_key"] else file_server_result["file_key"],
            original_filename=file.filename,
            file_size=len(file_data),
            mime_type=file.content_type or "application/octet-stream",
            upload_type=upload_type,
            description=description,
            tags=f"customer,{upload_type}",
            file_server_url=file_server_result["public_url"],
            folder=folder
        )
        
        db.add(file_upload)
        db.commit()
        db.refresh(file_upload)
        
        return {
            "message": "File uploaded successfully",
            "file_id": file_upload.id,
            "filename": file_upload.filename,
            "file_url": file_upload.file_server_url,
            "upload_type": file_upload.upload_type,
            "public_url": file_server_result["public_url"],
            "folder": folder
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading customer file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/customer/job/{job_id}/files")
async def get_customer_job_files(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all files for a specific job for the current customer"""
    try:
        # Get files from our database for this specific job
        query = db.query(FileUpload).filter(
            FileUpload.is_active == True,
            FileUpload.is_deleted == False,
            FileUpload.job_id == job_id,
            FileUpload.customer_id == current_user.get('user_id')
        )
        
        db_files = query.order_by(FileUpload.uploaded_at.desc()).all()
        
        # Also get files from file server for this job folder
        customer_email = current_user.get('email')
        folder = f"documents/{job_id}"
        file_server_result = await FileServerService.get_user_files(customer_email, folder)
        
        return {
            "files": [
                {
                    "id": f.id,
                    "filename": f.filename,
                    "original_filename": f.original_filename,
                    "file_size": f.file_size,
                    "mime_type": f.mime_type,
                    "upload_type": f.upload_type,
                    "description": f.description,
                    "tags": f.tags,
                    "uploaded_at": f.uploaded_at.isoformat(),
                    "file_url": f.file_server_url,
                    "folder": f.folder
                }
                for f in db_files
            ],
            "file_server_status": "success" if file_server_result["success"] else "error",
            "file_server_error": file_server_result.get("error") if not file_server_result["success"] else None,
            "job_id": job_id,
            "folder": folder
        }
        
    except Exception as e:
        logger.error(f"Error getting customer job files: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/customer/job/{job_id}")
async def update_customer_job(
    job_id: int,
    job_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update job information for the current customer"""
    try:
        # Verify the job belongs to the current customer
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.customer_id == current_user.get('user_id')
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found or access denied")
        
        # Separate business/branding fields (go to User model) from job fields
        business_fields = [
            'business_name', 'business_type', 'industry', 'industry_other',
            'brand_colors', 'brand_color_tags', 'brand_color_tag_others', 'brand_style', 'brand_style_other', 'brand_guidelines',
            'website_url', 'github_url', 'portfolio_url', 'social_media'
        ]
        
        job_fields = [
            'title', 'description', 'notes', 'additional_resource_info',
            'google_drive_links', 'github_repositories', 'workspace_links', 'additional_tools', 'server_details'
        ]
        
        # Update business/branding fields in User model (customer profile)
        customer = db.query(User).filter(User.id == current_user.get('user_id')).first()
        if customer:
            for field, value in job_data.items():
                if field in business_fields and hasattr(customer, field):
                    setattr(customer, field, value)
        
        # Update job fields in Job model
        for field, value in job_data.items():
            if field in job_fields and hasattr(job, field):
                setattr(job, field, value)
        
        db.commit()
        db.refresh(job)
        
        # Commit all changes
        db.commit()
        db.refresh(job)
        if customer:
            db.refresh(customer)
        
        return {
            "message": "Job and customer profile updated successfully",
            "job": {
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "notes": job.notes,
                "additional_resource_info": job.additional_resource_info,
                "google_drive_links": job.google_drive_links,
                "github_repositories": job.github_repositories,
                "workspace_links": job.workspace_links,
                "additional_tools": job.additional_tools,
                "server_details": job.server_details
            },
            "customer_profile": {
                "business_name": customer.business_name if customer else None,
                "business_type": customer.business_type if customer else None,
                "industry": customer.industry if customer else None,
                "industry_other": customer.industry_other if customer else None,
                "brand_colors": customer.brand_colors if customer else None,
                "brand_color_tags": customer.brand_color_tags if customer else None,
                "brand_color_tag_others": customer.brand_color_tag_others if customer else None,
                "brand_style": customer.brand_style if customer else None,
                "brand_style_other": customer.brand_style_other if customer else None,
                "brand_guidelines": customer.brand_guidelines if customer else None,
                "website_url": customer.website_url if customer else None,
                "github_url": customer.github_url if customer else None,
                "portfolio_url": customer.portfolio_url if customer else None,
                "social_media": customer.social_media if customer else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer job: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Admin endpoints
@router.get("/admin/files")
async def get_all_files(
    upload_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Get all files (admin only)"""
    try:
        # Get all active files from our database
        query = db.query(FileUpload).filter(
            FileUpload.is_active == True,
            FileUpload.is_deleted == False
        )
        
        if upload_type:
            query = query.filter(FileUpload.upload_type == upload_type)
        
        files = query.order_by(FileUpload.uploaded_at.desc()).all()
        
        return {
            "files": [
                {
                    "id": f.id,
                    "filename": f.filename,
                    "original_filename": f.original_filename,
                    "file_size": f.file_size,
                    "mime_type": f.mime_type,
                    "upload_type": f.upload_type,
                    "description": f.description,
                    "tags": f.tags,
                    "uploaded_at": f.uploaded_at.isoformat(),
                    "file_url": f.file_server_url,
                    "folder": f.folder,
                    "user_id": f.user_id,
                    "customer_id": f.customer_id,
                    "job_id": f.job_id
                }
                for f in files
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting all files: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
