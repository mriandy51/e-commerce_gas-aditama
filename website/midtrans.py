import midtransclient

def create_midtrans_transaction(order_id, gross_amount, customer_details):
    snap = midtransclient.Snap(
    is_production=False,
    server_key='WRITE YOUR OWN KEY HERE',
    client_key='WRITE YOUR OWN KEY HERE'
)
    param = {
        "transaction_details": {
            "order_id": order_id,
            "gross_amount": gross_amount
        },
        "customer_details": customer_details,
        "credit_card": {
            "secure": True
        }
    }

    transaction = snap.create_transaction(param)
    return transaction['token']
