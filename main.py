from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)


# Функция для подключения к БД
def get_db_connection():
    try:
        # Получаем URL базы из переменных окружения
        DATABASE_URL = os.environ.get('DATABASE_URL')

        if not DATABASE_URL:
            print("❌ DATABASE_URL не найден в переменных окружения!")
            return None

        # Подключаемся к базе
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Успешное подключение к PostgreSQL!")
        return conn

    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return None


# Создаём подключение при старте приложения
conn = get_db_connection()

# Создаём таблицу если её нет
if conn:
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
        conn.commit()
        print("✅ Таблица 'messages' готова к работе")
    except Exception as e:
        print(f"❌ Ошибка создания таблицы: {e}")


# Маршруты API
@app.route('/')
def hello():
    return "Hello, Serverless with Database! 🚀\n", 200, {'Content-Type': 'text/plain'}


@app.route('/save', methods=['POST'])
def save_message():
    if not conn:
        return jsonify({"error": "База данных не подключена"}), 500

    data = request.get_json()

    if not data or 'message' not in data:
        return jsonify({"error": "Нужен JSON с полем 'message'"}), 400

    message = data['message']

    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO messages (content) VALUES (%s)", (message,))
            conn.commit()

        return jsonify({
            "status": "success",
            "message": "Сообщение сохранено в базу",
            "your_message": message
        })

    except Exception as e:
        return jsonify({"error": f"Ошибка базы данных: {str(e)}"}), 500


@app.route('/messages')
def get_messages():
    if not conn:
        return jsonify({"error": "База данных не подключена"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, content, created_at 
                FROM messages 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            rows = cur.fetchall()

        messages = []
        for row in rows:
            messages.append({
                "id": row[0],
                "text": row[1],
                "time": str(row[2])  # Преобразуем дату в строку
            })

        return jsonify({
            "total": len(messages),
            "messages": messages
        })

    except Exception as e:
        return jsonify({"error": f"Ошибка чтения из БД: {str(e)}"}), 500


@app.route('/health')
def health_check():
    db_status = "connected" if conn else "disconnected"
    return jsonify({
        "status": "healthy",
        "database": db_status,
        "service": "Serverless Lab with PostgreSQL"
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)