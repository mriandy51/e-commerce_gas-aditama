from datetime import datetime, timedelta
from flask import Blueprint, jsonify, render_template, flash, request, send_from_directory, redirect, url_for
from flask_login import login_required, current_user
import requests
from werkzeug.utils import secure_filename
import os, uuid
from .forms import ProductForm, ProductVariantForm, DeliveryTruck, SignUpForm, ComplaintForm
from .models import Cart, Product, GasTruck, Complaint, Order, ProductVariant, User, DetailOrder, ReturnOrder
from . import db
from math import ceil

admin = Blueprint('admin', __name__)

@admin.route('/media/<path:filename>')
def get_image(filename):
    return send_from_directory('../media', filename)

def allowed_file(filename):
    allowed_extensions = {'jpg', 'jpeg', 'png'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

@admin.route('/dashproduct', methods=['GET', 'POST'])
@login_required
def manage_shop_items():
    if current_user.roles != 0 and current_user.roles != 3:
        product_form = ProductForm()
        variant_form = ProductVariantForm()
        
        if product_form.validate_on_submit():
            try:
                # Handle file upload
                file = product_form.product_picture.data
                filename = secure_filename(file.filename)
                
                allowed_extensions = {'jpg', 'jpeg', 'png'}
                if not '.' in filename or \
                   filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                    flash('Format file tidak diizinkan. Gunakan JPG, JPEG, atau PNG')
                    return redirect(url_for('admin.manage_shop_items'))
                
                # Validasi tipe MIME
                if not file.content_type.startswith('image/'):
                    flash('File harus berupa gambar')
                    return redirect(url_for('admin.manage_shop_items'))
                
                file_path = f'./media/{filename}'
                file.save(file_path)

                # Create new product
                new_product = Product(
                    product_name=product_form.product_name.data,
                    product_picture=file_path
                )
                
                db.session.add(new_product)
                db.session.commit()
                
                flash(f'Produk {new_product.product_name} berhasil ditambahkan')
                return redirect(url_for('admin.manage_shop_items'))
                
            except Exception as e:
                print(e)
                flash('Gagal menambahkan produk!')
                return redirect(url_for('admin.manage_shop_items'))

        # Get all products with their variants
        products = Product.query.order_by(Product.date_added.desc()).all()
        
        return render_template(
            'dashproduct.html',
            product_form=product_form,
            variant_form=variant_form,
            products=products
        )
    else:
        return render_template('404.html')

@admin.route('/add-variant/<int:product_id>', methods=['POST'])
@login_required
def add_variant(product_id):
    if current_user.roles != 0 and current_user.roles != 3:
        form = ProductVariantForm()
        if form.validate_on_submit():
            try:
                existing_variant = ProductVariant.query.filter_by(
                    product_id=product_id,
                    variant_type=form.variant_type.data
                ).first()
                
                if existing_variant:
                    flash(f'Variant dengan tipe {form.variant_type.data} sudah ada untuk produk ini')
                    return redirect(url_for('admin.manage_shop_items'))
                
                if form.price.data < 0 or form.stock.data < 0:
                    flash('Harga dan stok tidak boleh negatif')
                    return redirect(url_for('admin.manage_shop_items'))
                    
                new_variant = ProductVariant(
                    product_id=product_id,
                    variant_name=form.variant_name.data,
                    variant_type=form.variant_type.data,
                    price=form.price.data,
                    stock=form.stock.data
                )
                
                db.session.add(new_variant)
                db.session.commit()
                
                flash(f'Variant {new_variant.variant_name} berhasil ditambahkan')
            except Exception as e:
                print(e)
                flash('Gagal menambahkan variant!')
                
        return redirect(url_for('admin.manage_shop_items'))
    else:
        return render_template('404.html')
    
@admin.route('/get-product/<int:product_id>')
@login_required
def get_product(product_id):
    if current_user.roles != 0 and current_user.roles != 3:
        product = Product.query.get_or_404(product_id)
        return jsonify({
            'product_name': product.product_name,
            'product_picture': product.product_picture
        })
    return render_template('404.html')

@admin.route('/get-variant/<int:variant_id>')
@login_required
def get_variant(variant_id):
    if current_user.roles != 0 and current_user.roles != 3:
        variant = ProductVariant.query.get_or_404(variant_id)
        return jsonify({
            'variant_name': variant.variant_name,
            'variant_type': variant.variant_type,
            'price': variant.price,
            'stock': variant.stock
        })
    return render_template('404.html')

@admin.route('/update-product/<int:product_id>', methods=['POST'])
@login_required
def update_product(product_id):
    if current_user.roles != 0 and current_user.roles != 3:
        try:
            product = Product.query.get_or_404(product_id)
            product.product_name = request.form.get('product_name')

            if 'product_picture' in request.files:
                file = request.files['product_picture']
                if file and file.filename:
                    if not allowed_file(file.filename):
                        flash('Format file tidak diizinkan. Gunakan JPG, JPEG, atau PNG')
                        return redirect(url_for('admin.manage_shop_items'))
                        
                    # Validasi tipe MIME
                    if not file.content_type.startswith('image/'):
                        flash('File harus berupa gambar')
                        return redirect(url_for('admin.manage_shop_items'))
                        
                    filename = secure_filename(file.filename)
                    file_path = f'./media/{filename}'
                    file.save(file_path)
                    product.product_picture = file_path

            db.session.commit()
            flash('Produk berhasil diupdate')
        except Exception as e:
            print(e)
            flash('Gagal mengupdate produk')

        return redirect(url_for('admin.manage_shop_items'))
    return render_template('404.html')

@admin.route('/update-variant/<int:variant_id>', methods=['POST'])
@login_required
def update_variant(variant_id):
    if current_user.roles != 0 and current_user.roles != 3:
        try:
            variant = ProductVariant.query.get_or_404(variant_id)
            price = request.form.get('price', type=int)
            # stock = request.form.get('stock', type=int)
            
            #if price < 0 or stock < 0:
             #   flash('Harga dan stok tidak boleh negatif')
              #  return redirect(url_for('admin.manage_shop_items'))
            if price < 0 :
                flash('Harga tidak boleh negatif')
                return redirect(url_for('admin.manage_shop_items'))
                
            variant.variant_name = request.form.get('variant_name')
            variant.variant_type = request.form.get('variant_type')
            variant.price = price
           # variant.stock = stock

            db.session.commit()
            flash('Variant berhasil diupdate')
        except Exception as e:
            print(e)
            flash('Gagal mengupdate variant')

        return redirect(url_for('admin.manage_shop_items'))
    return render_template('404.html')



@admin.route('/delete-product/<int:product_id>')
@login_required
def delete_product(product_id):
    if current_user.roles != 0 and current_user.roles != 3:
        try:
            product = Product.query.get_or_404(product_id)
            image_path = product.product_picture  
            
            db.session.delete(product)
            db.session.commit()
            
            if os.path.exists(image_path):
                os.remove(image_path)
                
            flash('Produk berhasil dihapus')
            
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting product: {e}")
            flash('Tidak bisa menghapus produk karena sudah terkait dengan transaksi')

        return redirect(url_for('admin.manage_shop_items'))
    return render_template('404.html')

@admin.route('/delete-variant/<int:variant_id>')
@login_required
def delete_variant(variant_id):
    if current_user.roles != 0 and current_user.roles != 3:
        try:
            variant = ProductVariant.query.get_or_404(variant_id)
            product = variant.main_product

            db.session.delete(variant)
            db.session.commit()
            flash('Variant berhasil dihapus')
        except Exception as e:
            print(e)
            flash(f'Tidak boleh menghapus variant karena berkaitan dengan pesanan')

        return redirect(url_for('admin.manage_shop_items'))
    return render_template('404.html')

@admin.route('/subtract-stock/<int:variant_id>', methods=['POST'])
@login_required
def subtract_stock(variant_id):
    if current_user.roles == 0 and current_user.roles == 3:
        return render_template('404.html')
        
    try:
        variant = ProductVariant.query.get_or_404(variant_id)
        quantity = int(request.form.get('quantity', 0))
        
        if quantity <= 0 or quantity > variant.stock:
            flash(f'Jumlah tidak valid. Maksimal {variant.stock}')
            return redirect(url_for('admin.manage_shop_items'))
            
        variant.stock -= quantity
        db.session.commit()
        
        flash(f'Berhasil mengurangi {quantity} stok {variant.variant_name}')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error reducing stock: {e}")
        flash('Gagal mengurangi stok')
        
    return redirect(url_for('admin.manage_shop_items'))

@admin.route('/toggle-product-status/<int:product_id>')
@login_required
def toggle_product_status(product_id):
    if current_user.roles != 0 and current_user.roles != 3:
        try:
            product = Product.query.get_or_404(product_id)
            product.is_active = not product.is_active
            
            # Jika produk dinonaktifkan, nonaktifkan semua variant
            if not product.is_active:
                for variant in product.variants:
                    variant.is_active = False
                    
                # Hapus item dari cart jika ada
                cart_items = Cart.query.join(ProductVariant).filter(
                    ProductVariant.product_id == product_id
                ).all()
                for item in cart_items:
                    db.session.delete(item)
            
            db.session.commit()
            flash(f'Status produk berhasil {"dinonaktifkan" if not product.is_active else "diaktifkan"}')
        except Exception as e:
            db.session.rollback()
            print(e)
            flash('Gagal mengubah status produk')
            
        return redirect(url_for('admin.manage_shop_items'))
    return render_template('404.html')

@admin.route('/toggle-variant-status/<int:variant_id>')
@login_required
def toggle_variant_status(variant_id):
    if current_user.roles != 0 and current_user.roles != 3:
        try:
            variant = ProductVariant.query.get_or_404(variant_id)
            variant.is_active = not variant.is_active
            
            if not variant.is_active:
                # Hapus item dari cart jika ada
                Cart.query.filter_by(variant_id=variant_id).delete()
            
            db.session.commit()
            flash(f'Status variant berhasil {"dinonaktifkan" if not variant.is_active else "diaktifkan"}')
        except Exception as e:
            db.session.rollback()
            print(e)
            flash('Gagal mengubah status variant')
            
        return redirect(url_for('admin.manage_shop_items'))
    return render_template('404.html')

def send_push_notification(title, message):
    """Send a push notification using OneSignal's REST API."""
    ONESIGNAL_APP_ID = "1ab40228-4ab8-47b5-9052-33d6b0cc42e8"
    REST_API_KEY = "os_v2_app_dk2aekckxbd3lecsgpllbtcc5dcfoej7qkcug2vjt3jgi2cm4jd47i6wohmusrbfhqaqy4gmwz5xqxy5javj5pbnqfxzw3im3vfzeva"

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {REST_API_KEY}",
    }

    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "headings": {"en": title},  
        "contents": {"en": message}, 
        "included_segments": ["All"],  
    }

    response = requests.post(
        "https://onesignal.com/api/v1/notifications",
        headers=headers,
        json=payload,
    )

    print("Push Notification Response:", response.json())
    return response.json()



