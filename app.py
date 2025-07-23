from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from fpdf import FPDF
from datetime import datetime
import re
import os
import random
from werkzeug.utils import secure_filename
import json
from flask import current_app
from datetime import datetime, timezone
from flask_mail import Mail, Message


app = Flask(__name__)

@app.route('/manage-password')
def manage_password():
    return render_template('your_template.html') 

CORS(app, resources={r"/api/*": {"origins": "http://127.0.0.1:5000"}})

mail = Mail(app)

mysql = MySQL(app)


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'otp.ayubogo@gmail.com'
app.config['MAIL_PASSWORD'] = 'vczl zkch cjwy pknc'
app.config['MAIL_DEFAULT_SENDER'] = 'otp.ayubogo@gmail.com'

mail = Mail(app)


# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'tourism_db'



@app.route('/api/send-email', methods=['POST'])
def send_email():
    data = request.get_json()

    user_id = data.get('userID')
    booking_id = data.get('booking_id')
    amount = data.get('amount')

    print("Received:", user_id, booking_id, amount)

    # Get user email and name from DB
    cur = mysql.connection.cursor()
    cur.execute("SELECT email, first_name FROM tourists WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    user_email = user[0]
    user_name = user[1]

    # Validate required fields
    if not all([user_email, booking_id, amount]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Prepare and send the email
    msg = Message('Payment Confirmation - Ayubogo',
                  recipients=[user_email])
    msg.body = f"""Hello {user_name},

Thank you for your payment!

Booking ID: {booking_id}
Amount Paid: ${amount}

Best regards,  
Ayubogo Team
"""

    try:
        mail.send(msg)
        return jsonify({'message': 'Email sent successfully'}), 200
    except Exception as e:
        print("Error sending email:", e)
        return jsonify({'error': str(e)}), 500



@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    try:
        # First get the tourist_id from the tourists table using email (UserName)
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM tourists WHERE first_name = %s", (data['userName'],))
        tourist = cur.fetchone()
        
        if not tourist:
            return jsonify({"success": False, "error": "User not found"})
            
        tourist_id = tourist[0]

        # Insert booking with tourist_id
        cur.execute("""
            INSERT INTO Bookings (tourist_id, UserName, ArrivalDate, DepartureDate, Adults, Children1to5, Children6to11)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (tourist_id, data['userName'], data['arrivalDate'], data['departureDate'], 
              data['adults'], data['children1to5'], data['children6to11']))
              
        mysql.connection.commit()
        booking_id = cur.lastrowid
        cur.close()

        return jsonify({"success": True, "ID": booking_id})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/update/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    data = request.json
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE Bookings
            SET ArrivalDate = %s, DepartureDate = %s, Adults = %s, Children1to5 = %s, Children6to11 = %s
            WHERE ID = %s
        """, (data['arrivalDate'], data['departureDate'], data['adults'], 
              data['children1to5'], data['children6to11'], booking_id))
        mysql.connection.commit()
        cursor.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/delete/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM Bookings WHERE ID = %s", (booking_id,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/rate")
def rate():
    return render_template("rate-experiences.html")

@app.route("/profile2")
def profile2():
    # Check if user is logged in/registered
    if not all(key in request.cookies for key in ['user_id', 'user_email', 'user_type']):
        return redirect('/login')
    
    try:
        cur = mysql.connection.cursor()
        # Get tourist data by ID from cookie
        cur.execute("SELECT * FROM tourists WHERE id = %s", (request.cookies.get('user_id'),))
        tourist = cur.fetchone()
        
        if tourist:
            # Prepare tourist data for template
            tourist_data = {
                'id': tourist[0],
                'first_name': tourist[1],
                'middle_name': tourist[2],
                'last_name': tourist[3],
                'email': tourist[4],
                'country': tourist[6],
                'dob': tourist[7],
                'first_time_visitor': "yes" if tourist[8] == 1 else "no",
                'passport_number': tourist[9],
                # Don't include password in the template data
                'full_name': f"{tourist[1]} {tourist[3]}"  # First + Last name
            }
            return render_template('profile2.html', tourist=tourist_data)
        else:
            return redirect('/login')
    except Exception as e:
        print(f"Error: {e}")
        return redirect('/login')
    finally:
        if 'cur' in locals():
            cur.close()

@app.route("/userdash")
def dash():
    return render_template("userdash.html")

@app.route("/arts")
def art():
    return render_template("arts.html")

@app.route("/performing-arts")
def perf():
    return render_template("performing-art.html")   

@app.route("/aboutus")
def about():
    return render_template("aboutus.html")

@app.route("/managepassword", methods=['GET', 'POST'])
def manage():
    if request.method == 'POST':
        # Get form data
        current_password = request.form.get('currentPassword')
        new_password = request.form.get('newPassword')
        
        # Basic validation
        if not current_password or not new_password:
            return jsonify({'success': False, 'message': 'Both current and new password are required'})
        
        try:
            cur = mysql.connection.cursor()
            
            # Get the current user (you should use session/user_id in a real app)
            cur.execute("SELECT id, password FROM tourists ORDER BY id DESC LIMIT 1")
            user = cur.fetchone()
            
            if not user:
                return jsonify({'success': False, 'message': 'User not found'})
            
            user_id, stored_password = user
            
            # Verify current password
            if not check_password_hash(stored_password, current_password):
                return jsonify({'success': False, 'message': 'Current password is incorrect'})
            
            # Hash new password
            new_hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            
            # Update with new hashed password
            cur.execute("UPDATE tourists SET password = %s WHERE id = %s", (new_hashed_password, user_id))
            mysql.connection.commit()
            
            return jsonify({'success': True, 'message': 'Password updated successfully'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})
            
        finally:
            if cur:
                cur.close()
    
    # GET request - show password change form
    return render_template("managepassword.html")

@app.route('/api/feedback', methods=['GET'])
def api_feedback():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT feedback_type, rating, comments FROM feedbacktable")
        feedbacks = cur.fetchall()
        
        if not feedbacks:
            return jsonify({'success': False, 'message': 'No feedback found'})
        
        # Convert result to list of dictionaries
        feedback_list = []
        for row in feedbacks:
            feedback_list.append({
                'feedback_type': row[0],
                'rating': row[1],
                'comments': row[2]
            })

        return jsonify({'success': True, 'data': feedback_list})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

    finally:
        if cur:
            cur.close()

@app.route("/feedback", methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        try:
            # Get form data
            feedback_type = request.form['feedback_type']
            rating = request.form['rating']
            comments = request.form.get('comments', '')
            
            # Get user info from cookies if available
            
            user_email = request.cookies.get('user_email')
            user_first_name = request.cookies.get('user_first_name')
            user_last_name = request.cookies.get('user_last_name')

            # Create cursor
            cur = mysql.connection.cursor()

            # Insert feedback into database
            cur.execute("""
                INSERT INTO feedbacktable (feedback_type, rating, comments, user_id, user_email, first_name, last_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (feedback_type, rating, comments, user_email, user_first_name, user_last_name))

            mysql.connection.commit()
            cur.close()

            # Return success response
            return jsonify({
                'success': True, 
                'message': 'Feedback submitted successfully!'
            })

        except Exception as e:
            # Handle errors
            return jsonify({
                'success': False, 
                'message': f'Error submitting feedback: {str(e)}'
            }), 500

    # Render feedback page for GET requests
    return render_template('feedback.html')

@app.route('/logout')
def logout():
    response = make_response(redirect('/login')) 
    response.delete_cookie('user_email')
    response.delete_cookie('user_type')
    response.delete_cookie('user_first_name')
    response.delete_cookie('user_last_name')
    response.delete_cookie('user_id')
    response.delete_cookie('user_phone')
    response.delete_cookie('user_address')
    response.delete_cookie('user_passport')
    response.delete_cookie('user_image')
    return response

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return jsonify({
                'success': False, 
                'message': 'Email and password are required'
            })

        try:
            cur = mysql.connection.cursor()

            # Check in tourists table first
            cur.execute("SELECT id, first_name, last_name, password FROM tourists WHERE email = %s", (email,))
            tourist = cur.fetchone()

            if tourist:
                tourist_id, first_name, last_name, stored_password = tourist
                if check_password_hash(stored_password, password):
                    # Create response with success message
                    response = make_response(jsonify({
                        'success': True, 
                        'message': 'Login successful!', 
                        'redirect': 'userdash',
                        'user_type': 'tourist',
                        'user_id': tourist_id,
                        'user_firstName': first_name,
                        'user_lastName': last_name
                    }))
                    
                    # Set secure cookies with user information
                    response.set_cookie('user_id', str(tourist_id), 
                                      httponly=False, secure=False, samesite='Lax')
                    response.set_cookie('user_email', email, 
                                      httponly=False, secure=False, samesite='Lax')
                    response.set_cookie('user_type', 'tourist', 
                                      httponly=False, secure=False, samesite='Lax')
                    response.set_cookie('user_first_name', first_name, 
                                      httponly=False, secure=False, samesite='Lax')
                    response.set_cookie('user_last_name', last_name, 
                                      httponly=False, secure=False, samesite='Lax')
                    
                    return response
            
            # If not found in tourists, check in admin table
            cur.execute("SELECT userid, password FROM admin WHERE email = %s", (email,))
            admin = cur.fetchone()
            
            if admin:
                admin_id, stored_password = admin
                if check_password_hash(stored_password, password):
                    response = make_response(jsonify({
                        'success': True, 
                        'message': 'Admin login successful!', 
                        'redirect': 'admin',
                        'user_type': 'admin',
                        'user_id': admin_id
                    }))
                    response.set_cookie('user_id', str(admin_id), 
                                      httponly=False, secure=False, samesite='Lax')
                    response.set_cookie('user_email', email, 
                                      httponly=False, secure=False, samesite='Lax')
                    response.set_cookie('user_type', 'admin', 
                                      httponly=False, secure=False, samesite='Lax')
                    return response
            
            # If we got here, credentials are invalid
            return jsonify({
                'success': False, 
                'message': 'Invalid email or password'
            })

        except Exception as e:
            return jsonify({
                'success': False, 
                'message': 'An error occurred during login',
                'error': str(e)
            })
        finally:
            if 'cur' in locals():
                cur.close()

    # Render login page for GET requests
    return render_template("Login.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        first_name = request.form['first_name']
        middle_name = request.form.get('middle_name', '')  
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        country = request.form['country']
        dob = request.form['dob']
        first_time_visitor = request.form.get('first_time_visitor', 'no')  # Default to 'no' if not provided
        passport_number = request.form['passport_number']

        print(request.form)
        # Hash the password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        print(hashed_password)
        # Convert "yes" or "no" to 1 or 0
        first_time_visitor_value = 1 if first_time_visitor.lower() == "yes" else 0

        # Validate Email Format
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            return jsonify({'success': False, 'message': 'Invalid email address'})

        try:
            cur = mysql.connection.cursor()

            # Check if email already exists
            cur.execute("SELECT id FROM tourists WHERE email = %s", (email,))
            if cur.fetchone():
                return jsonify({'success': False, 'message': 'Email already registered'})

            # Insert tourist with hashed password
            cur.execute("""
                INSERT INTO tourists (first_name, middle_name, last_name, email, password, 
                                    country, dob, first_time_visitor, passport_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (first_name, middle_name, last_name, email, hashed_password, 
                  country, dob, first_time_visitor_value, passport_number))

            # Get the auto-generated tourist_id
            tourist_id = cur.lastrowid

            mysql.connection.commit()
            cur.close()

            # Create response with redirect to profile
            response = make_response(jsonify({
                'success': True, 
                'message': 'Registration successful!', 
                'redirect': '/profile'
            }))
            
            # Set cookies with user data
            response.set_cookie('user_id', str(tourist_id), httponly=True)
            response.set_cookie('user_email', email, httponly=True)
            response.set_cookie('user_type', 'tourist', httponly=True)
            response.set_cookie('user_first_name', first_name, httponly=True)
            response.set_cookie('user_last_name', last_name, httponly=True)
            
            return response

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'success': False, 'message': str(e)})

    return render_template('register.html')

@app.route('/profile')
def profile():
    # Get all user info from cookies
    user_id = request.cookies.get('user_id')
    user_email = request.cookies.get('user_email')
    
    if not user_id or not user_email:
        return redirect('/login')

    try:
        cur = mysql.connection.cursor()
        # Get tourist data by ID AND email for extra security
        cur.execute("""
            SELECT id, first_name, middle_name, last_name, email, 
                   country, dob, first_time_visitor, passport_number 
            FROM tourists 
            WHERE id = %s AND email = %s
        """, (user_id, user_email))
        tourist = cur.fetchone()

        if tourist:
            tourist_data = {
                'id': tourist[0],
                'first_name': tourist[1],
                'middle_name': tourist[2],
                'last_name': tourist[3],
                'email': tourist[4],
                'country': tourist[5],
                'dob': tourist[6].strftime('%Y-%m-%d') if tourist[6] else '',
                'first_time_visitor': "yes" if tourist[7] == 1 else "no",
                'passport_number': tourist[8],
                'full_name': f"{tourist[1]} {tourist[3]}"
            }
            return render_template('profile.html', tourist=tourist_data)
        else:
            return redirect('/login')
    except Exception as e:
        print(f"Error fetching profile: {str(e)}")
        return redirect('/login')
    finally:
        if 'cur' in locals():
            cur.close()

@app.route('/edit/<int:id>', methods=['POST'])
def edit_tourist(id):
    try:
        # Get JSON data from request
        data = request.get_json()
        print("Received data:", data)  # Debug print
        
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400

        # Convert "yes" or "no" to 1 or 0
        first_time_visitor_value = 1 if data.get('first_time_visitor', '').lower() == "yes" else 0

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE tourists 
            SET first_name = %s, middle_name = %s, last_name = %s, 
                email = %s, country = %s, 
                dob = %s, first_time_visitor = %s, passport_number = %s
            WHERE id = %s
        """, (
            data.get('first_name'),
            data.get('middle_name'),
            data.get('last_name'),
            data.get('email'),
            data.get('country'),
            data.get('dob'),
            first_time_visitor_value,
            data.get('passport_number'),
            id
        ))
        mysql.connection.commit()
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()

            
@app.route('/delete/<int:id>', methods=['POST'])
def delete_tourist(id):
    try:
        cur = mysql.connection.cursor()
        
        # First check for bookings using tourist_id (the actual foreign key)
        cur.execute("SELECT COUNT(*) FROM booking WHERE tourist_id = %s", (id,))
        booking_count = cur.fetchone()[0]
        
        if booking_count > 0:
            # Option 1: Return error (current behavior)
            return jsonify({
                'success': False, 
                'message': 'Cannot delete account with active bookings. Please delete your bookings first.'
            }), 400
            
            # Option 2: Or you could automatically delete the bookings first
            # cur.execute("DELETE FROM Bookings WHERE tourist_id = %s", (id,))
            # mysql.connection.commit()
        
        # If no bookings (or after deleting them), proceed with tourist deletion
        cur.execute("DELETE FROM tourists WHERE id = %s", (id,))
        mysql.connection.commit()
        
        # Reset auto-increment if table is empty
        cur.execute("SELECT COUNT(*) FROM tourists")
        count = cur.fetchone()[0]
        if count == 0:
            cur.execute("ALTER TABLE tourists AUTO_INCREMENT = 1")
            mysql.connection.commit()
            
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cur.close()

@app.route('/get-bookings-by-tourist/<int:tourist_id>', methods=['GET'])
def get_bookings_by_tourist(tourist_id):
    try:
        cursor = mysql.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Bookings WHERE tourist_id = %s", (tourist_id,))
        bookings = cursor.fetchall()
        cursor.close()
        return jsonify({"success": True, "bookings": bookings})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/delete-bookings/<int:tourist_id>', methods=['DELETE'])
def delete_bookings(tourist_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM Bookings WHERE tourist_id = %s", (tourist_id,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({"success": True, "message": "All bookings deleted successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/add-supplier', methods=['POST'])
def add_supplier():
    try:
        name = request.form.get('name')
        category = request.form.get('type')  # your field naming
        sub_category = request.form.get('subcategory')
        location = request.form.get('location')
        email = request.form.get('email')
        description = request.form.get('description')
        price = request.form.get('price')
        times_json = request.form.get('times')  # JSON string of time slots

        # Handle image upload
        image_file = request.files.get('image')
        if image_file:
            # Make sure upload folder exists
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)

            # Secure filename (you can import secure_filename from werkzeug.utils)
            from werkzeug.utils import secure_filename
            filename = secure_filename(image_file.filename)

            # Save file
            image_path = os.path.join(upload_folder, filename)
            image_file.save(image_path)

            # Save relative path to DB (relative to static folder)
            db_image_path = f"static/uploads/{filename}"
        else:
            db_image_path = None

        # Insert supplier data to DB, example:
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO suppliers (name, category, sub_category, location, email, description, price, image)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, category, sub_category, location, email, description, price, db_image_path))
        supplier_id = cur.lastrowid
        mysql.connection.commit()

        # Insert times if any
        import json
        times = json.loads(times_json) if times_json else []
        for session in times:
            start = session.get('start')
            end = session.get('end')
            cur.execute("""
                INSERT INTO suppliersessiontime (supplier_id, start_time, end_time)
                VALUES (%s, %s, %s)
            """, (supplier_id, start, end))
        mysql.connection.commit()

        return jsonify({'message': 'Supplier added successfully', 'id': supplier_id}), 201
    except Exception as e:
        print("Error in add_supplier:", e)
        return jsonify({'error': str(e)}), 500


@app.route('/get-user-email/<int:tourist_id>', methods=['GET'])
def get_user_email(tourist_id):
    cur = None
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT email FROM tourists WHERE id = %s", (tourist_id,))
        result = cur.fetchone()
        if result:
            return jsonify({'success': True, 'email': result[0]})
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': 'Server error: ' + str(e)}), 500
    finally:
        if cur:
            cur.close()


@app.route('/check-bookings', methods=['GET'])
def check_bookings():
    try:
        tourist_id = request.args.get('tourist_id')
        if not tourist_id:
            return jsonify({'success': False, 'message': 'Tourist ID parameter is required'}), 400

        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) FROM booking WHERE tourist_id = %s and status = 'Pending'" , (tourist_id,))
        count = cur.fetchone()[0]
        return jsonify({'success': True, 'has_bookings': count > 0})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cur.close()


@app.route('/toublo', methods=['GET', 'POST'])  # ← Add this
def tour():

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            cur = mysql.connection.cursor()

            # Get user's hashed password
            cur.execute("SELECT id, password FROM tourists WHERE email = %s", (email,))
            user = cur.fetchone()
            cur.close()

            if user:
                user_id, stored_password = user
                # Verify hashed password
                if check_password_hash(stored_password, password):
                    return jsonify({
                        'success': True, 
                        'message': 'Login successful!', 
                        'redirect': '/'
                    })
            
            # If credentials are invalid
            return jsonify({
                'success': False, 
                'message': 'Invalid email or password'
            })

        except Exception as e:
            return jsonify({
                'success': False, 
                'message': 'An error occurred: ' + str(e)
            })

   
    # Render login page for GET requests
    return render_template('toublo.html')


@app.route("/cart")
def cart_page():
    return render_template("cart.html")

@app.route('/paymentmethod')
def payment_method():
    return render_template('PaymentMethod.html')

@app.route('/mypayment')
def mypay():
    try:
        # Fetch all payments from the database
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM payments ORDER BY date DESC")
        payments = cursor.fetchall()
        cursor.close()
        
        # Convert payments to a list of dictionaries
        payment_list = []
        for payment in payments:
            payment_list.append({
                'id': payment[0],
                'date': payment[1].strftime('%Y-%m-%d') if payment[1] else None,
                'passport_number': payment[2],
                'payment_method': payment[3],
                'name': payment[4],
                'status': payment[5],
                'amount': payment[6]
            })
        
        return render_template('MyPayment.html', payments=payment_list)
    except Exception as e:
        print(f"Error fetching payments: {str(e)}")
        return render_template('MyPayment.html', payments=[], error="Error loading payments")

@app.route('/paymenthistory')
def paymenthis():
    return render_template('PaymentHistory.html')

@app.route('/add')
def paymentadd():
    return render_template('AddCardDetails.html')


@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.json
    print(data)
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute('''
            INSERT INTO booking (
                tourist_id,
                supplier_id,
                booking_date,
                price,
                session_id,
                num_adults,
                num_children_1_5,
                num_children_6_11,
                status,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            data['tourist_id'],
            data['supplier_id'],
            data['booking_date'],
            data['price'],
            data['session_id'],
            data['num_adults'],
            data['num_children_1_5'],
            data['num_children_6_11'],
            data.get('status', 'pending'),
            datetime.now(timezone.utc).isoformat()
        ))

        print("Booking created successfully")
        mysql.connection.commit()
        booking_id = cursor.lastrowid
        return jsonify({'success': True, 'booking_id': booking_id})
    except Exception as e:
        print("Error in booking:", e)
        return jsonify({'success': False, 'message': 'Booking failed'}), 500


@app.route('/api/cards/<int:user_id>', methods=['GET'])
def get_cards(user_id):
    try:    
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM payment_cards where tourist_id = %s", (user_id,))
        cards = cursor.fetchall()
        cursor.close()
        card_list = []
        for card in cards:
            card_list.append({
                'id': card[0],
                'card_number': card[1],
                'cardholder_name': card[2],
                'expiry_date': card[3],
                'cvv': card[4],
                'card_type': card[5],
                'created_at': str(card[6])
            })
        
        return jsonify({"success": True, "cards": card_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
@app.route('/api/cards', methods=['POST'])
def add_card():
    try:
        data = request.json
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            INSERT INTO payment_cards (card_number, cardholder_name, expiry_date, cvv, card_type, tourist_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (data['card_number'], data['cardholder_name'], data['expiry_date'], 
              data['cvv'], data['card_type'], data['tourist_id']))
        print(data['tourist_id'])
        mysql.connection.commit()
        card_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({"success": True, "id": card_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/cards/<int:card_id>', methods=['PUT'])
def update_card(card_id):
    try:
        data = request.json
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            UPDATE payment_cards 
            SET card_number = %s, cardholder_name = %s, expiry_date = %s, 
                cvv = %s, card_type = %s
            WHERE id = %s
        """, (data['card_number'], data['cardholder_name'], data['expiry_date'],
              data['cvv'], data['card_type'], card_id))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/cards/<int:card_id>', methods=['DELETE'])
