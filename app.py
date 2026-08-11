import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify

app = Flask(__name__)

# Render 환경변수에서 DATABASE_URL을 가져옵니다.
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """PostgreSQL DB 연결 객체를 생성하여 반환합니다."""
    # Supabase Transaction Pooler (port 6543) 연동 시 SSL 설정 지원
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def init_db():
    """앱 실행 시 테스트 테이블 생성 및 초기 데이터 삽입"""
    if not DATABASE_URL:
        print("DATABASE_URL 환경변수가 설정되지 않았습니다.")
        return

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. 테스트용 테이블이 없으면 생성
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                role VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 2. 기존 데이터가 없을 때만 샘플 데이터 1건 삽입
        cur.execute("SELECT COUNT(*) FROM test_users;")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO test_users (name, role) 
                VALUES ('홍길동(테스트)', '관리자');
            """)
            
        conn.commit()
        cur.close()
        conn.close()
        print("DB Initialization Completed Successfully!")
    except Exception as e:
        print(f"DB Initialization Error: {e}")

# 앱 스타트 시 DB 초기화 실행
init_db()


@app.route('/')
def index():
    """기본 접속 페이지: DB에서 데이터를 조회해서 화면에 보여줍니다."""
    if not DATABASE_URL:
        return "❌ DATABASE_URL 환경변수가 설정되지 않았습니다.", 500

    try:
        conn = get_db_connection()
        # RealDictCursor를 사용하면 결과를 파이썬 딕셔너리 형태로 편하게 받습니다.
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # DB 데이터 조회
        cur.execute("SELECT * FROM test_users ORDER BY id ASC;")
        users = cur.fetchall()
        
        cur.close()
        conn.close()

        # 화면 출력용 HTML 구성
        user_list_html = "".join([
            f"<li><b>ID {u['id']}</b>: {u['name']} ({u['role']}) - 등록일: {u['created_at']}</li>" 
            for u in users
        ])
        
        return f"""
        <h1>🎉 Render <-> Supabase DB 연결 성공!</h1>
        <p>PostgreSQL 데이터베이스 조회가 정상적으로 수행되었습니다.</p>
        <h3>테스트 데이터 목록:</h3>
        <ul>
            {user_list_html}
        </ul>
        <hr>
        <p><a href="/api/users">👉 JSON API 결과 보기 (/api/users)</a></p>
        """
    except Exception as e:
        return f"<h1>❌ DB 연결 및 조회 실패</h1><p>에러 내용: {e}</p>", 500


@app.route('/api/users')
def get_users_api():
    """백엔드 API 테스트 엔드포인트: JSON 형식으로 반환"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM test_users;")
        users = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"status": "success", "data": users})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)