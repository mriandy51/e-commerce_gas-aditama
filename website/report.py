from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, make_response
from flask_login import login_required, current_user
import pdfkit
from .models import Order, Product, Complaint, DetailOrder, ReturnOrder
from sqlalchemy import func
from . import db
from calendar import monthrange

report = Blueprint('report', __name__)

@report.route('/report', methods=['GET'])
@login_required
def view_report():
    if current_user.roles not in [1, 2]:  
        return render_template('404.html')
        
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    page = request.args.get('page', 1, type=int)
    per_page = 10 

    query = Order.query

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%d/%m/%Y')
        end_date = datetime.strptime(end_date, '%d/%m/%Y') + timedelta(days=1)
        query = query.filter(Order.date_added >= start_date, Order.date_added < end_date)

    orders_pagination = query.order_by(Order.date_added.desc()).paginate(page=page, per_page=per_page)
    
    # Online Transactions
    online_query = Order.query.filter(
        Order.status == 'Selesai',
        Order.is_offline == False
    )
    if start_date and end_date:
        online_query = online_query.filter(Order.date_added >= start_date, Order.date_added < end_date)
    online_transactions = online_query.all()
    
    online_count = len(online_transactions)
    online_revenue = 0
    
    for order in online_transactions:
        order_revenue = 0
        for detail in order.details:
            return_request = ReturnOrder.query.filter_by(
                order_detail_id=detail.id,
                status='Selesai'
            ).first()
            
            if not return_request:
                order_revenue += detail.sub_total
        online_revenue += order_revenue
        
    # Hitung total pengembalian online
    if start_date and end_date:
        total_returns_online = db.session.query(
            func.sum(DetailOrder.price * ReturnOrder.quantity)
        ).join(
            ReturnOrder, DetailOrder.id == ReturnOrder.order_detail_id
        ).join(
            Order, DetailOrder.order_id == Order.id
        ).filter(
            ReturnOrder.status == 'Selesai',
            Order.date_added >= start_date,
            Order.date_added < end_date,
            Order.is_offline == False
        ).scalar() or 0
    else:
        total_returns_online = db.session.query(
            func.sum(DetailOrder.price * ReturnOrder.quantity)
        ).join(
            ReturnOrder, DetailOrder.id == ReturnOrder.order_detail_id
        ).join(
            Order, DetailOrder.order_id == Order.id
        ).filter(
            ReturnOrder.status == 'Selesai',
            Order.is_offline == False
        ).scalar() or 0

    # Offline Transactions
    offline_query = Order.query.filter(
        Order.status == 'Selesai',
        Order.is_offline == True
    )
    if start_date and end_date:
        offline_query = offline_query.filter(Order.date_added >= start_date, Order.date_added < end_date)
    offline_transactions = offline_query.all()
    
    offline_count = len(offline_transactions)
    offline_revenue = 0
    
    for order in offline_transactions:
        order_revenue = 0
        for detail in order.details:
            return_request = ReturnOrder.query.filter_by(
                order_detail_id=detail.id,
                status='Selesai'
            ).first()
            
            if not return_request:
                order_revenue += detail.sub_total
        offline_revenue += order_revenue
    
    total_revenue = online_revenue + offline_revenue
    
    # Hitung total pengembalian offline
    
    if start_date and end_date:
        total_returns_offline = db.session.query(
            func.sum(DetailOrder.price * ReturnOrder.quantity)
        ).join(
            ReturnOrder, DetailOrder.id == ReturnOrder.order_detail_id
        ).join(
            Order, DetailOrder.order_id == Order.id
        ).filter(
            ReturnOrder.status == 'Selesai',
            Order.date_added >= start_date,
            Order.date_added < end_date,
            Order.is_offline == True
        ).scalar() or 0
    else:
        total_returns_offline = db.session.query(
            func.sum(DetailOrder.price * ReturnOrder.quantity)
        ).join(
            ReturnOrder, DetailOrder.id == ReturnOrder.order_detail_id
        ).join(
            Order, DetailOrder.order_id == Order.id
        ).filter(
            ReturnOrder.status == 'Selesai',
            Order.is_offline == True
        ).scalar() or 0
    

    
    # Summary status
    status_query = db.session.query(
        Order.status, 
        func.count(Order.id)
    )
    if start_date and end_date:
        status_query = status_query.filter(Order.date_added >= start_date, Order.date_added < end_date)
    status_summary = status_query.group_by(Order.status).all()
    
    # Summary produk & variant
    variant_summary = []
    products = Product.query.all()
    
    for product in products:
        for variant in product.variants:
            sales_query = db.session.query(func.sum(DetailOrder.quantity))\
                .join(Order)\
                .filter(
                    DetailOrder.variant_id == variant.id,
                    Order.status == 'Selesai'
                )
            
            returns_query = db.session.query(func.sum(ReturnOrder.quantity))\
                .join(DetailOrder)\
                .filter(
                    DetailOrder.variant_id == variant.id,
                    ReturnOrder.status == 'Selesai'
                )
                
            if start_date and end_date:
                sales_query = sales_query.filter(Order.date_added >= start_date, Order.date_added < end_date)
                returns_query = returns_query.filter(ReturnOrder.date_requested >= start_date, ReturnOrder.date_requested < end_date)
                
            sold_quantity = sales_query.scalar() or 0
            returns = returns_query.scalar() or 0
            
            variant_summary.append({
                'product_name': product.product_name,
                'variant_name': variant.variant_name,
                'variant_type': variant.variant_type,
                'stock': variant.stock,
                'sold': sold_quantity,
                'returns': returns
            })
    
    # Summary Komplain
    complaint_query = db.session.query(
        Complaint.status,
        func.count(Complaint.id)
    )
    if start_date and end_date:
        complaint_query = complaint_query.filter(Complaint.date_added >= start_date, Complaint.date_added < end_date)
    complaint_summary = complaint_query.group_by(Complaint.status).all()
    
    # Summary Return 
    return_query = db.session.query(
        ReturnOrder.status,
        func.count(ReturnOrder.id)
    )
    if start_date and end_date:
        return_query = return_query.filter(ReturnOrder.date_requested >= start_date, ReturnOrder.date_requested < end_date)
    return_summary = return_query.group_by(ReturnOrder.status).all()

    # Product Returns Details
    variant_returns = []
    for product in products:
        for variant in product.variants:
            # Total sold query
            sold_query = db.session.query(func.sum(DetailOrder.quantity))\
                .join(Order)\
                .filter(
                    DetailOrder.variant_id == variant.id,
                    Order.status == 'Selesai'
                )
                
            # Total returns query
            returns_query = db.session.query(func.sum(ReturnOrder.quantity))\
                .join(DetailOrder)\
                .filter(
                    DetailOrder.variant_id == variant.id,
                    ReturnOrder.status == 'Selesai'
                )
                
            if start_date and end_date:
                sold_query = sold_query.filter(Order.date_added >= start_date, Order.date_added < end_date)
                returns_query = returns_query.filter(ReturnOrder.date_requested >= start_date, ReturnOrder.date_requested < end_date)
                
            total_sold = sold_query.scalar() or 0
            total_returns = returns_query.scalar() or 0
            
            total_return_value = total_returns * variant.price if total_returns else 0
            return_percentage = (total_returns / total_sold * 100) if total_sold > 0 else 0
            
            variant_returns.append({
                'product_name': product.product_name,
                'variant_name': variant.variant_name,
                'variant_type': variant.variant_type,
                'total_sold': total_sold,
                'total_returns': total_returns,
                'return_percentage': return_percentage,
                'return_value': total_return_value
            })
    
    return render_template(
        'report.html',
        start_date=start_date.strftime('%d/%m/%Y') if start_date else None,
        end_date=end_date.strftime('%d/%m/%Y') if end_date else None,
        total_revenue=total_revenue,
        online_revenue=online_revenue,
        offline_revenue=offline_revenue,
        online_count=online_count,
        offline_count=offline_count,
        total_returns_offline=total_returns_offline,
        total_returns_online=total_returns_online,
        status_summary=status_summary,
        variant_summary=variant_summary,
        complaint_summary=complaint_summary,
        return_summary=return_summary,
        variant_returns=variant_returns,
        orders=orders_pagination
    )
 

