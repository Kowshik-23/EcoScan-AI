from flask import Flask, request, render_template, redirect, url_for
import os
import uuid
import requests
import base64
from supabase import create_client, Client
import threading  # <--- NEW: Import the threading library

# --- Configuration ---
PIPEDREAM_WEBHOOK_URL = "https://eo8vcfmjs7fs71q.m.pipedream.net"
UPLOAD_FOLDER = 'static/uploads'
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
# --------------------

app = Flask(__name__)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- NEW: Helper function to send webhook in the background ---
def send_webhook_in_background(url, payload):
    """This function will be run in a separate thread."""
    try:
        print(f"Background thread sending webhook for key: {payload.get('db_key')}")
        requests.post(url, json=payload, timeout=20)
        print("Background webhook sent successfully.")
    except Exception as e:
        print(f"!!! ERROR in background webhook thread: {e}")
# -----------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # ... (all your file checking, saving, and base64 encoding logic is the same) ...
        if 'waste_image' not in request.files:
            return redirect(request.url)

        file = request.files['waste_image']

        if file.filename == '':
            return redirect(request.url)

        if file:
            # Note: I am assuming you have a `db_key` column of type `text` in Supabase
            # and you have set it as the Primary Key or at least UNIQUE.
            unique_name = str(uuid.uuid4())
            image_extension = os.path.splitext(file.filename)[1]
            image_filename = unique_name + image_extension
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            file.save(image_path)

            # (Your base64 encoding logic here...)
            image_base64_data = None
            try:
                with open(image_path, "rb") as image_file:
                    image_base64_data = base64.b64encode(image_file.read()).decode('utf-8')
            except Exception as e:
                print(f"Error encoding image: {e}")

            if image_base64_data:
                # Create initial record in Supabase
                try:
                    supabase.table('submissions').insert({
                        "db_key": unique_name,
                        "status": "Pending",
                        "image_path": f"/{image_path}",
                    }).execute()
                    print(f"Initial pending record created for {unique_name}")
                except Exception as e:
                    print(f"!!! ERROR creating initial record in Supabase: {e}")

                # Prepare payload for Pipedream
                webhook_payload = {
                    "db_key": unique_name,
                    "image_base64": image_base64_data, 
                    "user_lat": request.form.get('latitude'), 
                    "user_lon": request.form.get('longitude')
                }

                # --- NEW: Send webhook in a non-blocking thread ---
                webhook_thread = threading.Thread(
                    target=send_webhook_in_background,
                    args=(PIPEDREAM_WEBHOOK_URL, webhook_payload)
                )
                webhook_thread.start() # Start the thread
                # ----------------------------------------------------

        # The function now returns immediately, not waiting for the webhook.
        return redirect(url_for('index'))

    # --- GET request logic for fetching and displaying submissions ---
    try:
        response = supabase.table('submissions').select("*").order('created_at', desc=True).execute()
        submissions = response.data
    except Exception as e:
        print(f"!!! ERROR fetching from Supabase: {e}")
        submissions = []

    return render_template('index.html', submissions=submissions)
# ADD THIS NEW FUNCTION TO main.py



@app.route('/clear-history', methods=['POST'])
def clear_history():
    """
    This route deletes all rows from the submissions table.
    It's accessible to all users.
    """
    try:
        # This Supabase command deletes all rows from the 'submissions' table.
        # It works by matching all rows where the 'id' is not equal to a non-existent value.
        supabase.table('submissions').delete().neq('id', -1).execute()
        print("Successfully cleared submission history by user request.")
    except Exception as e:
        print(f"!!! ERROR clearing history: {e}")

    # After clearing, redirect the user back to the main page.
    return redirect(url_for('index'))
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)