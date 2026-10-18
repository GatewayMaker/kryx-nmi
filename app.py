"""
KRYX NMI 1$ CHKR - Web & API Service
Developer: @sweartx
Telegram Channel: t.me/KryxCheck
"""

import os
import time
import hashlib
import sqlite3
import threading
from typing import Optional
import requests
from flask import Flask, request, jsonify, render_template
from checker import (
    check_card,
    gateway_manager,
    GATEWAY_CONFIG,
    DEVELOPER,
    TELEGRAM_CHANNEL
)

app = Flask(__name__)

app.config['JSON_SORT_KEYS'] = False
app.json.ensure_ascii = False

# Multi-Worker & Multi-Thread Synchronized Active Users Store
DB_PATH = os.path.join(os.path.dirname(__file__), 'active_users.db')
START_TIME = time.time()

def init_db():
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS active_clients (
                    client_id TEXT PRIMARY KEY,
                    last_seen REAL
                )
            """)
    except Exception:
        pass

init_db()

# -------------------------------------------------------------
# KEEP-ALIVE SELF PINGER (Prevents Render Free Tier from Sleeping)
# -------------------------------------------------------------
SELF_PING_INTERVAL = 60  # Pings every 60 seconds
DETECTED_APP_URL = os.environ.get('RENDER_EXTERNAL_URL') or os.environ.get('APP_URL') or ''

def keep_alive_worker():
    """Background worker that pings own /health endpoint every 60s so Render stays awake 24/7."""
    time.sleep(15)  # Wait for server to bind
    while True:
        target_url = DETECTED_APP_URL or os.environ.get('RENDER_EXTERNAL_URL') or os.environ.get('APP_URL')
        if target_url:
            ping_url = target_url.rstrip('/') + '/health'
            try:
                requests.get(ping_url, timeout=10)
            except Exception:
                pass
        time.sleep(SELF_PING_INTERVAL)

def start_keep_alive():
    t = threading.Thread(target=keep_alive_worker, daemon=True, name="render_keep_alive")
    t.start()

start_keep_alive()


def register_client_activity(client_id: Optional[str] = None):
    """Registers heartbeat for a real client tab/session (synced across all Gunicorn workers)."""
    if not client_id or not client_id.strip():
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1').split(',')[0].strip()
        ua = request.headers.get('User-Agent', '')
        client_id = hashlib.md5(f"{client_ip}:{ua}".encode()).hexdigest()[:16]

    now = time.time()
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            conn.execute("INSERT OR REPLACE INTO active_clients (client_id, last_seen) VALUES (?, ?)", (client_id, now))
            conn.execute("DELETE FROM active_clients WHERE last_seen < ?", (now - 25.0,))
    except Exception:
        pass


def remove_client(client_id: Optional[str]):
    """Removes a client immediately upon tab close/disconnect across all workers."""
    if not client_id:
        return
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            conn.execute("DELETE FROM active_clients WHERE client_id = ?", (client_id,))
    except Exception:
        pass


def get_real_active_count() -> int:
    """Returns actual real concurrent active user count synced across all workers."""
    now = time.time()
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            conn.execute("DELETE FROM active_clients WHERE last_seen < ?", (now - 25.0,))
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM active_clients")
            row = cur.fetchone()
            count = row[0] if row else 1
            return max(count, 1)
    except Exception:
        return 1


@app.before_request
def auto_detect_app_host():
    """Captures the live app host URL from incoming requests for self-ping keep-alive."""
    global DETECTED_APP_URL
    if not DETECTED_APP_URL and request.host_url:
        host = request.host_url.rstrip('/')
        if 'localhost' not in host and '127.0.0.1' not in host:
            DETECTED_APP_URL = host


@app.route('/')
def index():
    cid = request.args.get('client_id', '')
    register_client_activity(cid)
    active_users = get_real_active_count()
    cfg = gateway_manager.get_config()
    return render_template(
        'index.html',
        active_users=active_users,
        org_name=cfg.get('org_name', 'BookSpring'),
        charge_amount=f"${cfg.get('charge_amount', '1')}.00 {cfg.get('currency', 'USD')}",
        gateway_name="NMI (SafeSave / DonorPerfect)",
        developer=DEVELOPER,
        channel=TELEGRAM_CHANNEL
    )


@app.route('/health', methods=['GET'])
def health():
    cfg = gateway_manager.get_config()
    return jsonify({
        "status": "ok",
        "service": "KRYX NMI CHKR",
        "gateway": "NMI 1$ Charge Gateway",
        "merchant": cfg.get('org_name', 'BookSpring'),
        "charge_amount": f"${cfg.get('charge_amount', '1')}.00 {cfg.get('currency', 'USD')}",
        "keep_alive_active": True,
        "ping_target": DETECTED_APP_URL or os.environ.get('RENDER_EXTERNAL_URL') or "Auto-detected on Render",
        "active_users": get_real_active_count(),
        "uptime": f"{round(time.time() - START_TIME, 1)}s",
        "developer": DEVELOPER,
        "channel": TELEGRAM_CHANNEL
    })


@app.route('/api/ping', methods=['GET', 'POST'])
def api_ping():
    """Heartbeat endpoint to track authentic concurrent users."""
    cid = request.args.get('client_id') or (request.get_json(silent=True) or {}).get('client_id')
    register_client_activity(cid)
    return jsonify({
        "status": "ok",
        "active_users": get_real_active_count()
    })


@app.route('/api/disconnect', methods=['POST'])
def api_disconnect():
    """Unload beacon endpoint to decrement user count instantly on tab close."""
    cid = request.args.get('client_id') or request.form.get('client_id') or (request.get_json(silent=True) or {}).get('client_id')
    remove_client(cid)
    return jsonify({"status": "ok"})


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Live telemetry stats for UI telemetry badges."""
    cid = request.args.get('client_id', '')
    register_client_activity(cid)
    cfg = gateway_manager.get_config()
    tok = cfg.get('tokenization_key', '')
    masked_key = f"{tok[:6]}...{tok[-4:]}" if len(tok) > 10 else "READY"
    return jsonify({
        "status": "ok",
        "service": "KRYX NMI CHKR",
        "gateway_ready": bool(tok),
        "gateway_merchant": cfg.get('org_name', 'BookSpring'),
        "charge_amount": f"${cfg.get('charge_amount', '1')}.00 {cfg.get('currency', 'USD')}",
        "tokenization_key": masked_key,
        "active_users": get_real_active_count(),
        "uptime_seconds": int(time.time() - START_TIME),
        "developer": DEVELOPER,
        "channel": TELEGRAM_CHANNEL
    })


