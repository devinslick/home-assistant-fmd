import base64

sig = 'hb+EcVgn2dMNxLg+VbjClTe0V8yhgijh4C9lqd0lHI+WZhuVfT4buShN1NIzgUezh8xWxmVGBoXkpjDj7bOIuF0N450NLH6pWKtdhnYYxK4Roxn0KvvJBtyNvshJww9sbPgO1Ng9Qbf6oAGU4zb7sN9hMSUF5wUOhhyY1OEcYHD6oLVIPxqjzCdekDM3KjRRslLLhe/kRbs4MNiGP1uresXC6EOLWPhgTXLYXogxOLhN/pxsAIJTjNzop/prVFVOn0ZUPgpNVisTHMSb2ImDZaKJvFhss+ty/0xfjaOOWCXt2fFG+L8azZibTxZRpOlH/ftkQYK8y4Z/G6y3ab5Rb8vhdlIB1ttWus6/4S1US/+XYZYOYL6LlmfbJhZ3zISbousZ2glZBoJkKcLHDk6c7hpfQjh6A2Opa6pSmPLmfe3WVIK1OCfe0M+FBipu/eXvXNALpdvOMU2UVNdTqnCZf06AVcgaEgOXMrt6bXCLLEB8DpT+NMZusekXovRetrsT'

print(f'Signature length: {len(sig)} chars')
print(f'Has = padding: {"=" in sig}')

try:
    raw = base64.b64decode(sig)
    print(f'Raw signature: {len(raw)} bytes')
    print(f'Expected: 384 bytes for RSA-3072')
    print(f'Match: {len(raw) == 384}')
except Exception as e:
    print(f'Error decoding: {e}')

# Compare with our format
our_sig = 'luyQ3BwwM6KDXWiDBOa922ymMvC9xQvs9x7QYS9EeZGK7X1uoUdf3WIsixhuAprgMDi613'
print(f'\nOur signature length: {len(our_sig)} chars')
print(f'Both are ~512 chars (no padding): {len(sig) > 500 and len(our_sig) > 500}')
