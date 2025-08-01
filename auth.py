import dotenv
dotenv.load_dotenv()
import os
import random
import pyotp
import qrcode
import io
from flask import Blueprint, render_template, redirect, url_for, request, session, g, flash, send_file
from forms import LoginForm, SignUpForm
from access_control import login_required
from authlib.integrations.flask_client import OAuth
import db
from utils import mail, executor, limiter, send_email, oauth, google
from config import Config

auth = Blueprint('auth', __name__)
limiter.limit("1/second")(auth)


def generate_pin(length=6):
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

def clear_flash_messages():
    session.pop('_flashes', None)

@auth.route('/signUp', methods=['GET', 'POST'])
@limiter.limit("5/hour;10/day", methods=["POST"])
def sign_up():
    if request.method == 'GET':
        clear_flash_messages()  
    
    form = SignUpForm(request.form)
    if request.method == 'POST':
        if not form.validate():
            clear_flash_messages()
            for field, errors in form.errors.items():
                field_name = field.replace('_', ' ').title()
                flash(f"{field_name}: {errors[0]}", 'danger')
                break
            return render_template('sign_up.html', form=form)
        
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data
        role = form.role.data

       
        hashed_password = db.hashed_pw(password)

        if role == "elderly":
            user_role = 1
        elif role == "volunteer":
            user_role = 2
        else:
            clear_flash_messages()
            flash("Invalid role selected.", "danger")
            return render_template('sign_up.html', form=form)

        if db.insert_user(first_name, last_name, email, hashed_password, user_role):
            clear_flash_messages()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            clear_flash_messages()
            flash('Error creating account. Please try again.', 'danger')
            return render_template('sign_up.html', form=form)
        
    return render_template('sign_up.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("1/hour", methods=["POST"], deduct_when=lambda response: g.get("login_success", False))
def login():
    if request.method == 'GET':
        clear_flash_messages()  
    
    form = LoginForm(request.form)
    if request.method == 'POST':
        clear_flash_messages()
        
        if not form.validate():
            flash('Please check your email and password and try again.', 'danger')
            return render_template('login.html', form=form)
        
        email = form.email.data
        password = form.password.data
        user = db.verify_user(email, password)
        
        if not user:
            flash('Invalid email or password.', 'danger')
            return render_template('login.html', form=form)
        
        session['user_id'] = user['user_id']
        session['email'] = user['email']
        session['role'] = user['user_role']
        g.login_success = True
        
        if user.get('mfa_enabled'):
            return redirect(url_for('auth.login_mfa'))
        
        if user['user_role'] == 3:
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin.home'))
        else:
            flash('Logged in successfully!', 'success')
            return redirect(url_for('explore_groups'))
    
    return render_template('login.html', form=form)

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('.login'))

@auth.route('/forgetPassword', methods=['GET', 'POST'])
@limiter.limit("3/minute;10/day", methods=["POST"])
def forget_password():
    if request.method == 'GET':
        pass
        # clear_flash_messages()
    
    if request.method == 'POST':
        email = request.form.get('email')
        # clear_flash_messages()
        
        if not email:
            flash('Email is required.', 'danger')
            return render_template('forget_password.html')
        
        user = db.get_user_by_email(email)
        if user:
            pin = generate_pin()
            session['reset_email'] = email
            session['reset_pin'] = pin
            send_email.submit(
                recipient=email,
                subject="Your Social Sage Password Reset PIN",
                body=f"Your password reset PIN is: {pin}\nIf you did not request this, please change your password immediately and contact us"
            )
        flash('A PIN has been sent to your email if it exists. Please enter it below.', 'info')
        return redirect(url_for('.enter_pin'))
    
    return render_template('forget_password.html')

@auth.route('/enterPin', methods=['GET', 'POST'])
@limiter.limit("5/hour;10/day", methods=["POST"])
def enter_pin():
    if request.method == 'GET':
        clear_flash_messages()
        pass
    
    if 'reset_email' not in session or 'reset_pin' not in session:
         clear_flash_messages()
         flash('Invalid session. Please restart the password reset process.', 'danger')
         return redirect(url_for('.forget_password'))
    
    if request.method == 'POST':
        clear_flash_messages()
        entered_pin = request.form.get('pin')
        
        if not entered_pin:
            flash('PIN is required.', 'danger')
            return render_template('enter_pin.html')
        
        if entered_pin == session.get('reset_pin') and "reset_email" in session:
            flash('PIN verified. Please enter a new password.', 'success')
            return redirect(url_for('.change_password'))
        else:
            flash('Incorrect PIN. Please try again.', 'danger')
    
    return render_template('enter_pin.html')

@auth.route('/resendPin', methods=['POST'])
def resend_pin():
    clear_flash_messages()
    
    if 'reset_email' not in session:
        flash('Invalid session. Please restart the password reset process.', 'danger')
        return redirect(url_for('forget_password'))
    
    email = session['reset_email']
    pin = generate_pin()
    
    try:
        send_email(
            recipient=email,
            subject="Your Social Sage Password Reset PIN (Resent)",
            body=f"Your new password reset PIN is: {pin}\nThis PIN will expire in 10 minutes.\nIf you did not request this, please ignore."
        )
        flash('A new PIN has been sent to your email.', 'info')
    except Exception as e:
        flash('Error sending email. Please try again.', 'danger')
    
    return redirect(url_for('enter_pin'))