@admin.route('/add-refill-stock/<int:variant_id>', methods=['POST'])
@login_required
def add_refill_stock(variant_id):
    if current_user.roles == 0 and current_user.roles == 3:
        return render_template('404.html')
        
    try:
        refill_variant = ProductVariant.query.get_or_404(variant_id)
        if refill_variant.variant_type != 'refill':
            flash('Variant ini bukan tipe refill')
            return redirect(url_for('admin.manage_shop_items'))
            
        empty_variant = ProductVariant.query.filter_by(
            product_id=refill_variant.product_id,
            variant_type='tabung_kosong'
        ).first()
        
        if not empty_variant:
            flash('Variant tabung kosong tidak ditemukan')
            return redirect(url_for('admin.manage_shop_items'))
            
        quantity = int(request.form.get('quantity', 0))
        
        if quantity <= 0:
            flash('Jumlah harus lebih dari 0')
            return redirect(url_for('admin.manage_shop_items'))
            
        if quantity > empty_variant.stock:
            flash(f'Stok tabung kosong tidak cukup. Tersedia: {empty_variant.stock}')
            return redirect(url_for('admin.manage_shop_items'))
            
        refill_variant.stock += quantity
        empty_variant.stock -= quantity
        
        db.session.commit()
        flash(f'Berhasil menambah {quantity} stok {refill_variant.variant_name}')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding refill stock: {e}")
        flash('Gagal menambah stok')
        
    return redirect(url_for('admin.manage_shop_items'))

