import json
import urllib.request

payload = {
    'vendor': 'Test Vendor',
    'invoice_number': 'INV-DEBUG-001',
    'invoice_date': '2026-07-28',
    'division': 'Sales',
    'category': 'Purchase',
    'payment_method': 'Transfer',
    'description': 'Debug save with items',
    'grand_total': 350000,
    'items': [
        {'item': 'Produk A', 'qty': 1, 'price': 150000, 'total': 150000},
        {'item': 'Produk B', 'qty': 2, 'price': 100000, 'total': 200000}
    ]
}

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/save',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req, timeout=30) as resp:
    print('save status', resp.status)
    result = json.loads(resp.read().decode('utf-8'))
    print('save result', json.dumps(result, indent=2, ensure_ascii=False))
    doc_id = result.get('document_id')

if doc_id is not None:
    url2 = f'http://127.0.0.1:8000/api/documents/{doc_id}'
    with urllib.request.urlopen(url2, timeout=30) as resp2:
        print('detail status', resp2.status)
        detail = json.loads(resp2.read().decode('utf-8'))
        print('detail result', json.dumps(detail, indent=2, ensure_ascii=False))
else:
    print('Document ID not returned')