def delete_card(card_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM payment_cards WHERE id = %s", (card_id,))
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/explore')
def explore():
    return render_template('explore.html')

@app.route('/categories')
def categories():
    return render_template('categories.html')

@app.route('/wellness')
def wellness():
    return render_template('wellness.html')

@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    sub_category = request.args.get('subcategory')
    print(sub_category)
    cursor = mysql.connection.cursor()
    query = "SELECT id, name, email, category, sub_category, location, price, image, description FROM suppliers WHERE sub_category = %s"
    cursor.execute(query, (sub_category,))
    result = cursor.fetchall()
    print(result)
    # Column names
    columns = [desc[0] for desc in cursor.description]

    # Combine data with keys and add random rating
    vendors = []
    for row in result:
        vendor = dict(zip(columns, row))
        vendor['rating'] = random.randint(3, 5)
        vendors.append(vendor)
    cursor.close()
    return jsonify(vendors)

def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"

def get_period_from_time(start):
    try:
        start_hour = int(start.split(':')[0])
        if 6 <= start_hour < 12:
            return "Morning"
        elif 12 <= start_hour < 16:
            return "Afternoon"
        elif 16 <= start_hour < 21:
            return "Evening"
        else:
            return "Night"
    except Exception:
        return "Unknown"

@app.route('/api/available-times', methods=['POST'])
def get_available_times():
    data = request.get_json()
    supplier_name = data.get('supplier')
    date_str = data.get('date')  # format: YYYY-MM-DD

    if not supplier_name or not date_str:
        return jsonify({"error": "Missing supplier or date"}), 400

    try:
        cur = mysql.connection.cursor()
        # Get supplier ID
        cur.execute("SELECT id FROM suppliers WHERE name = %s", (supplier_name,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Supplier not found"}), 404
        supplier_id = row[0]

        # Get all session times (start_time and end_time as timedelta)
        cur.execute("SELECT id, start_time, end_time FROM suppliersessiontime WHERE supplier_id = %s", (supplier_id,))
        sessions = cur.fetchall()

        # Get booked sessions on the date
        cur.execute("SELECT session_id FROM booking WHERE supplier_id = %s AND booking_date = %s AND status = 'pending'", (supplier_id, date_str))
        booked_session_ids = {row[0] for row in cur.fetchall()}

        available_sessions = []
        for session in sessions:
            session_id, start_time, end_time = session

            # Skip if session is booked
            if session_id in booked_session_ids:
                continue

            # Convert timedelta to "HH:MM"
            start_str = format_timedelta(start_time)
            end_str = format_timedelta(end_time)

            # Determine time period
            period = get_period_from_time(start_str)

            available_sessions.append({
                "session_id": session_id,
                "start": start_str,
                "end": end_str,
                "period": period
            })

        return jsonify({"available_sessions": available_sessions})

    except Exception as e:
        print("Error in get_available_times:", e)
        return jsonify({"error": "Server error"}), 500
    finally:
        cur.close()

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

# Supplier Management Routes
@app.route('/supregister', methods=['GET', 'POST'])
def supregister():
    if request.method == 'GET':
        return render_template('supregister.html')
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            category = request.form['category']
            description = request.form['description']

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO suppliers (name, email, category, description)
                VALUES (%s, %s, %s, %s)
            """, (name, email, category, description))
            mysql.connection.commit()
            return redirect(url_for('suppliers'))
        except Exception as e:
            print(f"Error: {e}")
            return {"error": "Registration failed. Please try again."}, 500
        finally:
            cur.close()

@app.route('/suppliers')
def suppliers():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM suppliers")
        data = cur.fetchall()
        return render_template('suppliers.html', suppliers=data)
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}, 500
    finally:
        cur.close()


@app.route('/api/suppliers/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    cur = mysql.connection.cursor()
    try:
        # Get form data instead of JSON
        data = request.form

        required_fields = ['name', 'type', 'location', 'email']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        # Image handling
        image_file = request.files.get('image')
        image_filename = None
        if image_file:
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
            image_file.save(upload_path)
            image_filename =  "/static/uploads/" + filename  # Save this in the database

        update_query = """
            UPDATE suppliers 
            SET name = %s, email = %s, category = %s, sub_category = %s,
                location = %s, price = %s, description = %s {image_part}
            WHERE id = %s
        """
        image_part = ", image = %s" if image_filename else ""
        query = update_query.format(image_part=image_part)

        values = [
            data['name'],
            data['email'],
            data['type'],
            data.get('subcategory', ''),
            data['location'],
            data.get('price', 0),
            data.get('description', '')
        ]
        if image_filename:
            values.append(image_filename)
        values.append(supplier_id)

        cur.execute(query, tuple(values))
        mysql.connection.commit()

        cur.execute("DELETE FROM suppliersessiontime WHERE supplier_id = %s", (supplier_id,))
        session_times = request.form.get('times')
        if session_times:
            import json
            times = json.loads(session_times)
            for slot in times:
                cur.execute("""
                    INSERT INTO suppliersessiontime (supplier_id, start_time, end_time)
                    VALUES (%s, %s, %s)
                """, (supplier_id, slot['start'], slot['end']))
        mysql.connection.commit()

        cur.execute("SELECT * FROM suppliers WHERE id = %s", (supplier_id,))
        updated_supplier = cur.fetchone()

        return jsonify({
            'id': updated_supplier[0],
            'name': updated_supplier[1],
            'email': updated_supplier[2],
            'type': updated_supplier[3],
            'sub_category': updated_supplier[4],
            'location': updated_supplier[5],
            'price': updated_supplier[6],
            'image': updated_supplier[7],
            'description': updated_supplier[8]
        })

    except Exception as e:
        print(f"Error in update_supplier: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_supplier(id):
    cur = None  # Initialize to prevent UnboundLocalError
    try:
        if request.method == 'GET':
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM suppliers WHERE id = %s", (id,))
            supplier = cur.fetchone()
            if supplier:
                return render_template('edit_supplier.html', supplier=supplier)
            return redirect(url_for('suppliers'))

        if request.method == 'POST':
            # Fetch form data
            name = request.form.get('name')
            email = request.form.get('email')
            category = request.form.get('category')
            description = request.form.get('description')

            # Optional: Handle uploaded image
            image_file = request.files.get('image')
            if image_file and image_file.filename:
                image_path = f'static/uploads/{image_file.filename}'
                image_file.save(image_path)
                # You may also want to store image_path in DB

            # Update query
            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE suppliers 
                SET name = %s, email = %s, category = %s, description = %s
                WHERE id = %s
            """, (name, email, category, description, id))
            mysql.connection.commit()

            return redirect(url_for('suppliers'))

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}, 500

    finally:
        if cur:
            cur.close()
@app.route('/delete/<int:id>', methods=['POST'])
def delete_supplier(id):
    try:
        cur = mysql.connection.cursor()
        
        # First delete the supplier
        cur.execute("DELETE FROM suppliers WHERE id = %s", (id,))
        mysql.connection.commit()
        
        # Then reset auto-increment if table is empty
        cur.execute("SELECT COUNT(*) FROM suppliers")
        count = cur.fetchone()[0]
        if count == 0:
            cur.execute("ALTER TABLE suppliers AUTO_INCREMENT = 1")
            mysql.connection.commit()
            
        return '', 204
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}, 500
    finally:
        cur.close()