@admin.route('/send-product-notification', methods=['POST'])
@login_required
def send_product_notification():
    if current_user.roles not in [1, 2, 4]:  
        return render_template('404.html')
        
    try:
        product_id = request.form.get('product_id')
        message = request.form.get('notification_message')
        
        if not product_id or not message:
            flash('Product dan pesan notifikasi harus diisi')
            return redirect('/dashproduct')
            
        product = Product.query.get_or_404(product_id)
        title = f"Info Stok {product.product_name}"
            
        send_push_notification(title, message)
        flash('Notifikasi berhasil dikirim')
        
    except Exception as e:
        print(e)
        flash('Gagal mengirim notifikasi')
        
    return redirect('/dashproduct')

@admin.route('/add-empty-tank-stock/<int:variant_id>', methods=['POST'])
@login_required
def add_empty_tank_stock(variant_id):
    if current_user.roles == 0 and current_user.roles == 3:
        return render_template('404.html')
        
    try:
        empty_variant = ProductVariant.query.get_or_404(variant_id)
        
        if empty_variant.variant_type != 'tabung_kosong':
            flash('Variant ini bukan tipe tabung kosong')
            return redirect(url_for('admin.manage_shop_items'))
            
        quantity = int(request.form.get('quantity', 0))
        
        if quantity <= 0:
            flash('Jumlah harus lebih dari 0')
            return redirect(url_for('admin.manage_shop_items'))
            
        empty_variant.stock += quantity
        
        db.session.commit()
        flash(f'Berhasil menambah {quantity} stok {empty_variant.variant_name}')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error adding empty tank stock: {e}")
        flash('Gagal menambah stok')
        
    return redirect(url_for('admin.manage_shop_items'))


