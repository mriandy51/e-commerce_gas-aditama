from datetime import datetime, timedelta
from flask import Blueprint, render_template, flash, redirect, request, jsonify, url_for
from math import ceil
from website.midtrans import create_midtrans_transaction
from .models import Product, Cart, Order, DetailOrder, ProductVariant, ReturnOrder
from flask_login import login_required, current_user
from . import db
import uuid

views = Blueprint('views', __name__)
""""
API_TOKEN='ISSecretKey_test_fea315c1-9b97-437e-8fdc-b4725ed83b39'
API_PUBLISABHLE_KEY = 'ISPubKey_test_8701266f-8a66-408e-abc6-04e5047dbc92'"""

@views.route('/')
def home():
    items = Product.query.order_by(Product.date_added).all()
    return render_template('index.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                           if current_user.is_authenticated else [])

@views.route('/add-to-cart/<int:variant_id>')
@login_required
def add_to_cart(variant_id):
    variant_to_add = ProductVariant.query.get(variant_id)

    if variant_to_add is None or variant_to_add.stock <= 0:
        flash('Stok barang habis')
        return redirect(request.referrer)

    item_exists = Cart.query.filter_by(variant_id=variant_id, customer_link=current_user.id).first()
    
    if item_exists:
        if item_exists.quantity + 1 > variant_to_add.stock:
            flash(f'Tidak dapat menambahkan barang lebih dari stok ({variant_to_add.stock})!')
            return redirect(request.referrer)
        
        try:
            item_exists.quantity += 1
            db.session.commit()
            flash(f'Jumlah {variant_to_add.variant_name} pada keranjang diperbarui')
            return redirect(request.referrer)
        except Exception as e:
            print('Quantity not Updated', e)
            flash(f'Gagal menambah {variant_to_add.variant_name} ke keranjang')
            return redirect(request.referrer)

    new_cart_item = Cart()
    new_cart_item.quantity = 1
    new_cart_item.variant_id = variant_to_add.id
    new_cart_item.customer_link = current_user.id

    try:
        db.session.add(new_cart_item)
        db.session.commit()
        flash(f'{variant_to_add.variant_name} ditambah ke keranjang')
    except Exception as e:
        print('Gagal menambah barang ke keranjang', e)
        flash(f'{variant_to_add.variant_name} Gagal ditambah ke keranjang')

    return redirect(request.referrer)

@views.route('/cart')
@login_required
def show_cart():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = 0
    for item in cart:
        amount += item.variant.price * item.quantity

    return render_template('cart.html', cart=cart, amount=amount, total=amount)

@views.route('/pluscart')
@login_required
def plus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        variant = ProductVariant.query.get(cart_item.variant_id)

        if cart_item.quantity + 1 > variant.stock:
            flash(f'Tidak dapat menambah barang lebih dari stok ({variant.stock})!')
            return redirect('/cart')

        cart_item.quantity += 1
        db.session.commit()

    return redirect('/cart')

@views.route('/minuscart')
@login_required
def minus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        variant = ProductVariant.query.get(cart_item.variant_id)

        if cart_item.quantity > variant.stock:
            cart_item.quantity = variant.stock 

        if cart_item.quantity > 1:  
            cart_item.quantity -= 1
            db.session.commit()
        else:
            db.session.delete(cart_item) 
            db.session.commit()

    return redirect('/cart')

@views.route('removecart')
@login_required
def remove_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()

        return redirect('/cart')
    

@views.route('/place-order')
@login_required
def place_order():
    customer_cart = Cart.query.filter_by(customer_link=current_user.id).all()
    if customer_cart:
        try:
            total = sum(item.variant.price * item.quantity for item in customer_cart)

            for item in customer_cart:
                variant = item.variant
                if variant.stock < item.quantity:
                    flash(f'Tidak dapat memesan {variant.variant_name}. Hanya {variant.stock} yang tersisa.')
                    return redirect('/cart')

            new_order = Order(
                id=str(uuid.uuid4()),  
                customer_link=current_user.id,
                customer_name=current_user.full_name,
                status='Bayar Sekarang',
                total=total
            )
            db.session.add(new_order)

            # Create order details and update stock
            for item in customer_cart:
                detail_order = DetailOrder(
                    order_id=new_order.id,
                    variant_id=item.variant_id,
                    quantity=item.quantity,
                    price=item.variant.price,
                    sub_total=item.variant.price * item.quantity
                )
                db.session.add(detail_order)

                variant = item.variant
                variant.stock -= item.quantity

                if variant.variant_type == 'refill':
                    empty_tank_variant = ProductVariant.query.filter_by(
                        product_id=variant.product_id,
                        variant_type='tabung_kosong'
                    ).first()
                    if empty_tank_variant:
                        empty_tank_variant.stock += item.quantity

                db.session.delete(item)

            db.session.commit()

            customer_details = {
                "first_name": current_user.username,
                "email": current_user.email,
            }

            snap_token = create_midtrans_transaction(new_order.id, total, customer_details)
            Order.query.filter_by(id=new_order.id).update(dict(snap_token=snap_token))
            db.session.commit()

            return render_template('payment.html', snap_token=snap_token)

        except Exception as e:
            db.session.rollback()
            print(e)
            flash('Pesanan gagal dibuat')
            return redirect('/')

    else:
        flash('Keranjang anda kosong')
        return redirect('/')

@views.route('/retry-payment/<order_id>', methods=['GET'])
@login_required
def retry_payment(order_id):
    order = Order.query.filter_by(id=order_id, customer_link=current_user.id).first()

    if not order:
        flash('Pesanan tidak ditemukan atau Anda tidak memiliki akses.')
        return redirect('/orders')

    if order.status != 'Bayar Sekarang':
        flash('Pesanan ini tidak dapat dibayar ulang.')
        return redirect('/orders')

    if order.snap_token:
        return render_template('payment.html', snap_token=order.snap_token)
    else:
        flash('Token pembayaran tidak tersedia.')
        return redirect('/orders')

@views.route('/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    per_page = 3
    
    orders_data = (Order.query
        .filter_by(customer_link=current_user.id)
        .order_by(Order.date_added.desc())
        .paginate(page=page, per_page=per_page, error_out=False))
    
    today = datetime.utcnow() + timedelta(hours=7)
    
    # Kalkulasi batas waktu pengembalian
    for order in orders_data.items:
        for detail in order.details:
            detail.can_return = (
                order.status == 'Selesai' and
                order.completed_at and
                (today - order.completed_at) <= timedelta(hours=1) and
                detail.variant.variant_type != 'tabung_kosong' and
                detail.quantity > detail.returned_quantity
            )
            if order.completed_at:
                detail.return_deadline = (order.completed_at + timedelta(hours=1)).strftime('%d %B %Y, %H:%M')
    
    return render_template('orders.html', 
                         orders=orders_data.items,
                         ReturnOrder=ReturnOrder,  
                         pagination={
                             'page': page,
                             'total_pages': orders_data.pages,
                             'has_prev': orders_data.has_prev,
                             'has_next': orders_data.has_next,
                             'prev_page': page - 1 if page > 1 else None,
                             'next_page': page + 1 if page < orders_data.pages else None,
                         },
                         today=today)


@views.route('/request-return/<int:detail_id>', methods=['POST'])
@login_required
def request_return(detail_id):
    detail_order = DetailOrder.query.get_or_404(detail_id)
    order = Order.query.get(detail_order.order_id)
    
    if order.status != 'Selesai' or detail_order.variant.variant_type == 'tabung_kosong':
        flash('Pengembalian barang hanya bisa diajukan kalau pesanan selesai dan bukan untuk tabung kosong')
        return redirect(url_for('views.orders'))
    
    if not order.completed_at:
        flash('Waktu selesai pesanan tidak valid')
        return redirect(url_for('views.orders'))
    
    today_wib = datetime.utcnow() + timedelta(hours=7)
    time_since_completed = today_wib - order.completed_at
    
    if time_since_completed > timedelta(hours=1):
        flash('Pengembalian barang hanya bisa dilakukan dalam 1 jam setelah pesanan selesai!')
        return redirect(url_for('views.orders'))
    
        
    reason = request.form.get('reason')
    return_quantity = int(request.form.get('quantity', 1))
    
    if not reason:
        flash('Mohon isi alasan pengembalian')
        return redirect(url_for('views.orders'))
        
    available_quantity = detail_order.quantity - detail_order.returned_quantity
    if return_quantity <= 0 or return_quantity > available_quantity:
        flash(f'Jumlah tidak sesuai. Anda dapat mengembalikan {available_quantity} barang.')
        return redirect(url_for('views.orders'))
    
    new_return = ReturnOrder(
        order_detail_id=detail_id,
        reason=reason,
        return_category='tabung_bocor',
        quantity=return_quantity,
        status='Dalam Proses'
    )
    
    detail_order.returned_quantity += return_quantity
    if detail_order.returned_quantity >= detail_order.quantity:
        detail_order.can_return = False
    
    try:
        db.session.add(new_return)
        db.session.commit()
        flash('Pengembalian barang berhasil diajukan')
        return redirect('/orders')

    except Exception as e:
        db.session.rollback()
        flash('Gagal mengajukan pengembalian barang')
        
    return redirect(url_for('views.orders'))



@views.route('/midtrans-notification', methods=['POST'])
def midtrans_notification():
    data = request.get_json()
    order_id = data['order_id']
    transaction_status = data['transaction_status']

    order = Order.query.filter_by(id=order_id).first()
    if order:
        if transaction_status == 'settlement':
            order.status = 'Dalam Proses'
        elif transaction_status == 'pending':
            order.status = 'Bayar Sekarang'
        elif transaction_status in ['expire', 'cancel', 'deny', 'failure']:
            if order.status != 'Gagal':
                order.status = 'Gagal'
                # Return seluruh stok item
                order_details = DetailOrder.query.filter_by(order_id=order.id).all()
                for detail in order_details:
                    variant = detail.variant
                    variant.stock += detail.quantity
                    if variant.variant_type == 'refill':
                        empty_tank_variant = ProductVariant.query.filter_by(
                            product_id=variant.product_id,
                            variant_type='tabung_kosong'
                        ).first()
                        if empty_tank_variant:
                            empty_tank_variant.stock -= detail.quantity
                        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error updating order status: {e}")
            return jsonify({'status': 'error'}), 500

    return jsonify({'status': 'success'})

@views.route('/return-history')
@login_required
def return_history():
    page = request.args.get('page', 1, type=int)
    per_page = 3 
    
    returns_pagination = (ReturnOrder.query
        .join(DetailOrder)
        .join(Order)
        .filter(Order.customer_link == current_user.id)
        .order_by(ReturnOrder.date_requested.desc())
        .paginate(page=page, per_page=per_page, error_out=False))
    
    return render_template('return_history.html', 
                         returns=returns_pagination.items,
                         pagination={
                             'page': page,
                             'total_pages': returns_pagination.pages,
                             'has_prev': returns_pagination.has_prev,
                             'has_next': returns_pagination.has_next,
                             'prev_page': page - 1 if page > 1 else None,
                             'next_page': page + 1 if page < returns_pagination.pages else None,
                         })
    