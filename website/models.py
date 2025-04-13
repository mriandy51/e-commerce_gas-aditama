from . import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

def wib_time():
    return datetime.utcnow() + timedelta(hours=7)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(15), unique=True)
    username = db.Column(db.String(50), unique=True)  
    full_name = db.Column(db.String(100))  
    password_hash = db.Column(db.String(150))
    date_joined = db.Column(db.DateTime(), default=wib_time)
    roles = db.Column(db.Integer, default=0)
    
    
    cart_items = db.relationship('Cart', backref=db.backref('user', lazy=True))
    orders = db.relationship('Order', backref=db.backref('user', lazy=True))

    @property
    def password(self):
        raise AttributeError('Password is not a readable Attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password=password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password=password)

    def __str__(self):
        return '<User %r>' % User.id


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    product_picture = db.Column(db.String(1000), nullable=False)
    date_added = db.Column(db.DateTime, default=wib_time)
    is_active = db.Column(db.Boolean, default=True) 

    variants = db.relationship('ProductVariant', backref='main_product', lazy=True, cascade='all, delete-orphan')

    def __str__(self):
        return f'<Product {self.product_name}>'

class ProductVariant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    variant_name = db.Column(db.String(100), nullable=False)
    variant_type = db.Column(db.String(20), nullable=False)  
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    date_added = db.Column(db.DateTime, default=wib_time)
    is_active = db.Column(db.Boolean, default=True)

    carts = db.relationship('Cart', backref=db.backref('variant', lazy=True))
    detail_orders = db.relationship('DetailOrder', backref=db.backref('variant', lazy=True))

    def __str__(self):
        return f'<ProductVariant {self.variant_name}>'


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    customer_link = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=False)

    def __str__(self):
        return f'<Cart {self.id}>'

class Order(db.Model):
    id = db.Column(db.String(100), primary_key=True)  
    customer_link = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=True)
    customer_phone = db.Column(db.String(15), nullable=True)
    is_offline = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(100), nullable=False)
    date_added = db.Column(db.DateTime, default=wib_time)
    completed_at = db.Column(db.DateTime, nullable=True)
    total = db.Column(db.Integer, nullable=False)
    snap_token = db.Column(db.String(100))
    
    details = db.relationship('DetailOrder', backref='order')
    
    @property
    def total_quantity(self):
        return sum(detail.quantity for detail in self.details)

    def __str__(self):
        return f'<Order {self.order_id}>'
    
class DetailOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(100), db.ForeignKey('order.id'), nullable=False)  
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    sub_total = db.Column(db.Integer, nullable=False)
    can_return = db.Column(db.Boolean, default=True)
    returned_quantity = db.Column(db.Integer, default=0)

    def __str__(self):
        return f'<DetailOrder {self.id}>'
    
class ReturnOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_detail_id = db.Column(db.Integer, db.ForeignKey('detail_order.id'), nullable=False)
    reason = db.Column(db.String(1000), nullable=False)
    return_category = db.Column(db.String(50), nullable=False) 
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Dalam Proses')
    date_requested = db.Column(db.DateTime, default=wib_time)
    
    order_detail = db.relationship('DetailOrder', backref='return_request')

    def __str__(self):
        return f'<ReturnOrder {self.id}>'

    
class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    whatsapp = db.Column(db.String(15), nullable=False) 
    complaint_content = db.Column(db.String(1000), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    date_added = db.Column(db.DateTime, default=wib_time)

    def __str__(self):
        return '<Complaint %r>' % self.title

class GasTruck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    delivery_status = db.Column(db.String(100), nullable=False)
    estimated_delivery = db.Column(db.String(100), nullable=False)
    notification_message = db.Column(db.String(1000), default='None')
    updated_at = db.Column(db.DateTime, default=wib_time)

    def __str__(self):
        return '<GasTruck %r>' % self.id
