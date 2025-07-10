from flask import Flask, request, render_template, redirect, url_for, jsonify
import os
import uuid
import requests
import base64
from supabase import create_client, Client

# --- Configuration ---
PIPEDREAM_WEBHOOK_URL = "https://eo8vcfmjs7fs71q.m.pipedream.net"
UPLOAD_FOLDER = 'static/uploads'
# Use Replit Secrets to store your Supabase credentials securely
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
# --------------------

app = Flask(__name__)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def index():
    # This block handles the POST request when a user uploads a file
    if request.method == 'POST':
        if 'waste_image' not in request.files:
            return redirect(request.url)

        file = request.files['waste_image']

        if file.filename == '':
            return redirect(request.url)

        if file:
            # Generate a unique key for this submission
            unique_name = str(uuid.uuid4())
            image_extension = os.path.splitext(file.filename)[1]
            image_filename = unique_name + image_extension
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            file.save(image_path)

            image_base64_data = None
            try:
                # Read and encode the image to send to Pipedream
                with open(image_path, "rb") as image_file:
                    image_base64_data = base64.b64encode(image_file.read()).decode('utf-8')
                print(f"Image {unique_name} successfully encoded to Base64.")
            except Exception as e:
                print(f"!!! ERROR encoding image: {e}")

            if image_base64_data:
                # 1. Create the initial "Pending" record in your Supabase database
                try:
                    supabase.table('submissions').insert({
                        "db_key": unique_name,
                        "status": "Pending",
                        "image_path": f"/{image_path}",
                    }).execute()
                    print(f"Initial pending record created for {unique_name}")
                except Exception as e:
                    print(f"!!! ERROR creating initial record in Supabase: {e}")

                # 2. Prepare the data to send to the Pipedream workflow
                webhook_payload = {
                    "db_key": unique_name,
                    "image_base64": image_base64_data, 
                    "user_lat": request.form.get('latitude'), 
                    "user_lon": request.form.get('longitude')
                }

                # 3. Send the webhook to trigger the Pipedream automation
                try:
                    # This is a direct, simple request. No threading needed.
                    print(f"Sending webhook to Pipedream for key: {unique_name}")
                    requests.post(PIPEDREAM_WEBHOOK_URL, json=webhook_payload, timeout=20)
                    print("Webhook sent successfully.")
                except Exception as e:
                    print(f"!!! ERROR sending webhook: {e}")

        # After the POST request is handled, redirect back to the main page
        return redirect(url_for('index'))

    # --- This block handles the GET request (when a user visits or refreshes the page) ---
    try:
        # Fetch all submissions from Supabase, ordered by newest first
        response = supabase.table('submissions').select("*").order('created_at', desc=True).execute()
        submissions = response.data
    except Exception as e:
        print(f"!!! ERROR fetching from Supabase: {e}")
        submissions = []

    # Render the HTML page, passing the list of submissions to it
    return render_template('index.html', submissions=submissions)


@app.route('/clear-history', methods=['POST'])
def clear_history():
    """ This route deletes all rows from the submissions table. """
    try:
        supabase.table('submissions').delete().neq('id', -1).execute()
        print("Successfully cleared submission history by user request.")
    except Exception as e:
        print(f"!!! ERROR clearing history: {e}")

    # After clearing, redirect the user back to the main page
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
