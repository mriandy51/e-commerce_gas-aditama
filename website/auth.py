from flask import Blueprint, render_template, flash, redirect
from .forms import LoginForm, SignUpForm, PasswordChangeForm
from .models import User
from . import db
from flask_login import login_user, login_required, logout_user


auth = Blueprint('auth', __name__)


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        full_name = form.full_name.data
        phone = form.phone.data
        password1 = form.password1.data
        password2 = form.password2.data
        
        # Validasi nomor WhatsApp
        if not phone.startswith('08'):
            flash('Nomor WhatsApp harus diawali dengan 08')
            return redirect('/sign-up')
            
        # Cek email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email sudah terdaftar')
            return redirect('/sign-up')
            
        # Cek username
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash('Username sudah terdaftar')
            return redirect('/sign-up')
            
        # Cek phone
        existing_phone = User.query.filter_by(phone=phone).first()
        if existing_phone:
            flash('Whatsapp telepon sudah terdaftar')
            return redirect('/sign-up')

        if password1 == password2:
            new_customer = User()
            new_customer.email = email
            new_customer.username = username
            new_customer.full_name = full_name
            new_customer.phone = phone
            new_customer.password = password2

            try:
                db.session.add(new_customer)
                db.session.commit()
                flash('Akun berhasil dibuat, silahkan login')
                return redirect('/login')
            except Exception as e:
                print(e)
                flash('Gagal membuat akun')
        else:
            flash('Password tidak sama')

    return render_template('signup.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        login_input = form.login.data
        password = form.password.data

        user = User.query.filter(
            (User.email == login_input) | (User.username == login_input)
        ).first()

        if user:
            if user.verify_password(password=password):
                login_user(user)
                if user.roles in [1, 2]:  
                    return redirect('/dashuser')
                elif user.roles == 3: 
                    return redirect('/dashorders')
                elif user.roles == 4: 
                    return redirect('/dashproduct')
                else:  
                    return redirect('/')
            else:
                flash('Password salah')
        else:
            flash('Akun tidak ada, silahkan buat akun!')

    return render_template('login.html', form=form)


@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def log_out():
    logout_user()
    return redirect('/')

@auth.route('/profile/<int:customer_id>')
@login_required
def profile(customer_id):
    user = User.query.get(customer_id)
    return render_template('profile.html', user=user)

@auth.route('/change-password/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def change_password(customer_id):
    form = PasswordChangeForm()
    user = User.query.get(customer_id)
    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data
        confirm_new_password = form.confirm_new_password.data

        if user.verify_password(current_password):
            if new_password == confirm_new_password:
                user.password = confirm_new_password
                db.session.commit()
                flash('Password berhasil diperbarui')
                return redirect(f'/profile/{user.id}')
            else:
                flash('Password baru tidak sama !!')

        else:
            flash('Password saat ini salah')

    return render_template('change_password.html', form=form)