@app.route('/api/get-suppliers') 
def handle_suppliers():
    try:
        cur = mysql.connection.cursor()
        
        cur.execute("SELECT * FROM suppliers")
        suppliers = cur.fetchall()
        
        suppliers_list = []
        
        for supplier in suppliers:
            supplier_id = supplier[0]

            # Fetch session time slots
            cur.execute("SELECT start_time, end_time FROM suppliersessiontime WHERE supplier_id = %s", (supplier_id,))
            session_rows = cur.fetchall()
            sessions = []

            for row in session_rows:
                start = str(row[0])[:5]
                end = str(row[1])[:5]

                # Determine period based on start hour
                start_hour = int(start.split(':')[0])
                if 6 <= start_hour < 12:
                    period = "Morning"
                elif 12 <= start_hour < 17:
                    period = "Afternoon"
                elif 17 <= start_hour < 21:
                    period = "Evening"
                else:
                    period = "Night"

                sessions.append({
                    "start_time": start,
                    "end_time": end,
                    "period": period
                })

            suppliers_list.append({
                'id': supplier[0],
                'name': supplier[1],
                'email': supplier[2],
                'type': supplier[3],
                'sub_category': supplier[4],
                'location': supplier[5],
                'price': supplier[6],
                'image': supplier[7],
                'description': supplier[8],
                'times': sessions
            })
        return jsonify(suppliers_list)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

