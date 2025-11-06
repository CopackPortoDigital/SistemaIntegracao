import requests

BASE = "http://127.0.0.1:8000"


def test_health():
    r = requests.get(f"{BASE}/")
    print('health status code:', r.status_code)
    assert r.status_code == 200
    data = r.json()
    assert data.get('status') == 'ok'


if __name__ == '__main__':
    print('Running quick sanity test...')
    test_health()
    print('If this passed, start using /register and /token to test auth-protected endpoints.')

