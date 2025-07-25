from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from pymongo import MongoClient
import json
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fraud_detection_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# MongoDB bağlantısı
client = MongoClient("mongodb://localhost:27017/")
db = client["fraudDB"]
alerts_collection = db["alerts"]


@app.route('/')
def dashboard():
    """Ana dashboard sayfası"""
    return render_template('dashboard.html')


@app.route('/alerts')
def get_alerts():
    """Tüm fraud alerts'leri getir"""
    try:
        alerts = list(alerts_collection.find().sort("_id", -1).limit(100))

        # MongoDB ObjectId'yi string'e çevir
        for alert in alerts:
            alert['_id'] = str(alert['_id'])

        return jsonify({
            'success': True,
            'data': alerts,
            'total': len(alerts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/stats')
def get_stats():
    """Dashboard istatistikleri"""
    try:
        # Toplam fraud sayısı
        total_frauds = alerts_collection.count_documents({})

        # Son 24 saatteki fraud'lar
        yesterday = datetime.now() - timedelta(days=1)
        recent_frauds = alerts_collection.count_documents({
            "_id": {"$gte": yesterday}
        })

        # V özelliklerinin ortalamaları (top 5 riskli)
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "avg_v1": {"$avg": "$V1"},
                    "avg_v2": {"$avg": "$V2"},
                    "avg_v3": {"$avg": "$V3"},
                    "avg_v4": {"$avg": "$V4"},
                    "avg_v5": {"$avg": "$V5"},
                    "avg_amount": {"$avg": "$normAmount"}
                }
            }
        ]

        avg_results = list(alerts_collection.aggregate(pipeline))
        averages = avg_results[0] if avg_results else {}

        # Zaman bazlı dağılım (son 7 gün)
        time_distribution = []
        for i in range(7):
            day_start = datetime.now() - timedelta(days=i + 1)
            day_end = datetime.now() - timedelta(days=i)

            count = alerts_collection.count_documents({
                "_id": {
                    "$gte": day_start,
                    "$lt": day_end
                }
            })

            time_distribution.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'count': count
            })

        return jsonify({
            'success': True,
            'stats': {
                'total_frauds': total_frauds,
                'recent_frauds': recent_frauds,
                'averages': averages,
                'time_distribution': list(reversed(time_distribution))
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/live-count')
def live_count():
    """Canlı fraud sayısı"""
    try:
        count = alerts_collection.count_documents({})
        return jsonify({
            'success': True,
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


# Arka plan fraud takibi
def monitor_frauds():
    """Arka planda fraud'ları izle ve SocketIO ile bildir"""
    last_count = 0
    while True:
        try:
            current_count = alerts_collection.count_documents({})
            if current_count > last_count:
                new_frauds = current_count - last_count
                socketio.emit('new_fraud', {
                    'count': current_count,
                    'new_frauds': new_frauds,
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                })
                last_count = current_count
            time.sleep(2)  # 2 saniyede bir kontrol et
        except Exception as e:
            print(f"Monitoring error: {e}")
            time.sleep(5)


@socketio.on('connect')
def handle_connect():
    """Client bağlandığında mevcut sayıyı gönder"""
    try:
        count = alerts_collection.count_documents({})
        socketio.emit('fraud_count', {'count': count})
        print('Client connected')
    except Exception as e:
        print(f"Connect error: {e}")


if __name__ == '__main__':
    # Arka plan monitoring'i başlat
    monitor_thread = threading.Thread(target=monitor_frauds, daemon=True)
    monitor_thread.start()

    # Flask uygulamasını başlat
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)