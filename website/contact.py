from datetime import datetime
from flask import Blueprint, flash, render_template, redirect, url_for
from .forms import  ComplaintForm
from .models import Complaint
from . import db
contact = Blueprint('contact', __name__)


@contact.route('/contact', methods=['GET', 'POST'])
def add_complaint():
    form = ComplaintForm()
    if form.validate_on_submit():
        whatsapp = form.whatsapp.data
        
        # Validasi nomor WhatsApp
        if not whatsapp.startswith('08'):
            flash('Nomor WhatsApp harus diawali dengan 08')
            return redirect(url_for('contact.add_complaint'))
            
        if not (10 <= len(whatsapp) <= 15):
            flash('Nomor WhatsApp harus antara 10-15 digit')
            return redirect(url_for('contact.add_complaint'))

        new_complaint = Complaint(
            guest_name=form.guest_name.data,
            title=form.title.data,
            whatsapp=whatsapp,
            complaint_content=form.complaint_content.data,
            status=form.status.data,
            date_added=datetime.utcnow()
        )
        try:
            db.session.add(new_complaint)
            db.session.commit()
            flash('Pesan berhasil dikirim')
            return redirect(url_for('contact.add_complaint'))
        except Exception as e:
            print(e)
            flash('Pesan gagal terkirim, silahkan hubungi secara langsung melalui Whatsapp!')


    return render_template('contact.html', form=form)