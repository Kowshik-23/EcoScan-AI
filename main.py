from flask import Flask, request, render_template, redirect, url_for, jsonify
import os
import uuid
import requests
import base64
from supabase import create_client, Client

# --- Configuration ---
PIPEDREAM_WEBHOOK_URL = os.environ.get('PIPEDREAM_WEBHOOK_URL')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
app = Flask(__name__)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
UPLOAD_FOLDER = 'static/uploads' # Define this for the os.path.join
# --------------------

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def index():
    # This block handles the POST request when a user uploads a file via JavaScript fetch
    if request.method == 'POST':
        if 'waste_image' not in request.files:
            return jsonify({"success": False, "message": "No waste_image in request"}), 400

        file = request.files['waste_image']

        if file.filename == '':
            return jsonify({"success": False, "message": "No file selected"}), 400

        if file:
            unique_name = str(uuid.uuid4())
            # We don't need the extension for the db_key, just for the saved filename
            image_extension = os.path.splitext(file.filename)[1] if os.path.splitext(file.filename)[1] else '.jpg'
            image_filename = unique_name + image_extension
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            
            # Save the file locally first. We still need this for the image path in the DB.
            file.seek(0) # Rewind file pointer
            file.save(image_path)
            
            image_base64_data = None
            try:
                # Re-open and encode the saved file to ensure consistency
                with open(image_path, "rb") as image_file:
                    image_base64_data = base64.b64encode(image_file.read()).decode('utf-8')
                print(f"Image {unique_name} successfully encoded to Base64.")
            except Exception as e:
                print(f"!!! ERROR encoding image: {e}")
                return jsonify({"success": False, "message": "Error processing image"}), 500

            if image_base64_data:
                try:
                    supabase.table('submissions').insert({
                        "db_key": unique_name,
                        "status": "Pending",
                        "image_path": f"/{image_path}",
                    }).execute()
                    print(f"Initial pending record created for {unique_name}")
                except Exception as e:
                    print(f"!!! ERROR creating initial record in Supabase: {e}")
                    return jsonify({"success": False, "message": "Database error"}), 500

                webhook_payload = {
                    "db_key": unique_name,
                    "image_base64": image_base64_data, 
                    "user_lat": request.form.get('latitude'), 
                    "user_lon": request.form.get('longitude')
                }
                
                try:
                    requests.post(PIPEDREAM_WEBHOOK_URL, json=webhook_payload, timeout=20)
                    print("Webhook sent successfully.")
                except Exception as e:
                    print(f"!!! ERROR sending webhook: {e}")
            
            # This is the crucial change: Respond with JSON, not a redirect.
            return jsonify({"success": True, "message": "Upload successful, analysis started."})

    # --- This block handles the GET request (when a user visits or refreshes the page) ---
    try:
        response = supabase.table('submissions').select("*").order('created_at', desc=True).execute()
        submissions = response.data
    except Exception as e:
        print(f"!!! ERROR fetching from Supabase: {e}")
        submissions = []

    return render_template('index.html', submissions=submissions)


@app.route('/clear-history', methods=['POST'])
def clear_history():
    try:
        supabase.table('submissions').delete().neq('id', -1).execute()
        print("Successfully cleared submission history.")
    except Exception as e:
        print(f"!!! ERROR clearing history: {e}")
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
