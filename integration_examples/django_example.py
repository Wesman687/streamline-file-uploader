"""
Django Integration Example
=========================

This example shows how to integrate the Stream-Line file server
with a Django application.
"""

import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
import json

# Import the Stream-Line client (copy streamline_file_client.py to your project)
from streamline_file_client import StreamLineFileClient, StreamLineFileManager

# Configuration
STREAMLINE_SERVICE_TOKEN = getattr(settings, 'STREAMLINE_SERVICE_TOKEN', 
                                 'ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340')

# Initialize clients
file_client = StreamLineFileClient(STREAMLINE_SERVICE_TOKEN)
file_manager = StreamLineFileManager(file_client)


# Example Django Models
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UserDocument(models.Model):
    DOCUMENT_TYPES = [
        ('contract', 'Contract'),
        ('invoice', 'Invoice'),
        ('receipt', 'Receipt'),
        ('id', 'Identification'),
        ('general', 'General Document'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='general')
    file_key = models.CharField(max_length=255)
    public_url = models.URLField()
    original_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)


# Django Views

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def upload_profile_picture(request):
    """
    Upload a user's profile picture.
    
    Expected: multipart/form-data with 'picture' file
    """
    if 'picture' not in request.FILES:
        return JsonResponse({'error': 'No picture file provided'}, status=400)
    
    uploaded_file = request.FILES['picture']
    
    # Save temporarily
    temp_path = default_storage.save(f'temp/{uploaded_file.name}', uploaded_file)
    temp_full_path = default_storage.path(temp_path)
    
    try:
        # Upload to Stream-Line file server
        profile_url = file_manager.upload_profile_picture(
            user_id=str(request.user.id),
            image_path=temp_full_path
        )
        
        # Update user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.profile_picture_url = profile_url
        profile.save()
        
        # Clean up temp file
        default_storage.delete(temp_path)
        
        return JsonResponse({
            'success': True,
            'profile_url': profile_url
        })
        
    except Exception as e:
        # Clean up temp file
        default_storage.delete(temp_path)
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def upload_document(request):
    """
    Upload a document for the user.
    
    Expected: multipart/form-data with 'document' file and 'document_type'
    """
    if 'document' not in request.FILES:
        return JsonResponse({'error': 'No document file provided'}, status=400)
    
    uploaded_file = request.FILES['document']
    document_type = request.POST.get('document_type', 'general')
    
    # Save temporarily
    temp_path = default_storage.save(f'temp/{uploaded_file.name}', uploaded_file)
    temp_full_path = default_storage.path(temp_path)
    
    try:
        # Upload to Stream-Line file server
        result = file_manager.upload_document(
            user_id=str(request.user.id),
            doc_path=temp_full_path,
            doc_type=document_type
        )
        
        # Save document record
        document = UserDocument.objects.create(
            user=request.user,
            document_type=document_type,
            file_key=result['file_key'],
            public_url=result['public_url'],
            original_name=result['original_name'],
            file_size=result['size']
        )
        
        # Clean up temp file
        default_storage.delete(temp_path)
        
        return JsonResponse({
            'success': True,
            'document_id': document.id,
            'public_url': result['public_url'],
            'file_key': result['file_key']
        })
        
    except Exception as e:
        # Clean up temp file
        default_storage.delete(temp_path)
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def list_user_documents(request):
    """Get all documents for the authenticated user."""
    document_type = request.GET.get('type')
    
    # Get from database (faster than API call)
    queryset = UserDocument.objects.filter(user=request.user)
    if document_type:
        queryset = queryset.filter(document_type=document_type)
    
    documents = list(queryset.values(
        'id', 'document_type', 'public_url', 'original_name', 
        'file_size', 'uploaded_at'
    ))
    
    return JsonResponse({
        'documents': documents,
        'count': len(documents)
    })


@login_required
def get_user_profile(request):
    """Get user profile with picture URL."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        profile_picture_url = profile.profile_picture_url
    except UserProfile.DoesNotExist:
        profile_picture_url = None
    
    return JsonResponse({
        'user_id': request.user.id,
        'username': request.user.username,
        'profile_picture_url': profile_picture_url
    })


# Django URLs (add to your urls.py)
"""
from django.urls import path
from . import views

urlpatterns = [
    path('api/upload/profile-picture/', views.upload_profile_picture, name='upload_profile_picture'),
    path('api/upload/document/', views.upload_document, name='upload_document'),
    path('api/documents/', views.list_user_documents, name='list_documents'),
    path('api/profile/', views.get_user_profile, name='get_profile'),
]
"""

# Django Settings (add to settings.py)
"""
# Stream-Line File Server Configuration
STREAMLINE_SERVICE_TOKEN = os.getenv('STREAMLINE_SERVICE_TOKEN', 'your-token-here')
"""

# Example Django Template Usage
"""
<!-- In your HTML template -->
{% if user.userprofile.profile_picture_url %}
    <img src="{{ user.userprofile.profile_picture_url }}" alt="Profile Picture" class="profile-pic">
{% else %}
    <img src="{% static 'images/default-avatar.png' %}" alt="Default Avatar" class="profile-pic">
{% endif %}

<!-- Document list -->
<div id="documents">
    {% for doc in user_documents %}
        <div class="document-item">
            <a href="{{ doc.public_url }}" download="{{ doc.original_name }}">
                📄 {{ doc.original_name }}
            </a>
            <span class="doc-type">{{ doc.get_document_type_display }}</span>
        </div>
    {% endfor %}
</div>
"""

# JavaScript for file uploads
"""
// Upload profile picture
async function uploadProfilePicture(fileInput) {
    const formData = new FormData();
    formData.append('picture', fileInput.files[0]);
    
    try {
        const response = await fetch('/api/upload/profile-picture/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const result = await response.json();
        if (result.success) {
            // Update profile picture immediately
            document.querySelector('.profile-pic').src = result.profile_url;
            alert('Profile picture updated!');
        } else {
            alert('Upload failed: ' + result.error);
        }
    } catch (error) {
        alert('Upload error: ' + error.message);
    }
}

// Upload document
async function uploadDocument(fileInput, documentType) {
    const formData = new FormData();
    formData.append('document', fileInput.files[0]);
    formData.append('document_type', documentType);
    
    try {
        const response = await fetch('/api/upload/document/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const result = await response.json();
        if (result.success) {
            // Add to document list or refresh
            location.reload(); // Simple refresh, or update DOM dynamically
        } else {
            alert('Upload failed: ' + result.error);
        }
    } catch (error) {
        alert('Upload error: ' + error.message);
    }
}
"""
