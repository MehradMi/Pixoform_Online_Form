from flask import Flask, request, jsonify, send_from_directory, render_template
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
import re
from datetime import datetime
import os

app = Flask(__name__)

# ===== Email Configuration =====
EMAIL_CONFIG = {
    'smtp_server': 'mail.privateemail.com',
    'smtp_port': 587,  # TLS
    'email': 'info@pixoform.com',
    'password': 'G6F$b*7F*4$F',  # replace with your password
    'from_name': 'تیم پیکسوفرم'
}

# ===== Database Setup =====
DB_PATH = "submissions.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS form_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            instagram_link TEXT,
            service_type TEXT NOT NULL,
            project_description TEXT NOT NULL,
            budget_timeline TEXT,
            additional_info TEXT,
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_submission(form_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO form_submissions 
        (name, email, phone_number, instagram_link, service_type, project_description, budget_timeline, additional_info)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        form_data.get('name'),
        form_data.get('email'),
        form_data.get('phone_number'),
        form_data.get('instagram_link'),
        form_data.get('service_type'),
        form_data.get('project_description'),
        form_data.get('budget_timeline'),
        form_data.get('additional_info')
    ))
    conn.commit()
    submission_id = cursor.lastrowid
    conn.close()
    return submission_id

def validate_email(email):
    """Validate email format with proper regex"""
    if not email or not isinstance(email, str):
        return False
    
    # More comprehensive email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63}$'
    
    # Check basic format
    if not re.match(pattern, email):
        return False
    
    # Additional checks
    if '..' in email:  # No consecutive dots
        return False
    if email.startswith('.') or email.endswith('.'):  # No leading/trailing dots
        return False
    if email.count('@') != 1:  # Exactly one @ symbol
        return False
    
    # Check domain part
    domain = email.split('@')[1]
    if domain.startswith('-') or domain.endswith('-'):  # Domain can't start/end with hyphen
        return False
    
    return True

def validate_phone_number(phone):
    """Validate Iranian phone number format: 09xxxxxxxxx (11 digits starting with 09)"""
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove any spaces, dashes, or other characters
    clean_phone = re.sub(r'[^\d]', '', phone)
    
    # Check if it matches the pattern: 09 followed by 9 digits
    pattern = r'^09\d{9}$'
    
    return bool(re.match(pattern, clean_phone)) and len(clean_phone) == 11

def normalize_phone_number(phone):
    """Clean and normalize phone number"""
    if not phone:
        return phone
    
    # Remove all non-digit characters
    clean_phone = re.sub(r'[^\d]', '', phone)
    return clean_phone