@auth.route('/changePassword', methods=['GET', 'POST'])
def change_password():
    if request.method == 'GET':
        clear_flash_messages()
    
    if 'reset_email' not in session or 'reset_pin' not in session:
        clear_flash_messages()
        flash('Invalid session. Please restart the password reset process.', 'danger')
        return redirect(url_for('forget_password'))
    
    if request.method == 'POST':
        clear_flash_messages()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('Both password fields are required.', 'danger')
            return render_template('change_password.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('change_password.html')
        
        from forms import validate_password_strength
        from wtforms import PasswordField, Form
        
        class TempForm(Form):
            pass
        
        temp_form = TempForm()
        password_field = PasswordField()
        password_field.data = password
        
        try:
            validate_password_strength(temp_form, password_field)
        except Exception as e:
            flash(str(e), 'danger')
            return render_template('change_password.html')
        
        hashed = db.hashed_pw(password)
        if db.update_user_password(session['reset_email'], hashed):
            flash('Your password has been changed successfully!', 'success')
            session.pop('reset_email', None)
            session.pop('reset_pin', None)
            session.pop('pin_expiry', None)
            return redirect(url_for('login'))
        else:
            flash('Error updating password. Please try again.', 'danger')
    
    return render_template('change_password.html')

@auth.route('/login/google')
def login_google():
    clear_flash_messages()
    redirect_uri = url_for('.login_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@auth.route('/login/callback')
def login_google_callback():
    clear_flash_messages()
    try:
        token = google.authorize_access_token()
        user_info = google.userinfo()
        email = user_info.get('email')

        if not email:
            flash('Google did not return your email address. Please ensure you have granted permission to share your email.', 'danger')
            return redirect(url_for('.login'))

        user = db.get_user_by_email(email)

        if not user:
            if db.insert_user(
                user_info.get("given_name", ""), 
                user_info.get("family_name", ""), 
                email, 
                '',
                None
            ):
                user = db.get_user_by_email(email)
            else:
                flash('Error creating account with Google. Please try again.', 'danger')
                return redirect(url_for('.login'))

        if not user:
            flash('Error logging in with Google. Please try again.', 'danger')
            return redirect(url_for('.login'))

        session['user_id'] = user['user_id']
        session['email'] = email
        session['role'] = user['user_role']

        if not user['user_role']:
            return redirect(url_for('choose_role'))

        return redirect(url_for('explore_groups'))
    
    except Exception as e:
        flash('Error during Google authentication. Please try again.', 'danger')
        return redirect(url_for('.login'))

@auth.route('/chooseRole', methods=['GET', 'POST'])
def choose_role():
    if request.method == 'GET':
        clear_flash_messages()
    
    user_id = session.get('user_id')
    if request.method == 'POST':
        clear_flash_messages()
        role = request.form.get('role')
        
        if role not in ['1', '2']:
            flash('Invalid role selected.', 'danger')
            return render_template('choose_role.html')
        
        if db.update_user_role(user_id, role):
            session['role'] = int(role)
            flash('Role selected successfully!', 'success')
            return redirect(url_for('explore_groups'))
        else:
            flash('Error updating role. Please try again.', 'danger')
    
    return render_template('choose_role.html')


@auth.route('/loginMfa', methods=['GET', 'POST'])
def login_mfa():
    if request.method == 'GET':
        clear_flash_messages()
    
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('.login'))
    
    if request.method == 'POST':
        clear_flash_messages()
        code = request.form.get('code')
        
        if not code:
            flash('MFA code is required.', 'danger')
            return render_template('login_mfa.html')
        
        secret = db.get_user_mfa_secret(user_id)
        if not secret:
            flash('MFA not properly configured. Please contact support.', 'danger')
            return redirect(url_for('.login'))
        
        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            flash('Logged in with MFA!', 'success')
            return redirect(url_for('explore_groups'))
        else:
            flash('Invalid MFA code.', 'danger')
    
    return render_template('login_mfa.html')

@auth.route('/mfaQrCode')
@login_required
def mfa_qr_code():
    user_id = session['user_id']
    user_email = session['email']
    secret = db.get_user_mfa_secret(user_id)
    if not secret:
        secret = pyotp.random_base32()
        db.update_user_mfa_secret(user_id, secret)
    mfa_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user_email, issuer_name="Social Sage")
    img = qrcode.make(mfa_uri)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@auth.route('/setupMfa', methods=['GET', 'POST'])
@login_required
def setup_mfa():
    user_id = session['user_id']
    user_email = session['email']

    secret = db.get_user_mfa_secret(user_id)
    if not secret:
        secret = pyotp.random_base32()
        db.update_user_mfa_secret(user_id, secret)

    if request.method == 'POST':
        code = request.form.get('code')
        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            db.enable_user_mfa(user_id)
            flash('MFA enabled successfully!', 'success')
            return redirect(url_for('user_profile'))
        else:
            flash('Invalid code, please try again.', 'danger')

    return render_template('verify_mfa.html') 

@auth.route('/toggleMfa', methods=['POST'])
@login_required
def toggle_mfa():
    user_id = session['user_id']
    
    # Get current MFA status from DB
    is_mfa_enabled = db.is_user_mfa_enabled(user_id)
    
    if is_mfa_enabled:
        db.disable_user_mfa(user_id)
        flash('MFA disabled.', 'info')
    else:
        secret = db.get_user_mfa_secret(user_id)
        if not secret:
            return redirect(url_for('.setup_mfa'))
        db.enable_user_mfa(user_id)
        flash('MFA enabled.', 'success')
    
    return redirect(url_for('user_profile'))
