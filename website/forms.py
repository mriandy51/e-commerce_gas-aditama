from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, PasswordField, EmailField, SubmitField, SelectField
from wtforms.validators import DataRequired, length, NumberRange, Regexp, Optional  
from flask_wtf.file import FileField, FileRequired, FileAllowed

class SignUpForm(FlaskForm):
    full_name = StringField('Nama Lengkap', validators=[DataRequired()])
    username = StringField('Username', validators=[
        DataRequired(),
        length(min=6),
        Regexp(r'^[\w.]+$', message="Username hanya boleh berisi huruf, angka, titik dan underscore")
    ])
    email = EmailField('Email', validators=[DataRequired()])
    phone = StringField('Phone', validators=[
    DataRequired(),
    length(min=10, max=15, message="Nomor WhatsApp harus antara 10-15 digit"), 
    Regexp(r'^\d+$', message="Masukkan Nomor Whatsapp yang valid")
    ])
    password1 = PasswordField('Enter Your Password', validators=[DataRequired(), length(min=8)])
    password2 = PasswordField('Confirm Your Password', validators=[DataRequired(), length(min=8)])
    roles = SelectField('Role', 
                       choices=[
                           ('0', 'Regular User'), 
                           ('1', 'Super Admin'), 
                           ('2', 'Admin'),
                           ('3', 'Kasir'),
                           ('4', 'Staff Gudang')
                       ], 
                       validators=[Optional()])
    submit = SubmitField('Buat Akun')


class LoginForm(FlaskForm):
    login = StringField('Email or Username', validators=[DataRequired()])
    password = PasswordField('Enter Your Password', validators=[DataRequired()])
    submit = SubmitField('Log in')
    
class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired(), length(min=8)])
    new_password = PasswordField('New Password', validators=[DataRequired(), length(min=8)])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), length(min=8)])
    change_password = SubmitField('Submit')
    
class ProductForm(FlaskForm):
    product_name = StringField('Nama Produk', validators=[DataRequired()])
    product_picture = FileField('Gambar Produk', validators=[
        FileRequired()
    ])
    submit = SubmitField('Tambah Produk')

class ProductVariantForm(FlaskForm):
    variant_name = StringField('Nama Variant', validators=[DataRequired()])
    variant_type = SelectField('Tipe Variant', 
        choices=[
            ('refill', 'Isi Ulang'),
            ('tabung_kosong', 'Tabung Kosong'),
            ('tabung_bocor', 'Tabung Bocor')
        ],
        validators=[DataRequired()]
    )
    price = IntegerField('Harga', validators=[
        Optional(),  
        NumberRange(min=0, message="Harga tidak boleh negatif")
    ])
    stock = IntegerField('Stok', validators=[
        Optional(), 
        NumberRange(min=0, message="Stok tidak boleh negatif")
    ])
    submit = SubmitField('Tambah Variant')

class UpdateProductForm(FlaskForm):
    product_name = StringField('Nama Produk', validators=[DataRequired()])
    product_picture = FileField('Gambar Produk', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Hanya file gambar!')
    ])
    submit = SubmitField('Update Produk')

class UpdateVariantForm(FlaskForm):
    variant_name = StringField('Nama Variant', validators=[DataRequired()])
    variant_type = SelectField('Tipe Variant', 
        choices=[
            ('default', 'default'),
            ('refill', 'Isi Ulang'),
            ('tabung_kosong', 'Tabung Kosong'),
            ('tabung_bocor', 'Tabung Bocor')
        ],
        validators=[DataRequired()]
    )
    price = IntegerField('Harga', validators=[DataRequired()])
    stock = IntegerField('Stok', validators=[DataRequired()])
    submit = SubmitField('Update Variant')
    

class ShopItemsForm(FlaskForm):
    product_name = StringField('Name of Product', validators=[Optional()])
    current_price = FloatField('Current Price', validators=[Optional()])
    in_stock = IntegerField('In Stock', validators=[Optional()])
    product_picture = FileField('Product Picture', validators=[Optional()])
    add_product = SubmitField('Add Product')
    update_product = SubmitField('Update')

    
class DeliveryTruck(FlaskForm):
    delivery_status = SelectField('Delivery Status', 
                                choices=[('Belum Datang', 'Belum Datang'), 
                                        ('Sudah Datang', 'Sudah Datang')],
                                validators=[DataRequired()])
    estimated_delivery = StringField('Estimated Delivery', validators=[DataRequired()])
    notification_message = StringField('Notification Message', validators=[DataRequired()])
    update_truck = SubmitField()
    
class ComplaintForm(FlaskForm):
    guest_name = StringField(validators=[DataRequired()])
    title = StringField(validators=[DataRequired()])
    whatsapp = StringField(validators=[
        DataRequired(),
        length(min=10, max=15, message="Nomor WhatsApp harus antara 10-15 digit"),
        Regexp(r'^08\d+$', message="Nomor WhatsApp harus diawali dengan 08 dan hanya berisi angka")
    ])
    complaint_content = StringField(validators=[DataRequired()])    
    status = SelectField('Status', choices=[('Belum Ditangani', 'Belum Ditangani'), ('Dalam Penanganan', 'Dalam Penanganan'), ('Selesai', 'Selesai')], default='Belum Ditangani')
    add_complaint = SubmitField('Kirim')
    
class NewOrderForm(FlaskForm):
    user_id = IntegerField('User ID', validators=[DataRequired()])
    product_id = IntegerField('Product ID', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Belum Bayar', 'Belum Bayar'), ('Belum Diambil', 'Belum Diambil'), ('Lunas', 'Lunas'), ('Selesai', 'Selesai')], validators=[DataRequired()])
    submit = SubmitField('Create Order')

class AddOrderForm(FlaskForm):
    customer_id = SelectField('User', coerce=int, validators=[DataRequired()])
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add Order')