# ===== Email Sending Functions =====
def send_confirmation_email(form_data):
    try:
        print(f"Sending confirmation email to: {form_data['email']}")
        
        msg = MIMEMultipart()
        msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['email']}>"
        msg['To'] = form_data['email']
        msg['Subject'] = "تایید ثبت فرم - پیکسوفرم"
        
        # Format phone number for display
        phone_display = form_data.get('phone_number', 'وارد نشده')
        if phone_display and phone_display != 'وارد نشده':
            # Format as 09XX-XXX-XXXX for better readability
            if len(phone_display) == 11:
                phone_display = f"{phone_display[:4]}-{phone_display[4:7]}-{phone_display[7:]}"

        html_body = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="fa">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Tahoma', 'Arial', sans-serif;
                    direction: rtl;
                    text-align: right;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: normal;
                }}
                .header p {{
                    margin: 10px 0 0;
                    font-size: 16px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 30px;
                }}
                .greeting {{
                    font-size: 18px;
                    margin-bottom: 20px;
                    color: #333;
                }}
                .info-section {{
                    background: #f8f9ff;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-right: 4px solid #667eea;
                }}
                .info-section h3 {{
                    color: #667eea;
                    margin: 0 0 15px;
                    font-size: 18px;
                }}
                .info-item {{
                    margin: 10px 0;
                    padding: 8px 0;
                    border-bottom: 1px solid #eee;
                }}
                .info-item:last-child {{
                    border-bottom: none;
                }}
                .info-label {{
                    font-weight: bold;
                    color: #555;
                    display: inline-block;
                    min-width: 140px;
                }}
                .info-value {{
                    color: #333;
                }}
                .service-tag {{
                    background: #667eea;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 15px;
                    font-size: 14px;
                    display: inline-block;
                }}
                .description-box {{
                    background: #f9f9f9;
                    padding: 15px;
                    border-radius: 5px;
                    border-right: 3px solid #667eea;
                    margin: 10px 0;
                    font-style: italic;
                }}
                .next-steps {{
                    background: linear-gradient(45deg, #e8f4fd, #f0f8ff);
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #b3d9ff;
                    margin: 20px 0;
                }}
                .next-steps h3 {{
                    color: #667eea;
                    margin: 0 0 10px;
                }}
                .footer {{
                    background: #333;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    font-size: 14px;
                }}
                .footer a {{
                    color: #667eea;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>تایید دریافت فرم</h1>
                    <p>پیکسوفرم - خلاقیت بی‌حد و حصر</p>
                </div>
                
                <div class="content">
                    <div class="greeting">
                        سلام {form_data.get('name', '')} عزیز،
                    </div>
                    
                    <p>از ارسال فرم درخواست پروژه شما متشکریم. اطلاعات ارسالی شما با موفقیت دریافت شد و در ادامه تمامی جزئیات ثبت‌شده را مشاهده می‌کنید:</p>
                    
                    <div class="info-section">
                        <h3>اطلاعات تماس</h3>
                        <div class="info-item">
                            <span class="info-label">نام و نام خانوادگی:</span>
                            <span class="info-value">{form_data.get('name')}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">آدرس ایمیل:</span>
                            <span class="info-value">{form_data.get('email')}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">شماره تماس:</span>
                            <span class="info-value">{phone_display}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">پروفایل اینستاگرام:</span>
                            <span class="info-value">{form_data.get('instagram_link') or 'ارائه نشده'}</span>
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <h3>جزئیات پروژه</h3>
                        <div class="info-item">
                            <span class="info-label">نوع خدمت:</span>
                            <span class="service-tag">{form_data.get('service_type')}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">توضیحات پروژه:</span>
                            <div class="description-box">{form_data.get('project_description')}</div>
                        </div>
                        {f'''
                        <div class="info-item">
                            <span class="info-label">بودجه و زمان‌بندی:</span>
                            <div class="description-box">{form_data.get('budget_timeline')}</div>
                        </div>
                        ''' if form_data.get('budget_timeline') else ''}
                        {f'''
                        <div class="info-item">
                            <span class="info-label">اطلاعات تکمیلی:</span>
                            <div class="description-box">{form_data.get('additional_info')}</div>
                        </div>
                        ''' if form_data.get('additional_info') else ''}
                    </div>
                    
                    <div class="next-steps">
                        <h3>مراحل بعدی</h3>
                        <p>تیم متخصص ما فرم شما را بررسی کرده و حداکثر ظرف ۲۴ تا ۴۸ ساعت آینده با شما تماس خواهند گرفت.</p>
                        <p>ما مشتاقانه منتظر همکاری با شما و تحقق ایده‌های خلاقانه‌تان هستیم! 🎨✨</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>این پیام به‌صورت خودکار از سیستم پیکسوفرم ارسال شده است.</p>
                    <p>برای هرگونه سوال، می‌توانید به این ایمیل پاسخ دهید یا با <a href="mailto:info@pixoform.com">info@pixoform.com</a> در ارتباط باشید.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        server.send_message(msg)
        print("✅ Confirmation email sent successfully")
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        return False

def send_internal_notification(form_data, submission_id):
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['email']}>"
        msg['To'] = EMAIL_CONFIG['email']
        msg['Subject'] = f"فرم جدید #{submission_id} - {form_data.get('name')}"

        # Format phone number for display
        phone_display = form_data.get('phone_number', 'ارائه نشده')
        if phone_display and phone_display != 'ارائه نشده':
            if len(phone_display) == 11:
                phone_display = f"{phone_display[:4]}-{phone_display[4:7]}-{phone_display[7:]}"

        html_body = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="fa">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Tahoma', 'Arial', sans-serif;
                    direction: rtl;
                    text-align: right;
                    line-height: 1.6;
                    color: #333;
                }}
                .header {{
                    background: #667eea;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .info-item {{
                    margin: 10px 0;
                    padding: 10px;
                    background: #f9f9f9;
                    border-right: 3px solid #667eea;
                }}
                .label {{
                    font-weight: bold;
                    color: #555;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>فرم جدید دریافت شد - شماره #{submission_id}</h2>
                <p>زمان ثبت: {datetime.now().strftime('%Y/%m/%d - %H:%M')}</p>
            </div>
            
            <div class="info-item">
                <span class="label">نام:</span> {form_data.get('name')}
            </div>
            <div class="info-item">
                <span class="label">ایمیل:</span> <a href="mailto:{form_data.get('email')}">{form_data.get('email')}</a>
            </div>
            <div class="info-item">
                <span class="label">شماره تماس:</span> <a href="tel:{form_data.get('phone_number')}">{phone_display}</a>
            </div>
            <div class="info-item">
                <span class="label">اینستاگرام:</span> {form_data.get('instagram_link') or 'ارائه نشده'}
            </div>
            <div class="info-item">
                <span class="label">نوع خدمت:</span> <strong>{form_data.get('service_type')}</strong>
            </div>
            <div class="info-item">
                <span class="label">توضیحات پروژه:</span><br>{form_data.get('project_description')}
            </div>
            <div class="info-item">
                <span class="label">بودجه و زمان‌بندی:</span><br>{form_data.get('budget_timeline') or 'مشخص نشده'}
            </div>
            <div class="info-item">
                <span class="label">اطلاعات اضافی:</span><br>{form_data.get('additional_info') or 'ندارد'}
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        server.send_message(msg)
        print("✅ Internal notification sent successfully")
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Internal notification error: {e}")
        return False

# ===== API Route =====
@app.route("/submit-form", methods=["POST"])
def submit_form():
    try:
        data = request.get_json()
        
        # Define required fields
        required_fields = ["name", "email", "phone_number", "service_type", "project_description"]
        
        # Check for missing required fields
        missing_fields = []
        for field in required_fields:
            if not data.get(field) or str(data.get(field)).strip() == "":
                missing_fields.append(field)
        
        if missing_fields:
            field_names = {
                "name": "نام",
                "email": "ایمیل", 
                "phone_number": "شماره تماس",
                "service_type": "نوع خدمت",
                "project_description": "توضیحات پروژه"
            }
            missing_persian = [field_names.get(field, field) for field in missing_fields]
            return jsonify({
                "error": f"فیلدهای الزامی وارد نشده: {', '.join(missing_persian)}"
            }), 400

        # Validate email format
        email = data.get("email", "").strip()
        if not validate_email(email):
            return jsonify({
                "error": "آدرس ایمیل وارد شده معتبر نیست. لطفاً یک آدرس ایمیل صحیح وارد کنید."
            }), 400

        # Validate and normalize phone number
        phone = data.get("phone_number", "").strip()
        if not validate_phone_number(phone):
            return jsonify({
                "error": "شماره تماس باید به فرمت 09xxxxxxxxx وارد شود (۱۱ رقم که با ۰۹ شروع شود)"
            }), 400
        
        # Normalize phone number (remove any formatting)
        data["phone_number"] = normalize_phone_number(phone)
        
        # Additional validations
        if len(data.get("name", "").strip()) < 2:
            return jsonify({
                "error": "نام باید حداقل ۲ کاراکتر باشد"
            }), 400
            
        if len(data.get("project_description", "").strip()) < 10:
            return jsonify({
                "error": "توضیحات پروژه باید حداقل ۱۰ کاراکتر باشد"
            }), 400

        # Save submission to database
        submission_id = save_submission(data)
        print(f"✅ Form saved with ID: {submission_id}")

        # Send confirmation email to user
        email_sent = send_confirmation_email(data)

        # Send notification email to admin
        notification_sent = send_internal_notification(data, submission_id)

        response_data = {
            "success": True,
            "message": "فرم شما با موفقیت ثبت شد و به زودی تیم ما با شما تماس خواهد گرفت",
            "submission_id": submission_id
        }
        
        if not email_sent:
            response_data["warning"] = "فرم ثبت شد اما ایمیل تایید ارسال نشد"
            
        if not notification_sent:
            print("⚠️ Warning: Internal notification failed")

        return jsonify(response_data), 200

    except Exception as e:
        print(f"❌ Form submission error: {e}")
        return jsonify({
            "error": "خطای داخلی سرور. لطفاً دوباره تلاش کنید."
        }), 500

# ===== Test email route (for debugging) =====
@app.route("/test-email", methods=["GET"])
def test_email():
    """Test route to check email functionality"""
    test_data = {
        'name': 'تست کاربر',
        'email': 'test@example.com',
        'phone_number': '09123456789',
        'instagram_link': 'https://instagram.com/test',
        'service_type': 'ریل',
        'project_description': 'این یک پروژه تست است',
        'budget_timeline': 'حدود یک هفته',
        'additional_info': 'اطلاعات اضافی تست'
    }
    
    success = send_confirmation_email(test_data)
    
    if success:
        return jsonify({"message": "ایمیل تست با موفقیت ارسال شد"}), 200
    else:
        return jsonify({"error": "خطا در ارسال ایمیل تست"}), 500

# ===== Serve frontend file =====
@app.route("/")
def index():
    return render_template("form-frontend.html")

# ===== Get all submissions (admin route) =====
@app.route("/api/submissions", methods=["GET"])
def get_submissions():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, email, phone_number, instagram_link, service_type, 
                   project_description, budget_timeline, additional_info, submission_date
            FROM form_submissions 
            ORDER BY submission_date DESC
        ''')
        
        submissions = []
        for row in cursor.fetchall():
            submissions.append({
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'phone_number': row[3],
                'instagram_link': row[4],
                'service_type': row[5],
                'project_description': row[6],
                'budget_timeline': row[7],
                'additional_info': row[8],
                'submission_date': row[9]
            })
        
        conn.close()
        return jsonify(submissions), 200
        
    except Exception as e:
        print(f"Error fetching submissions: {e}")
        return jsonify({'error': 'خطا در دریافت اطلاعات'}), 500

if __name__ == "__main__":
    init_db()
    print("🚀 Starting Pixoform server...")
    print("📧 Email configured for:", EMAIL_CONFIG['email'])
    print("🔗 Visit: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)