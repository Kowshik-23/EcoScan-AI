# EcoScan AI ♻️

**EcoScan AI** is a real-time, AI-powered web application designed to help users correctly sort their waste. Users can take a photo of any waste item, and the application will instantly identify it, provide disposal instructions (Recycle, Compost, Trash, etc.), and find nearby disposal facilities.



---

### ✨ Features

- **Real-Time AI Analysis:** Uses Google's Gemini Pro Vision to identify waste from an image.
- **Intelligent Sorting:** Classifies items into categories like Recycle, Compost, Hazardous Waste, and Trash.
- **Plastic Identification:** Detects plastic resin numbers (e.g., #1 PETE) when visible.
- **Location-Based Facility Finder:** Finds nearby recycling centers or other facilities using the OpenStreetMap Overpass API.
- **Responsive Web Interface:** A clean, mobile-friendly frontend for easy use.
- **Instant Automation:** A serverless Pipedream workflow orchestrates the entire analysis process in real-time.

---

### 🛠️ Technology Stack

- **Frontend:** HTML, CSS, JavaScript (Hosted on Replit)
- **Backend Server:** Python (Flask) (Hosted on Replit)
- **Database:** Supabase (PostgreSQL)
- **AI Vision Model:** Google Gemini Pro Vision
- **Automation / "Glue":** Pipedream
- **Location Data:** OpenStreetMap (via Overpass API)

---

### 🚀 How to Run This Project

To set up and run this project locally or in your own cloud environment, you will need to configure the following services:

**1. Replit (or Local Python Environment):**
   - Fork this repository or clone it.
   - Install the required Python libraries:
     ```bash
     pip install Flask supabase requests
     ```
   - Set up the following environment variables (in Replit, use the "Secrets" tab):
     - `SUPABASE_URL`: Your Supabase project URL.
     - `SUPABASE_KEY`: Your Supabase `anon` public key.

**2. Supabase Project:**
   - Create a new project at [supabase.com](https://supabase.com).
   - Create a table named `submissions` with the following columns:
     - `id` (int8, primary key, generated)
     - `created_at` (timestamptz, default `now()`)
     - `db_key` (text, unique)
     - `status` (text, default `'Pending'`)
     - `image_path` (text)
     - `result_item` (text, nullable)
     - `result_action` (text, nullable)
     - `result_details` (text, nullable)
     - `result_locations` (jsonb, nullable)
     - `fallback_url` (text, nullable)

**3. Pipedream Workflow:**
   - Create a new workflow triggered by an HTTP Webhook. Copy the webhook URL.
   - Paste the webhook URL into the `PIPEDREAM_WEBHOOK_URL` variable in the `main.py` file.
   - Set up the following Environment Variables in your Pipedream project settings:
     - `GEMINI_API_KEY`: Your API key from Google AI Studio.
     - `SUPABASE_URL`: Your Supabase project URL.
     - `SUPABASE_ANON_KEY`: Your Supabase `anon` public key.
   - Recreate the workflow steps (or import the workflow if exported) as detailed in the project's development history.

## 🚀 Live Demo

**You can try EcoScan AI live at:** [**https://ecoscan-ai.onrender.com**](https://ecoscan-ai.onrender.com)

*Note: The free-tier instance may take 30-60 seconds to "wake up" on the first request if it has been inactive.*

---