@admin.route('/dashorders', methods=['GET', 'POST'])
@login_required
def manage_orders():
    if current_user.roles !=0 and current_user.roles!=4:
        per_page = 10
        page = request.args.get('page', 1, type=int)
    
        query = Order.query.order_by(Order.date_added.desc())

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')
        
        customer_type = request.args.get('customer_type', '')
        if customer_type:
            if customer_type == "offline":
                query = query.filter_by(is_offline=True)
            elif customer_type == "online":
                query = query.filter_by(is_offline=False)

            
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%d/%m/%Y')
            end_date = datetime.strptime(end_date, '%d/%m/%Y')
            end_date = end_date + timedelta(days=1)
            query = query.filter(Order.date_added >= start_date, Order.date_added <= end_date)

        if status:
            query = query.filter(Order.status == status)
            
        # Search  name
        search = request.args.get('search')
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Order.customer_name.ilike(search_term)                
                    )
            )

        # Menghitung total revenue selain item dikembalikan
        total_revenue = 0
        for order in query.filter_by(status='Selesai'):
            order_total = 0
            for detail in order.details:
                return_request = ReturnOrder.query.filter_by(
                    order_detail_id=detail.id, 
                    status='Selesai'
                ).first()
                
                if not return_request:
                    order_total += detail.sub_total
            total_revenue += order_total
            
        total_awal_test = 0
        for order in query.filter_by(status='Selesai'):
            order_total = 0
            for detail in order.details:
                return_request = ReturnOrder.query.filter_by(
                    order_detail_id=detail.id, 
                    status='Selesai'
                ).first()
                
                order_total += detail.sub_total
            total_awal_test += order_total

        total_items = query.count()
        total_pages = ceil(total_items / per_page)
        page = min(page, total_pages) if total_pages > 0 else 1
        items = query.paginate(page=page, per_page=per_page, error_out=False)

        for order in items.items:
            order_total = 0
            for detail in order.details:
                return_request = ReturnOrder.query.filter_by(
                    order_detail_id=detail.id, 
                    status='Selesai'
                ).first()
                
                if not return_request:
                    order_total += detail.sub_total
            order.adjusted_total = order_total  
            
        customers = User.query.order_by(User.username).all()
        products = Product.query.order_by(Product.product_name).all()
        
        return render_template('dashorder.html', 
                            items=items, 
                            total_revenue=total_revenue,
                            customers=customers,
                            total_awal_test=total_awal_test,
                            products=products)
    else:
        return render_template('404.html')


@admin.route('/get-variants/<int:product_id>')
@login_required
def get_variants(product_id):
    if current_user.roles != 0 and current_user.roles != 4:
        variants = ProductVariant.query.filter(
            ProductVariant.product_id==product_id,
            ProductVariant.variant_type!='tabung_bocor'
            ).all()
        return jsonify([{
            'id': v.id,
            'variant_name': v.variant_name,
            'variant_type': v.variant_type,
            'price': v.price,
            'stock': v.stock
        } for v in variants])
    return render_template('404.html')

@admin.route('/add-order', methods=['POST'])
@login_required
def add_order():
    if current_user.roles != 0 and current_user.roles != 4:
        try:
            is_offline = 'is_offline' in request.form
            variant_id = request.form.get('variant_id')
            quantity = int(request.form.get('quantity'))
            
            variant = ProductVariant.query.get_or_404(variant_id)
            customer_id = request.form.get('customer_id')
            customer = User.query.get(customer_id)

            # Chek stockd
            if variant.stock < quantity:
                flash(f'Stok tidak cukup. Hanya tersedia {variant.stock}.')
                return redirect(url_for('admin.manage_orders'))
                
            total = variant.price * quantity
            
            new_order = Order(
                id=str(uuid.uuid4()),
                customer_link=customer_id if not is_offline else 55555,
                customer_name=customer.full_name if not is_offline else '-',
                status='Selesai',  
                total=total,
                is_offline=is_offline,
                completed_at=datetime.utcnow() + timedelta(hours=7)  
            )

            if is_offline:
                new_order.customer_name = request.form.get('customer_name', 'Walk-in Customer')
                new_order.customer_phone = request.form.get('customer_phone', '-')
            
            db.session.add(new_order)
            db.session.flush()  
            
            detail_order = DetailOrder(
                order_id=new_order.id,
                variant_id=variant_id,
                quantity=quantity,
                price=variant.price,
                sub_total=total
            )
            db.session.add(detail_order)
            
            variant.stock -= quantity
            
            # If tabung isi, add stok tabung kosong
            if variant.variant_type == 'refill':
                empty_tank_variant = ProductVariant.query.filter_by(
                    product_id=variant.product_id,
                    variant_type='tabung_kosong'
                ).first()
                if empty_tank_variant:
                    empty_tank_variant.stock += quantity
            
            db.session.commit()
            flash('Pesanan berhasil dibuat')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error membuat pesanan: {str(e)}')
            
        return redirect(url_for('admin.manage_orders'))
    return render_template('404.html')
    
