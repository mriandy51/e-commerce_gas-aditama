import midtransclient

def create_midtrans_transaction(order_id, gross_amount, customer_details):
    snap = midtransclient.Snap(
    is_production=False,
    server_key='SB-Mid-server-7mR3-jbBLtZ-shC3OiZqPDqo',
    client_key='SB-Mid-client-z_VKWl4iEpLX2i1q'
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