@app.route('/api/suppliers/<int:supplier_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_single_supplier(supplier_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM suppliers WHERE id = %s", (supplier_id,))
        supplier = cur.fetchone()
        cur.execute("SELECT start_time, end_time FROM suppliersessiontime WHERE supplier_id = %s", (supplier_id,))
        session_rows = cur.fetchall()   
        if not supplier:
            return jsonify({'error': 'Supplier not found'}), 404
        if request.method == 'GET':
            sessions = []
            for row in session_rows:
                start = str(row[0])[:5]
                end = str(row[1])[:5]

                # Categorize period
                start_hour = int(start.split(":")[0])
                if 6 <= start_hour < 12:
                    period = "Morning"
                elif 12 <= start_hour < 17:
                    period = "Afternoon"
                elif 17 <= start_hour < 21:
                    period = "Evening"
                else:
                    period = "Night"
                sessions.append({
                    "start_time": start,
                    "end_time": end,
                    "period": period
                    })
            return jsonify({
                'id': supplier[0],
                'image': supplier[7],
                'name': supplier[1],
                'email': supplier[2],
                'type': supplier[3],
                'sub_category': supplier[4],
                'location': supplier[5],
                'price': supplier[6],
                'times': sessions,  
                'description': supplier[8]
            })

        elif request.method == 'PUT':
            data = request.get_json()
            update_fields = []
            update_values = []
            print("data: ", data)
            if 'name' in data:
                update_fields.append("name = %s")
                update_values.append(data['name'])

            if 'email' in data:
                update_fields.append("email = %s")
                update_values.append(data['email'])

            if 'type' in data:  # corresponds to 'category' in DB
                update_fields.append("category = %s")
                update_values.append(data['type'])

            if 'sub_category' in data:
                update_fields.append("sub_category = %s")
                update_values.append(data['sub_category'])

            if 'location' in data:
                update_fields.append("location = %s")
                update_values.append(data['location'])

            if 'price' in data:
                update_fields.append("price = %s")
                update_values.append(data['price'])

            if 'description' in data:
                update_fields.append("description = %s")
                update_values.append(data['description'])

            if update_fields:
                update_query = "UPDATE suppliers SET " + ", ".join(update_fields) + " WHERE id = %s"
                update_values.append(supplier_id)
                cur.execute(update_query, tuple(update_values))
                mysql.connection.commit()

            # Optional: update session times
            if 'times' in data:
                cur.execute("DELETE FROM suppliersessiontime WHERE supplier_id = %s", (supplier_id,))
                for session in data['times']:
                    start_time = session['start']
                    end_time = session['end']
                    cur.execute("""
                        INSERT INTO suppliersessiontime (supplier_id, start_time, end_time)
                        VALUES (%s, %s, %s)
                    """, (supplier_id, start_time, end_time))
                mysql.connection.commit()

            # Fetch updated supplier and session times
            cur.execute("SELECT * FROM suppliers WHERE id = %s", (supplier_id,))
            updated_supplier = cur.fetchone()

            cur.execute("SELECT start_time, end_time FROM suppliersessiontime WHERE supplier_id = %s", (supplier_id,))
            updated_sessions = cur.fetchall()

            sessions = []
            for row in updated_sessions:
                start = row[0].strftime('%H:%M')
                end = row[1].strftime('%H:%M')
                start_hour = int(start.split(":")[0])
                if 6 <= start_hour < 12:
                    period = "Morning"
                elif 12 <= start_hour < 17:
                    period = "Afternoon"
                elif 17 <= start_hour < 21:
                    period = "Evening"
                else:
                    period = "Night"
                sessions.append({
                    "start_time": start,
                    "end_time": end,
                    "period": period
                })

            return jsonify({
                'id': updated_supplier[0],
                'image': updated_supplier[7],
                'name': updated_supplier[1],
                'email': updated_supplier[2],
                'type': updated_supplier[3],
                'sub_category': updated_supplier[4],
                'location': updated_supplier[5],
                'price': updated_supplier[6],
                'times': sessions,
                'description': updated_supplier[8]
            })



        elif request.method == 'DELETE':
            cur.execute("DELETE FROM suppliers WHERE id = %s", (supplier_id,))
            mysql.connection.commit()
            
            # Reset auto-increment if table is empty
            cur.execute("SELECT COUNT(*) FROM suppliers")
            count = cur.fetchone()[0]
            if count == 0:
                cur.execute("ALTER TABLE suppliers AUTO_INCREMENT = 1")
                mysql.connection.commit()
                
            return jsonify({'message': 'Supplier deleted successfully'}), 200
            
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

# PDF Generation Route
@app.route('/download-suppliers-pdf')
def download_suppliers_pdf():
    try:
        # Create cursor
        cur = mysql.connection.cursor()
        
        # Get all suppliers
        cur.execute("SELECT * FROM suppliers")
        suppliers_data = cur.fetchall()
        
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Set up the PDF
        pdf.set_font("Helvetica", size=12)
        
        # Add title
        pdf.cell(200, 10, txt="Ayubo Go - Supplier Details", new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.ln(10)
        
        # Table header with background color
        pdf.set_fill_color(40, 110, 65)  # Green background (#597E52)
        pdf.set_text_color(255, 255, 255)  # White text
        
        # Set column widths
        col_widths = [15, 40, 50, 35, 50]  # Adjusted widths
        
        # Create header row
        pdf.cell(col_widths[0], 10, "ID", 1, new_x="RIGHT", new_y="TOP", align='C', fill=True)
        pdf.cell(col_widths[1], 10, "Business Name", 1, new_x="RIGHT", new_y="TOP", align='C', fill=True)
        pdf.cell(col_widths[2], 10, "Email", 1, new_x="RIGHT", new_y="TOP", align='C', fill=True)
        pdf.cell(col_widths[3], 10, "Category", 1, new_x="LMARGIN", new_y="NEXT", align='C', fill=True)
        
        # Reset text color for data
        pdf.set_text_color(0, 0, 0)
        
        # Add data rows
        for idx, supplier in enumerate(suppliers_data, 1):
            pdf.cell(col_widths[0], 10, str(idx), 1, new_x="RIGHT", new_y="TOP", align='C')
            pdf.cell(col_widths[1], 10, supplier[1][:20], 1, new_x="RIGHT", new_y="TOP", align='L')  # Business name (limited)
            pdf.cell(col_widths[2], 10, supplier[2][:25], 1, new_x="RIGHT", new_y="TOP", align='L')  # Email (limited)
            pdf.cell(col_widths[3], 10, supplier[3][:15], 1, new_x="LMARGIN", new_y="NEXT", align='L')  # Category (limited)
            
            # Add description as a multi-cell on the next row
            pdf.set_font("Helvetica", size=10)  # Smaller font for description
            pdf.cell(15, 10, "", 0, new_x="RIGHT", new_y="TOP")  # Empty cell for alignment
            pdf.multi_cell(0, 10, f"Description: {supplier[4][:200]}...", 1, align='L')  # Description with limit
            pdf.set_font("Helvetica", size=12)  # Reset font size
            pdf.ln(5)  # Add some space between suppliers
        
        # Generate the PDF file
        pdf_path = "static/suppliers.pdf"
        pdf.output(pdf_path)
        
        # Return the PDF file
        return send_file(pdf_path, as_attachment=True)
    
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return {"error": str(e)}, 500
    finally:
        cur.close()

@app.route('/api/cards/<int:card_id>', methods=['GET'])
def get_card(card_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM payment_cards WHERE id = %s", (card_id,))
        card = cursor.fetchone()
        cursor.close()
        
        if card:
            card_data = {
                'id': card[0],
                'card_number': card[1],
                'cardholder_name': card[2],
                'expiry_date': card[3],
                'cvv': card[4],
                'card_type': card[5],
                'created_at': str(card[6])
            }
            return jsonify({"success": True, "card": card_data})
        else:
            return jsonify({"success": False, "error": "Card not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/payments', methods=['GET'])
def get_payments():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM payments ORDER BY date DESC")
        payments = cursor.fetchall()
        cursor.close()
        
        payment_list = []
        for payment in payments:
            payment_list.append({
                'id': payment[0],
                'date': payment[1].strftime('%Y-%m-%d') if payment[1] else None,
                'passport_number': payment[2],
                'payment_method': payment[3],
                'name': payment[4],
                'status': payment[5],
                'amount': payment[6]
            })
        
        return jsonify(payment_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments', methods=['POST'])
def add_payment():
    try:
        data = request.json
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            INSERT INTO payments (date, booking_id, payment_method, name, status, amount)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['date'],
            data['booking_id'],
            data['payment_method'],
            data['name'],
            data['status'],
            data['amount']
        ))
        
        mysql.connection.commit()
        cursor.close()
        return jsonify({'message': 'Payment added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments/<int:payment_id>', methods=['PUT'])
def update_payment(payment_id):
    try:
        data = request.json
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            UPDATE payments
            SET date = %s, passport_number = %s, payment_method = %s,
                name = %s, status = %s, amount = %s
            WHERE id = %s
        """, (
            data['date'],
            data['passport_number'],
            data['payment_method'],
            data['name'],
            data['status'],
            data['amount'],
            payment_id
        ))
        
        mysql.connection.commit()
        cursor.close()
        return jsonify({'message': 'Payment updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments/<int:payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM payments WHERE id = %s", (payment_id,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'message': 'Payment deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/get-supplier-id', methods=['POST'])
def get_supplier_id():
    data = request.get_json()
    supplier_name = data.get('name')
    print("Supplier name:", supplier_name)
    if not supplier_name:
        return jsonify({'error': 'Supplier name is required'}), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM suppliers WHERE name = %s", (supplier_name,))
        row = cur.fetchone()
        cur.close()
        print("Supplier ID:", row[0])
        if row:
            return jsonify({'supplier_id': row[0]})
        else:
            return jsonify({'error': 'Supplier not found'}), 404

    except Exception as e:
        print("Error in get_supplier_id:", e)
        return jsonify({'error': 'Server error'}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)