@admin.route('/delete-order/<int:order_id>', methods=['POST'])
@login_required
def delete_order(order_id):
    if current_user.roles != 0 and current_user.roles!=4:
        try:
            order = Order.query.get_or_404(order_id)
            
            DetailOrder.query.filter_by(order_id=order.id).delete()
            
            for detail in order.details:
                ReturnOrder.query.filter_by(order_detail_id=detail.id).delete()
            
            db.session.delete(order)
            db.session.commit()
            flash('Pesanan berhasil dihapus')
            
        except Exception as e:
            db.session.rollback()
            print('Error deleting order:', e)
            flash('Gagal menghapus pesanan')
            
        return redirect(url_for('admin.manage_orders'))
    else:
        return render_template('404.html')
    
@admin.route('/order-details/<order_id>', methods=['GET'])
@login_required
def show_order_details(order_id):
    if current_user.roles != 0 and current_user.roles != 4:
        order = Order.query.get_or_404(order_id)
        if order:
            details = []
            for detail in order.details:
                # Hitung total pengembalian untuk detail order yg dipilih
                total_returns = 0
                return_value = 0
                for return_request in detail.return_request:
                    if return_request.status == 'Selesai':
                        total_returns += return_request.quantity
                        return_value += return_request.quantity * detail.price
                
                details.append({
                    'product_name': detail.variant.main_product.product_name,
                    'variant_name': detail.variant.variant_name, 
                    'quantity': detail.quantity,
                    'price': detail.price,
                    'sub_total': detail.sub_total,
                    'returned_quantity': total_returns,
                    'return_value': return_value,
                    'is_returned': total_returns > 0
                })

            response_data = {
                'id': order.id,
                'customer_name': order.customer_name if order.is_offline else order.user.full_name,
                'date': order.date_added.strftime('%d %B %Y, %H:%M'),
                'items': details,
                'total': sum(item['sub_total'] - item['return_value'] for item in details)
            }
            
            return jsonify(response_data)
        
        return jsonify({'error': 'Order not found'}), 404
    
    return render_template('404.html')

