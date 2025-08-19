"""
Flask Integration Example
========================

This example shows how to integrate the Stream-Line file server
with a Flask application.
"""

import os
from flask import Flask, request, jsonify, session, send_file
from werkzeug.utils import secure_filename
import tempfile

# Import the Stream-Line client (copy streamline_file_client.py to your project)
from streamline_file_client import StreamLineFileClient, StreamLineFileManager

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Configuration
STREAMLINE_SERVICE_TOKEN = os.getenv('STREAMLINE_SERVICE_TOKEN', 
                                   'ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340')

# Initialize clients
file_client = StreamLineFileClient(STREAMLINE_SERVICE_TOKEN)
file_manager = StreamLineFileManager(file_client)

# Example user session management (replace with your auth system)
def get_current_user_id():
    """Get current user ID from session (replace with your auth)."""
    return session.get('user_id', 'demo-user')

def require_auth(f):
    """Simple auth decorator (replace with your auth system)."""
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@app.route('/api/upload/profile-picture', methods=['POST'])
@require_auth
def upload_profile_picture():
    """
    Upload a user's profile picture.
    
    Expected: multipart/form-data with 'picture' file
    """
    if 'picture' not in request.files:
        return jsonify({'error': 'No picture file provided'}), 400
    
    file = request.files['picture']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    user_id = get_current_user_id()
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        file.save(temp_file.name)
        temp_path = temp_file.name
    
    try:
        # Upload to Stream-Line file server
        profile_url = file_manager.upload_profile_picture(
            user_id=user_id,
            image_path=temp_path
        )
        
        # Here you would typically save profile_url to your database
        # user.profile_picture_url = profile_url
        # db.session.commit()
        
        return jsonify({
            'success': True,
            'profile_url': profile_url,
            'message': 'Profile picture updated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Clean up temp file
        os.unlink(temp_path)


@app.route('/api/upload/document', methods=['POST'])
@require_auth
def upload_document():
    """
    Upload a document for the user.
    
    Expected: multipart/form-data with 'document' file and optional 'document_type'
    """
    if 'document' not in request.files:
        return jsonify({'error': 'No document file provided'}), 400
    
    file = request.files['document']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    document_type = request.form.get('document_type', 'general')
    user_id = get_current_user_id()
    
    # Save to temporary file
    filename = secure_filename(file.filename)
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}') as temp_file:
        file.save(temp_file.name)
        temp_path = temp_file.name
    
    try:
        # Upload to Stream-Line file server
        result = file_manager.upload_document(
            user_id=user_id,
            doc_path=temp_path,
            doc_type=document_type
        )
        
        # Here you would typically save document info to your database
        # document = Document(
        #     user_id=user_id,
        #     file_key=result['file_key'],
        #     public_url=result['public_url'],
        #     original_name=result['original_name'],
        #     document_type=document_type
        # )
        # db.session.add(document)
        # db.session.commit()
        
        return jsonify({
            'success': True,
            'public_url': result['public_url'],
            'file_key': result['file_key'],
            'original_name': result['original_name'],
            'size': result['size']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Clean up temp file
        os.unlink(temp_path)


@app.route('/api/upload/media', methods=['POST'])
@require_auth
def upload_media():
    """
    Upload media files (photos, videos, audio).
    
    Expected: multipart/form-data with 'media' file and optional 'media_type'
    """
    if 'media' not in request.files:
        return jsonify({'error': 'No media file provided'}), 400
    
    file = request.files['media']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    media_type = request.form.get('media_type', 'general')
    user_id = get_current_user_id()
    
    # Save to temporary file
    filename = secure_filename(file.filename)
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}') as temp_file:
        file.save(temp_file.name)
        temp_path = temp_file.name
    
    try:
        # Upload to Stream-Line file server
        result = file_manager.upload_media(
            user_id=user_id,
            media_path=temp_path,
            media_type=media_type
        )
        
        return jsonify({
            'success': True,
            'public_url': result['public_url'],
            'file_key': result['file_key'],
            'original_name': result['original_name'],
            'size': result['size'],
            'mime': result['mime']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Clean up temp file
        os.unlink(temp_path)


@app.route('/api/files', methods=['GET'])
@require_auth
def list_user_files():
    """Get all files for the authenticated user."""
    user_id = get_current_user_id()
    folder = request.args.get('folder')
    
    try:
        files = file_client.list_user_files(user_id, folder=folder)
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/files/<file_key>', methods=['DELETE'])
@require_auth
def delete_file(file_key):
    """Delete a file by its key."""
    try:
        success = file_client.delete_file(file_key)
        if success:
            # Here you would also delete from your database
            # Document.query.filter_by(file_key=file_key).delete()
            # db.session.commit()
            return jsonify({'success': True, 'message': 'File deleted'})
        else:
            return jsonify({'error': 'File deletion failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """Get user profile information."""
    user_id = get_current_user_id()
    
    # Get profile picture (you might cache this in your database)
    try:
        profile_picture_url = file_manager.get_user_profile_picture(user_id)
    except:
        profile_picture_url = None
    
    return jsonify({
        'user_id': user_id,
        'profile_picture_url': profile_picture_url
    })


@app.route('/api/documents', methods=['GET'])
@require_auth
def get_user_documents():
    """Get user's documents."""
    user_id = get_current_user_id()
    doc_type = request.args.get('type')
    
    try:
        documents = file_manager.get_user_documents(user_id, doc_type=doc_type)
        return jsonify({
            'documents': documents,
            'count': len(documents)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/media', methods=['GET'])
@require_auth
def get_user_media():
    """Get user's media files."""
    user_id = get_current_user_id()
    media_type = request.args.get('type')
    
    try:
        media = file_manager.get_user_media(user_id, media_type=media_type)
        return jsonify({
            'media': media,
            'count': len(media)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Check file server health."""
    try:
        health = file_client.get_health_status()
        return jsonify(health)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Simple login for demo (replace with your auth system)
@app.route('/login', methods=['POST'])
def login():
    """Simple login for demo purposes."""
    data = request.get_json()
    user_id = data.get('user_id', 'demo-user')
    session['user_id'] = user_id
    return jsonify({'success': True, 'user_id': user_id})


@app.route('/logout', methods=['POST'])
def logout():
    """Logout user."""
    session.pop('user_id', None)
    return jsonify({'success': True})


# HTML template for testing
@app.route('/')
def index():
    """Simple test page."""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Stream-Line File Server Test</title>
    </head>
    <body>
        <h1>Stream-Line File Server Integration Test</h1>
        
        <div id="auth">
            <h2>Login</h2>
            <input type="text" id="userId" placeholder="User ID" value="demo-user">
            <button onclick="login()">Login</button>
            <button onclick="logout()">Logout</button>
        </div>
        
        <div id="upload">
            <h2>Upload Profile Picture</h2>
            <input type="file" id="profilePic" accept="image/*">
            <button onclick="uploadProfilePicture()">Upload</button>
            
            <h2>Upload Document</h2>
            <input type="file" id="document">
            <select id="docType">
                <option value="general">General</option>
                <option value="contract">Contract</option>
                <option value="invoice">Invoice</option>
                <option value="receipt">Receipt</option>
            </select>
            <button onclick="uploadDocument()">Upload</button>
            
            <h2>Upload Media</h2>
            <input type="file" id="media" accept="image/*,video/*,audio/*">
            <select id="mediaType">
                <option value="general">General</option>
                <option value="photos">Photos</option>
                <option value="videos">Videos</option>
                <option value="audio">Audio</option>
            </select>
            <button onclick="uploadMedia()">Upload</button>
        </div>
        
        <div id="results">
            <h2>Results</h2>
            <div id="output"></div>
        </div>
        
        <script>
            async function login() {
                const userId = document.getElementById('userId').value;
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: userId})
                });
                const result = await response.json();
                updateOutput('Login: ' + JSON.stringify(result));
            }
            
            async function logout() {
                const response = await fetch('/logout', {method: 'POST'});
                const result = await response.json();
                updateOutput('Logout: ' + JSON.stringify(result));
            }
            
            async function uploadProfilePicture() {
                const fileInput = document.getElementById('profilePic');
                if (!fileInput.files[0]) return alert('Select a file');
                
                const formData = new FormData();
                formData.append('picture', fileInput.files[0]);
                
                const response = await fetch('/api/upload/profile-picture', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                updateOutput('Profile Upload: ' + JSON.stringify(result, null, 2));
            }
            
            async function uploadDocument() {
                const fileInput = document.getElementById('document');
                const docType = document.getElementById('docType').value;
                if (!fileInput.files[0]) return alert('Select a file');
                
                const formData = new FormData();
                formData.append('document', fileInput.files[0]);
                formData.append('document_type', docType);
                
                const response = await fetch('/api/upload/document', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                updateOutput('Document Upload: ' + JSON.stringify(result, null, 2));
            }
            
            async function uploadMedia() {
                const fileInput = document.getElementById('media');
                const mediaType = document.getElementById('mediaType').value;
                if (!fileInput.files[0]) return alert('Select a file');
                
                const formData = new FormData();
                formData.append('media', fileInput.files[0]);
                formData.append('media_type', mediaType);
                
                const response = await fetch('/api/upload/media', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                updateOutput('Media Upload: ' + JSON.stringify(result, null, 2));
            }
            
            function updateOutput(text) {
                document.getElementById('output').innerHTML += '<pre>' + text + '</pre>';
            }
        </script>
    </body>
    </html>
    '''


if __name__ == '__main__':
    app.run(debug=True, port=5000)
