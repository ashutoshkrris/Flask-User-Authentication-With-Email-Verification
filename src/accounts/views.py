from datetime import datetime
from flask import render_template, url_for, \
    redirect, flash, request, Blueprint
from flask_login import login_user, logout_user, \
    login_required


from src.accounts.models import User
from src import db, bcrypt
from src.accounts.token import confirm_token, generate_token
from src.email import send_email
from .forms import LoginForm, RegisterForm


accounts_bp = Blueprint('accounts', __name__)


@accounts_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            password=form.password.data
        )
        db.session.add(user)
        db.session.commit()
        token = generate_token(user.email)
        confirm_url = url_for('accounts.confirm_email',
                              token=token, _external=True)
        html = render_template('accounts/confirm_email.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(user.email, subject, html)

        login_user(user)
        flash('A confirmation email has been sent via email.', 'success')

        return redirect(url_for('core.home'))

    return render_template('accounts/register.html', form=form)


@accounts_bp.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except Exception:
        flash('The confirmation link is invalid or has expired.', 'danger')
    user = User.query.filter_by(email=email).first_or_404()

    if user.is_active:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.is_active = True
        user.activated_on = datetime.now()
        db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('core.home'))


@accounts_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(
                user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('core.home'))
        else:
            flash('Invalid email and/or password.', 'danger')
            return render_template('accounts/login.html', form=form)
    return render_template('accounts/login.html', form=form)


@accounts_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You were logged out.', 'success')
    return redirect(url_for('accounts.login'))