def generate_financial_report_pdf(start_date, end_date, orders, total_revenue, online_revenue, online_count, offline_revenue, offline_count, total_returns_value):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Laporan Keuangan</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 20px;
                color: #333;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            .date-range {{
                color: #666;
                margin-bottom: 20px;
                text-align: center;
            }}
            .summary-section {{
                margin-bottom: 30px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }}
            .summary-item {{
                margin-bottom: 10px;
            }}
            .summary-label {{
                font-weight: bold;
                color: #2c3e50;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                font-size: 12px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #2c3e50;
                color: white;
            }}
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}

            .footer {{
                margin-top: 30px;
                text-align: center;
                font-size: 12px;
                color: #666;
            }}
            .returned {{
                color: #dc2626;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Laporan Keuangan Pangkalan Gas Aditama</h1>
        </div>

        <div class="date-range">
        
            <p>Periode: {start_date.strftime('%d %B %Y')} - {(end_date - timedelta(days=1)).strftime('%d %B %Y')}</p>
        </div>

        <div class="summary-section">
            
            <div class="summary-item">
                <span class="summary-label">Jumlah Transaksi Online:</span>
                <span>{online_count}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">Pendapatan Online:</span>
                <span>Rp {"{:,.0f}".format(online_revenue)}</span>
            </div>
            <br>
            
            <div class="summary-item">
                <span class="summary-label">Jumlah Transaksi Offline:</span>
                <span>{offline_count}</span>
            </div>
            
            <div class="summary-item">
                <span class="summary-label">Pendapatan Offline:</span>
                <span>Rp {"{:,.0f}".format(offline_revenue)}</span>
            </div>
            <br>
            
            <div class="summary-item">
                <span class="summary-label">Total Transaksi:</span>
                <span>{online_count + offline_count}</span>
            </div>
            
            <div class="summary-item">
                <span class="summary-label">Total Pendapatan:</span>
                <span>Rp {"{:,.0f}".format(total_revenue)}</span>
            </div>
            
            <div class="summary-item">
                <span class="summary-label">Total Nilai Pengembalian:</span>
                <span>Rp {"{:,.0f}".format(total_returns_value)}</span>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>ID Pesanan</th>
                    <th>Pelanggan</th>
                    <th>Whatsapp</th>
                    <th>Status</th>
                    <th>Tipe</th>
                    <th>Pesanan Dibuat</th>
                    <th>Pesanan Selesai</th>
                    <th>Total Awal</th>
                    <th>Pengembalian</th>
                    <th>Total Akhir</th>
                </tr>
            </thead>
            <tbody>
                {generate_order_rows(orders)}
            </tbody>
        </table>

        <div class="footer">
            <p>Dicetak pada {datetime.now().strftime('%d %B %Y %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    """

    # Konfigurasi PDF 
    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': 'UTF-8',
        'no-outline': None,
        'enable-local-file-access': None
    }
    try:
        #config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')  # For Linux AWS 
        #pdf = pdfkit.from_string(html_content, False, configuration=config, options=options) #For linux AWS
        pdf = pdfkit.from_string(html_content, False, options=options)
        return pdf
    except Exception as e:
        print(f"Error generating PDF: {e}")
        raise 
 
    return pdf

def generate_order_rows(orders):
    rows = ""
    for order in orders:
        # Hitung money Sub total
        initial_total = sum(detail.sub_total for detail in order.details)
        
        # Hitung money pengembalian
        returns_total = sum(
            detail.price * return_order.quantity
            for detail in order.details
            for return_order in detail.return_request
            if return_order.status == 'Selesai'
        )

        final_total = initial_total - returns_total
        
        rows += f"""
            <tr>
                <td>{order.id}</td>
                <td>{order.customer_name if order.is_offline else order.user.full_name}</td>
                <td>{order.customer_phone if order.is_offline else order.user.phone}</td>
                <td>{order.status}</td>
                <td>{'Offline' if order.is_offline else 'Online'}</td>
                <td>{order.date_added.strftime('%d-%m-%Y %H:%M')}</td>
                <td>{order.completed_at.strftime('%d-%m-%Y %H:%M') if order.completed_at else '-'}</td>  
                <td>Rp {"{:,.0f}".format(initial_total)}</td>
                <td class="returned">{'Rp ' + "{:,.0f}".format(returns_total) if returns_total > 0 else '-'}</td>
                <td>Rp {"{:,.0f}".format(final_total)}</td>
            </tr>
        """
    return rows



@report.route('/generate-pdf')
@login_required
def generate_pdf():
    if current_user.roles not in [1, 2]:
        return render_template('404.html')

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    first_order_date = Order.query.order_by(Order.date_added.asc()).first()

    if not start_date or not end_date:
        end_date_print = datetime.now()
        #start_date_print = datetime(2025, 1, 1)
        start_date_print = first_order_date.date_added
        start_date = start_date_print.strftime('%d/%m/%Y')
        end_date = end_date_print.strftime('%d/%m/%Y')
    else:
        start_date_print = datetime.strptime(start_date, '%d/%m/%Y')
        end_date_print = datetime.strptime(end_date, '%d/%m/%Y')

    # Convert dates untuk query
    start_date_obj = datetime.strptime(start_date, '%d/%m/%Y')
    end_date_obj = datetime.strptime(end_date, '%d/%m/%Y') + timedelta(days=1)

    # Get orders 
    orders = Order.query.filter(
        Order.date_added >= start_date_obj,
        Order.date_added < end_date_obj,
        Order.status == 'Selesai'
    ).order_by(Order.date_added.desc()).all()

    # Hitung money revenue online
    online_transactions = Order.query.filter(
        Order.status == 'Selesai',
        Order.is_offline == False,
        Order.date_added >= start_date_obj,
        Order.date_added < end_date_obj
    ).all()

    online_len = online_transactions
    online_count = len(online_len)
    
    online_revenue = sum(
        detail.sub_total 
        for order in online_transactions 
        for detail in order.details 
        if not ReturnOrder.query.filter_by(
            order_detail_id=detail.id,
            status='Selesai'
        ).first()
    )

    # Hitung money revenue offliine
    offline_transactions = Order.query.filter(
        Order.status == 'Selesai',
        Order.is_offline == True,
        Order.date_added >= start_date_obj,
        Order.date_added < end_date_obj
    ).all()
    
    offline_revenue = sum(
        detail.sub_total 
        for order in offline_transactions 
        for detail in order.details 
        if not ReturnOrder.query.filter_by(
            order_detail_id=detail.id,
            status='Selesai'
        ).first()
    )
    
    offline_len = offline_transactions
    offline_count = len(offline_len)

    total_revenue = online_revenue + offline_revenue

    # Hitung total pengembalian
    total_returns_value = db.session.query(
        func.sum(DetailOrder.price * ReturnOrder.quantity)
    ).join(
        ReturnOrder, DetailOrder.id == ReturnOrder.order_detail_id
    ).join(
        Order, DetailOrder.order_id == Order.id
    ).filter(
        ReturnOrder.status == 'Selesai',
        Order.date_added >= start_date_obj,
        Order.date_added < end_date_obj
    ).scalar() or 0

    pdf = generate_financial_report_pdf(
        start_date_obj,
        end_date_obj - timedelta(days=1),  
        orders,
        total_revenue,
        online_revenue,
        online_count,
        offline_revenue,
        offline_count,
        total_returns_value
    )

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=laporan_keuangan_{start_date_obj.strftime("%d-%m-%Y")}_{(end_date_obj - timedelta(days=1)).strftime("%d-%m-%Y")}.pdf'

    return response