@admin.route('/update-order-status/<order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if current_user.roles != 0 and current_user.roles!=4:
        new_status = request.form.get('new_status')
        order_to_update = Order.query.get(order_id)  
        
        if order_to_update:
            
            for detail in order_to_update.details:
                if detail.return_request:
                    flash('Tidak dapat mengubah status pesanan karena sudah ada pengajuan pengembalian barang')
                    return redirect(url_for('admin.manage_orders'))
            
            old_status = order_to_update.status
            order_to_update.status = new_status
            
            if new_status == 'Selesai':
                order_to_update.completed_at = datetime.utcnow() + timedelta(hours=7)
            
            try:
                # If status diganti ke 'Gagal'
                if new_status == 'Gagal' and old_status != 'Gagal':
                    order_to_update.completed_at = None
                    order_details = DetailOrder.query.filter_by(order_id=order_to_update.id).all()
                    for detail in order_details:
                        variant = detail.variant
                        if variant:
                            variant.stock += detail.quantity
                            # If tabung isi, decrease tabung kosnong stok
                            if variant.variant_type == 'refill':
                                empty_tank_variant = ProductVariant.query.filter_by(
                                    product_id=variant.product_id,
                                    variant_type='tabung_kosong'
                                ).first()
                                if empty_tank_variant:
                                    empty_tank_variant.stock -= detail.quantity
                            
                # If status diganti dari 'Gagal' ke yg lain
                elif old_status == 'Gagal' and new_status != 'Gagal':
                    order_details = DetailOrder.query.filter_by(order_id=order_to_update.id).all()
                    for detail in order_details:
                        variant = detail.variant
                        if variant and variant.stock >= detail.quantity:
                            variant.stock -= detail.quantity
                            if variant.variant_type == 'refill':
                                empty_tank_variant = ProductVariant.query.filter_by(
                                    product_id=variant.product_id,
                                    variant_type='tabung_kosong'
                                ).first()
                                if empty_tank_variant:
                                    empty_tank_variant.stock += detail.quantity
                        else:
                            db.session.rollback()
                            flash('Stok tidak mencukupi untuk mengubah status pesanan')
                            return redirect(url_for('admin.manage_orders'))
                
                db.session.commit()
                flash('Status pesanan berhasil diperbarui')
                
            except Exception as e:
                db.session.rollback()
                print(f"Error updating order status: {e}")
                flash('Status pesanan gagal diperbarui')
        else:
            flash('Pesanan tidak ditemukan')
            
    return redirect(url_for('admin.manage_orders'))

@admin.route('/dashtruck', methods=['GET', 'POST'])
@login_required
def update_gas_truck():
    if current_user.roles != 0 and current_user.roles!=3:
        # current_truck = GasTruck.query.first()
        current_truck = GasTruck.query.order_by(GasTruck.id.desc()).first()
        history = GasTruck.query.order_by(GasTruck.updated_at.desc()).limit(5)
        form = DeliveryTruck()
        
        if form.validate_on_submit():
            try:
                history_record = GasTruck(
                    delivery_status=form.delivery_status.data,
                    estimated_delivery=form.estimated_delivery.data,
                    notification_message=form.notification_message.data
                )
                db.session.add(history_record)
                
                send_push_notification(
                    'Info Pengiriman LPG 3 kg',
                    form.notification_message.data
                )
                
                db.session.commit()
                flash('Status truk berhasil diperbarui')
                    
                return redirect('/dashtruck')
                
            except Exception as e:
                print('Status not Updated', e)
                flash('Gagal memperbarui status truk')

        return render_template('dashgastruck.html', 
                            form=form, 
                            current_truck=current_truck,
                            history=history)
    return render_template('404.html')
    

@admin.route('/dashcomplaint', methods=['GET', 'POST'])
@login_required
def manage_complaint():
    if current_user.roles != 0 and current_user.roles!=4:
        form = ComplaintForm()
        query = Complaint.query
        
        page = request.args.get('page', 1, type=int)
        per_page = 10
        query = Complaint.query
        
        # Filter date
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%d/%m/%Y')
            end_date = datetime.strptime(end_date, '%d/%m/%Y') + timedelta(days=1)
            query = query.filter(Complaint.date_added >= start_date, Complaint.date_added < end_date)
        
        # Filter  status
        status = request.args.get('status')
        if status:
            query = query.filter(Complaint.status == status)
        
        # Filter search
        search = request.args.get('search')
        if search:
            tetot = f"%{search}%"
            query = query.filter(
                db.or_(
                    Complaint.guest_name.ilike(tetot)                
                    )
            )
            
        search_title = request.args.get('search_title')
        if search_title:
            search_term = f"%{search_title}%"
            query = query.filter(
                db.or_(
                    Complaint.title.ilike(search_term)                
                    )
            )
        # Get all complaints with filters
        items = query.order_by(Complaint.date_added.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        
        return render_template('dashcomplaint.html', 
                             items=items, 
                             form=form,
                             selected_status=status,
                             start_date=start_date,
                             end_date=end_date)
    return render_template('404.html')

@admin.route('/update-complaint-status/<int:id>', methods=['POST'])
@login_required
def update_complaint_status(id):
    if current_user.roles != 0 and current_user.roles!=4:
        new_status = request.form.get('new_status')
        Complaint_to_update = Complaint.query.get(id)
        if Complaint_to_update:
            Complaint_to_update.status = new_status
            try:
                db.session.commit()
                flash('Status keluhan diperbarui.')
            except Exception as e:
                db.session.rollback()
                flash('Gagal memperbarui status keluhan.')
        else:
            flash('Keluhan tidak ditemukan.')
    else:
        flash('Unauthorized access.')
    return redirect(url_for('admin.manage_complaint'))

@admin.route('/delete-complaint/<int:complaintID>', methods=['POST'])
@login_required
def delete_complaint(complaintID):
    if current_user.roles != 0 and current_user.roles!=4 and current_user.roles!=3:
        try:
            complaint_to_delete = Complaint.query.get(complaintID)
            if complaint_to_delete:
                db.session.delete(complaint_to_delete)
                db.session.commit()
                flash('Complaint berhasil dihapus')
            else:
                flash('ID Complain tidak ditemukan')
        except Exception as e:
            print('User not deleted:', e)
            flash('Gagal menghapus complaint')
            
        return redirect(url_for('admin.manage_complaint'))
    return render_template('404.html')


@admin.route('/dashuser', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.roles == 0 or current_user.roles == 4 or current_user.roles == 3:
        return render_template('404.html')
        
    page = request.args.get('page', 1, type=int)
    per_page = 10
    query = User.query
    
    # Filter date
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date and end_date:
        start_date_obj = datetime.strptime(start_date, '%d/%m/%Y')
        end_date_obj = datetime.strptime(end_date, '%d/%m/%Y') + timedelta(days=1)
        query = query.filter(User.date_joined >= start_date_obj, User.date_joined < end_date_obj)
    
    # Filter role
    role = request.args.get('role')
    if role:
        query = query.filter(User.roles == role)
    
    # Filter name
    search = request.args.get('search')
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                User.username.ilike(search_term),
                User.full_name.ilike(search_term)
            )
        )
    
    users = query.order_by(User.date_joined).paginate(page=page, per_page=per_page, error_out=False)
    form = SignUpForm() 
     
    if current_user.roles == 2:  
        form.roles.choices = [('0', 'Pelanggan'), ('2', 'Admin'), ('3', 'Kasir'), ('4', 'Staff Gudang')]
    
    if form.validate_on_submit():
        try:
            print("Form submitted:", form.data)

            if User.query.filter_by(email=form.email.data).first():
                flash('Email sudah terdaftar')
                return redirect(url_for('admin.manage_users'))
                  
            if User.query.filter_by(username=form.username.data).first():
                flash('Username sudah terdaftar')
                return redirect(url_for('admin.manage_users'))
                
            if User.query.filter_by(phone=form.phone.data).first():
                flash('Nomor telepon sudah terdaftar')
                return redirect(url_for('admin.manage_users'))
            
            if not form.phone.data.startswith('08'):
                flash('Nomor WhatsApp harus diawali dengan 08')
                return redirect(url_for('admin.manage_users'))

            if form.password1.data != form.password2.data:
                flash('Password tidak sama')
                return redirect(url_for('admin.manage_users'))

            new_customer = User()
            new_customer.email = form.email.data
            new_customer.username = form.username.data
            new_customer.phone = form.phone.data
            new_customer.password = form.password1.data
            new_customer.roles = int(form.roles.data) if form.roles.data else 0
            new_customer.full_name = form.full_name.data

            db.session.add(new_customer)
            db.session.commit()
            flash('Akun berhasil dibuat')
            print('Akun berhasil dibuat:', new_customer.username)
            return redirect(url_for('admin.manage_users'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user: {e}")
            flash(f'Gagal membuat akun: {str(e)}')
            
    if form.errors:
        print("Form validation errors:", form.errors)
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}')

    return render_template('dashuser.html', 
                         users=users, 
                         form=form,
                         start_date=start_date,
                         end_date=end_date)
    
@admin.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.roles != 0 and current_user.roles!=4 and current_user.roles!=3:
        try:
            user_to_delete = User.query.get(user_id)
            if not user_to_delete:
                flash('User tidak ditemukan')
                return redirect(url_for('admin.manage_users'))
                
            if current_user.roles == 2 and user_to_delete.roles == 1:
                flash('Tidak memiliki izin untuk menghapus admin')
                return redirect(url_for('admin.manage_users'))
                
            if user_to_delete.id == current_user.id:
                flash('Tidak dapat menghapus akun sendiri')
                return redirect(url_for('admin.manage_users'))

            # Hapus seluruh cart dari user tsb
            Cart.query.filter_by(customer_link=user_id).delete()
            
            # Hapus pesanan user tsb
            orders = Order.query.filter_by(customer_link=user_id).all()
            for order in orders:
                # Delete detail order
                DetailOrder.query.filter_by(order_id=order.id).delete()
                # Delete  order
                db.session.delete(order)

            db.session.delete(user_to_delete)
            db.session.commit()
            flash('User berhasil dihapus')
            
        except Exception as e:
            db.session.rollback()
            print('User not deleted:', e)
            flash('Gagal menghapus user')
            
        return redirect(url_for('admin.manage_users'))
    return render_template('404.html')

@admin.route('/manage-returns')
@login_required
def manage_returns():
    if current_user.roles != 0 and current_user.roles!=4:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        query = ReturnOrder.query\
            .join(ReturnOrder.order_detail)\
            .join(DetailOrder.order)\
            .join(DetailOrder.variant)\
            .join(ProductVariant.main_product)
        
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%d/%m/%Y')
            end_date = datetime.strptime(end_date, '%d/%m/%Y') + timedelta(days=1)
            query = query.filter(ReturnOrder.date_requested >= start_date, 
                               ReturnOrder.date_requested < end_date)
            
        search = request.args.get('search')
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Order.customer_name.ilike(search_term)                )
            )
            
        if status:
            query = query.filter(ReturnOrder.status == status)

        returns = query.order_by(ReturnOrder.date_requested.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        
        return render_template('manage_returns.html', 
                             returns=returns,
                             selected_status=status,
                             start_date=start_date,
                             end_date=end_date)
                             
    return render_template('404.html')

@admin.route('/update-return-status/<int:return_id>', methods=['POST'])
@login_required
def update_return_status(return_id):
    if current_user.roles != 0 and current_user.roles!=4:
        return_order = ReturnOrder.query.get_or_404(return_id)
        new_status = request.form.get('status')
        
        if new_status not in ['Dalam Proses', 'Diterima', 'Ditolak', 'Selesai']:
            return jsonify({'error': 'Invalid status'}), 400
            
        try:
            if return_order.status != new_status:
                return_order.status = new_status
                
                if new_status == 'Selesai':
                    detail_order = DetailOrder.query.get(return_order.order_detail_id)
                    variant = detail_order.variant
                    
                    if variant.variant_type == 'refill':
                        # Cari atau buat variant tabung_bocor
                        bocor_variant = ProductVariant.query.filter_by(
                            product_id=variant.product_id,
                            variant_type='tabung_bocor'
                        ).first()
                        
                        # Buat variant tabung_bocor jika belum ada
                        if not bocor_variant:
                            bocor_variant = ProductVariant(
                                product_id=variant.product_id,
                                variant_name=f"Tabung Bocor {variant.main_product.product_name}",
                                variant_type='tabung_bocor',
                                price=0,  
                                stock=0
                            )
                            db.session.add(bocor_variant)
                        
                        bocor_variant.stock += return_order.quantity
                    
                    elif variant.variant_type == 'default':
                        # Untuk default, cukup kembalikan stok
                        variant.stock += return_order.quantity
                
                db.session.commit()
                flash('Status pengembalian berhasil diperbarui')
                
        except Exception as e:
            db.session.rollback()
            print(f"Error updating return status: {e}")
            flash('Gagal memperbarui status pengembalian')
            
        return redirect(url_for('admin.manage_returns'))
    return render_template('404.html')

@admin.route('/request-offline-return/<int:detail_id>', methods=['POST'])
@login_required
def request_offline_return(detail_id):
    print("Form data:", request.form) 

    if current_user.roles not in [1, 2, 3]: 
        return render_template('404.html')
        
    detail_order = DetailOrder.query.get_or_404(detail_id)
    order = Order.query.get(detail_order.order_id)
    
    current_time = datetime.utcnow() + timedelta(hours=7) 
    if not order.completed_at:
        flash('Waktu selesai pesanan tidak valid')
        return redirect(url_for('admin.manage_orders'))
        
    time_since_completed = current_time - order.completed_at
    if time_since_completed > timedelta(hours=1):
        flash('Pengembalian barang hanya bisa dilakukan dalam 1 jam setelah pesanan selesai!')
        return redirect(url_for('admin.manage_orders'))
    
    if not order.is_offline or order.status != 'Selesai':
        flash('Pengembalian hanya untuk transaksi offline yang sudah selesai')
        return redirect(url_for('admin.manage_orders'))
    
        
    reason = request.form.get('reason')
    return_quantity = int(request.form.get('quantity', 1))
    
    if not reason:
        flash('Mohon isi alasan pengembalian')
        return redirect(url_for('admin.manage_orders'))
        
    available_quantity = detail_order.quantity - detail_order.returned_quantity
    if return_quantity <= 0 or return_quantity > available_quantity:
        flash(f'Jumlah tidak sesuai. Maksimal {available_quantity} barang.')
        return redirect(url_for('admin.manage_orders'))
    
    new_return = ReturnOrder(
        order_detail_id=detail_id,
        reason=reason,
        return_category='tabung_bocor',
        quantity=return_quantity,
        status='Dalam Proses',
    )
    
    detail_order.returned_quantity += return_quantity
    if detail_order.returned_quantity >= detail_order.quantity:
        detail_order.can_return = False
    
    try:
        db.session.add(new_return)
        db.session.commit()
        flash('Pengembalian barang berhasil diajukan')
    except Exception as e:
        db.session.rollback()
        flash('Gagal mengajukan pengembalian barang')
        
    return redirect(url_for('admin.manage_orders'))


@admin.route('/convert-gas-bocor/<int:product_id>/<string:target_type>', methods=['POST'])
@login_required
def convert_gas_bocor(product_id, target_type):
    if current_user.roles != 0 and current_user.roles != 3:
        try:
            broken_variant = ProductVariant.query.filter_by(
                product_id=product_id,
                variant_type='tabung_bocor'
            ).first()
            
            if not broken_variant or broken_variant.stock <= 0:
                flash('Tidak ada tabung bocor yang tersedia untuk dikonversi')
                return redirect(url_for('admin.manage_shop_items'))

            quantity = int(request.form.get('quantity', 1))
            if quantity > broken_variant.stock:
                flash(f'Jumlah melebihi stok tabung bocor yang tersedia ({broken_variant.stock})')
                return redirect(url_for('admin.manage_shop_items'))

            target_type_map = {
                'isi': 'refill',
                'kosong': 'tabung_kosong'
            }
            
            target_variant = ProductVariant.query.filter_by(
                product_id=product_id,
                variant_type=target_type_map[target_type]
            ).first()

            if not target_variant:
                flash(f'Variant tujuan tidak ditemukan')
                return redirect(url_for('admin.manage_shop_items'))

            broken_variant.stock -= quantity
            target_variant.stock += quantity

            db.session.commit()
            flash(f'Berhasil mengkonversi {quantity} tabung bocor menjadi {target_variant.variant_name}')

        except Exception as e:
            db.session.rollback()
            print(f"Error converting broken tank: {e}")
            flash('Gagal mengkonversi tabung bocor')

        return redirect(url_for('admin.manage_shop_items'))
    return render_template('404.html')