@app.route('/api/gateway/refresh', methods=['GET', 'POST'])
def api_gateway_refresh():
    """Forces dynamic refresh of NMI Gateway tokenization key and form details."""
    proxy = request.args.get('proxy', '') or (request.get_json(silent=True) or {}).get('proxy', '')
    gateway_manager.refresh(proxy=proxy or None)
    cfg = gateway_manager.get_config()
    tok = cfg.get('tokenization_key', '')
    return jsonify({
        "status": "ok",
        "message": "NMI Gateway parameters refreshed successfully",
        "merchant": cfg.get('org_name'),
        "tokenization_key": f"{tok[:6]}...{tok[-4:]}" if len(tok) > 10 else "READY"
    })


@app.route('/api/check', methods=['GET', 'POST'])
def api_check():
    cid = request.args.get('client_id', '')
    register_client_activity(cid)

    card = ''
    proxy = ''

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json(silent=True) or {}
            card = data.get('card') or data.get('rave') or ''
            proxy = data.get('proxy', '')
        else:
            card = request.form.get('card') or request.form.get('rave') or ''
            proxy = request.form.get('proxy', '')

    if not card:
        card = request.args.get('card') or request.args.get('rave') or ''
    if not proxy:
        proxy = request.args.get('proxy', '')

    res = check_card(card_str=card, proxy=proxy)
    return jsonify(res)


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"status": "ERROR", "message": "Endpoint not found"}), 404
    return "Not Found", 404


@app.errorhandler(500)
def server_error(e):
    if request.path.startswith('/api/'):
        return jsonify({"status": "ERROR", "message": "Internal server error"}), 500
    return "Internal Server Error", 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
