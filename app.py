
import sqlite3
import logging
import secrets
import random
import os
from datetime import datetime, timedelta
import pytz
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, g, flash, abort, session, jsonify, send_file, make_response, send_from_directory
from io import BytesIO
from functools import wraps

app = Flask(__name__)
app.config.update(
    DEBUG=False,
    SECRET_KEY='dev',
    DATABASE=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'votes.db')
)

# 验证码数据库表结构
CAPTCHA_SCHEMA = """
DROP TABLE IF EXISTS captcha_sessions;

CREATE TABLE captcha_sessions (
    id TEXT PRIMARY KEY,
    answer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
"""

def init_captcha_tables():
    """初始化验证码相关数据表"""
    with app.app_context():
        db = get_db()
        db.executescript(CAPTCHA_SCHEMA)
        db.commit()

from captcha.image import ImageCaptcha
import string

def generate_captcha_text(length=4):
    """生成随机验证码文本"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_captcha_image(text):
    """生成验证码图片"""
    image = ImageCaptcha(width=160, height=60)
    data = image.generate(text)
    return BytesIO(data.read())

def store_captcha_session(session_id, answer):
    """存储验证码会话"""
    db = get_db()
    expires_at = datetime.now(pytz.UTC) + timedelta(minutes=5)
    db.execute(
        'INSERT INTO captcha_sessions (id, answer, expires_at) VALUES (?, ?, ?)',
        (session_id, answer, expires_at.strftime('%Y-%m-%d %H:%M:%S'))
    )
    db.commit()

def verify_captcha_answer(session_id, answer):
    """验证验证码答案"""
    db = get_db()
    now = datetime.now(pytz.UTC)
    
    result = db.execute(
        '''SELECT answer FROM captcha_sessions 
           WHERE id = ? AND expires_at > ?''',
        (session_id, now.strftime('%Y-%m-%d %H:%M:%S'))
    ).fetchone()
    
    if not result:
        return False
        
    # 清理已使用的验证码
    db.execute('DELETE FROM captcha_sessions WHERE id = ?', (session_id,))
    db.commit()
    
    return result['answer'].upper() == answer.upper()

@app.route('/api/captcha', methods=['GET'])
def get_captcha():
    """获取验证码图片"""
    # 生成验证码文本和会话ID
    captcha_text = generate_captcha_text()
    session_id = secrets.token_urlsafe(32)
    
    # 存储验证码会话
    store_captcha_session(session_id, captcha_text)
    
    # 生成验证码图片
    img_byte_arr = generate_captcha_image(captcha_text)
    
    # 返回图片和会话ID
    response = make_response(send_file(img_byte_arr, mimetype='image/png'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['X-Captcha-ID'] = session_id
    return response

@app.route('/api/verify-captcha', methods=['POST'])
def verify_captcha():
    """验证用户提交的验证码"""
    data = request.get_json()
    if not data or 'captcha_id' not in data or 'answer' not in data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400

    session_id = data['captcha_id']
    answer = data['answer']
    
    if verify_captcha_answer(session_id, answer):
        session['captcha_verified'] = True
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': '验证码错误，请重试'})

def setup_logging():
    handler = RotatingFileHandler('app.log', maxBytes=1024 * 1024, backupCount=10)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    handler.setLevel(logging.ERROR)
    app.logger.addHandler(handler)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

def with_db(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            app.logger.error(f"Database error in {f.__name__}: {e}", exc_info=True)
            flash('操作失败，请稍后重试')
            return redirect(url_for('index'))
    return decorated_function

setup_logging()

@app.teardown_appcontext
def close_db(error):
    if db := g.pop('db', None):
        db.close()

def init_db():
    """Initialize the database."""
    # 确保在应用上下文中运行
    if not app.config.get('DATABASE'):
        raise RuntimeError('Database configuration not found')

    db_path = app.config['DATABASE']

    # 关闭所有现有连接
    if hasattr(g, 'db'):
        g.db.close()
        delattr(g, 'db')

    # 删除现有数据库文件
    try:
        if os.path.exists(db_path):
            # 确保文件未被锁定
            with open(db_path, 'a'):
                os.remove(db_path)
    except (IOError, OSError) as e:
        print(f"Error removing database file: {e}")
        return

    # 创建新的数据库连接
    try:
        # 创建新的数据库连接，不使用get_db()以避免缓存
        db = sqlite3.connect(db_path, isolation_level=None)
        db.row_factory = sqlite3.Row

        # 禁用外键约束和日志
        db.execute("PRAGMA foreign_keys = OFF")
        db.execute("PRAGMA journal_mode = OFF")
        db.execute("PRAGMA synchronous = OFF")
        db.execute("BEGIN TRANSACTION")

        # 读取并执行schema
        with open('schema.sql', 'r', encoding='utf-8') as f:
            db.executescript(f.read())

        # 插入初始数据
        utc_now = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
        db.execute('INSERT INTO polls (question, created_at) VALUES (?, ?)',
                  ('您最喜欢的编程语言是？', utc_now))
        poll_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        for option in ['Python', 'JavaScript', 'Java', 'C++']:
            db.execute('INSERT INTO options (poll_id, option_text) VALUES (?, ?)',
                      (poll_id, option))

        # 初始化验证码表
        db.executescript(CAPTCHA_SCHEMA)

        # 提交事务并重新启用约束
        db.execute("COMMIT")
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("PRAGMA journal_mode = WAL")
        db.execute("PRAGMA synchronous = NORMAL")

        print('数据库初始化完成')

    except Exception as e:
        print(f'初始化失败: {e}')
        if 'db' in locals():
            db.execute("ROLLBACK")
    finally:
        if 'db' in locals():
            db.close()

@app.after_request
def handle_db_transaction(response):
    db = g.pop('db', None)
    if db is not None:
        try:
            if response.status_code < 500:
                db.commit()
            else:
                db.rollback()
        except Exception as e:
            app.logger.error(f"Database transaction error: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()
    return response

def get_client_ip():
    return request.headers.get('X-Real-IP') or \
           request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or \
           request.remote_addr

def convert_to_local_time(utc_time_str):
    local_tz = pytz.timezone('Asia/Shanghai')
    utc_time = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
    utc_time = pytz.utc.localize(utc_time)
    local_time = utc_time.astimezone(local_tz)
    return local_time.strftime('%Y-%m-%d %H:%M')

# 为所有模板提供now变量
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# 路由
@app.route('/')
def index():
    db = get_db()
    polls = db.execute('SELECT * FROM polls ORDER BY id DESC').fetchall()
    
    ip_address = get_client_ip()
    polls_with_status = []
    
    for poll in polls:
        last_vote = db.execute('''
            SELECT voted_at FROM vote_records 
            WHERE poll_id = ? AND (ip_address = ? OR browser_fingerprint IN (
                SELECT DISTINCT browser_fingerprint FROM vote_records 
                WHERE poll_id = ? AND ip_address = ?
            ))
            ORDER BY voted_at DESC LIMIT 1
        ''', [poll['id'], ip_address, poll['id'], ip_address]).fetchone()
        
        poll_info = dict(poll)
        poll_info['created_at'] = convert_to_local_time(poll['created_at'])
        poll_info['has_voted'] = last_vote is not None
        poll_info['vote_time'] = convert_to_local_time(last_vote['voted_at']) if last_vote else None
        polls_with_status.append(poll_info)
    
    return render_template('index.html', polls=polls_with_status)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        password = request.form.get('password')
        question = request.form['question'].strip()
        options = [opt.strip() for opt in request.form.getlist('options[]') if opt.strip()]

        if password != '995907':
            return """
                <script>
                    alert('创建密码错误');
                    window.location.href = '{}';
                </script>
            """.format(url_for('create'))

        options = [opt.strip() for opt in request.form.getlist('options[]') if opt.strip()]
        
        if not question:
            flash('问题不能为空')
            return render_template('create.html', question=question, options=options)
        
        if len(options) < 2:
            flash('至少需要两个有效选项')
            return render_template('create.html', question=question, options=options)
        
        try:
            db = get_db()
            utc_now = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
            
            db.execute('INSERT INTO polls (question, created_at) VALUES (?, ?)', 
                      [question, utc_now])
            poll_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            for option in options:
                db.execute('INSERT INTO options (poll_id, option_text) VALUES (?, ?)',
                          [poll_id, option])
            
            flash('投票创建成功！')
            return redirect(url_for('index'))
        except Exception as e:
            app.logger.error(f"Create poll failed: {e}", exc_info=True)
            flash('创建投票失败，请稍后重试')
            return render_template('create.html', question=question, options=options)
    
    return render_template('create.html')

@app.route('/vote/<int:poll_id>', methods=['GET', 'POST'])
def vote(poll_id):
    db = get_db()
    poll = db.execute('SELECT * FROM polls WHERE id = ?', [poll_id]).fetchone()
    options = db.execute('SELECT * FROM options WHERE poll_id = ?', [poll_id]).fetchall()
    
    if not poll or not options:
        abort(404)
    
    ip_address = get_client_ip()
    last_vote = db.execute('''
        SELECT 1 FROM vote_records 
        WHERE poll_id = ? AND (ip_address = ? OR browser_fingerprint IN (
            SELECT DISTINCT browser_fingerprint FROM vote_records 
            WHERE poll_id = ? AND ip_address = ?
        ))
        LIMIT 1
    ''', [poll_id, ip_address, poll_id, ip_address]).fetchone()
    
    if last_vote:
        return """
            <script>
                alert('您已经参与过这个投票了');
                window.location.href = '{}';
            </script>
        """.format(url_for('results', poll_id=poll_id))
    
    if request.method == 'POST':
        fingerprint = request.form.get('fingerprint')
        option_id = request.form.get('option')
        
        if not session.get('captcha_verified'):
            flash('请先完成验证码验证')
            return render_template('vote.html', poll=poll, options=options)
            
        if not fingerprint:
            flash('无法验证浏览器指纹，请确保启用了JavaScript')
            return render_template('vote.html', poll=poll, options=options)
        
        if not option_id:
            flash('请选择一个选项')
            return render_template('vote.html', poll=poll, options=options)
        
        try:
            db.execute('UPDATE options SET votes = votes + 1 WHERE id = ? AND poll_id = ?', 
                      [option_id, poll_id])
            db.execute('''
                INSERT INTO vote_records (poll_id, option_id, ip_address, browser_fingerprint)
                VALUES (?, ?, ?, ?)
            ''', [poll_id, option_id, ip_address, fingerprint])
            flash('投票成功！')
            return redirect(url_for('results', poll_id=poll_id))
        except Exception as e:
            app.logger.error(f"Vote failed: {e}", exc_info=True)
            flash('投票失败，请重试')
            return redirect(url_for('vote', poll_id=poll_id))
    
    return render_template('vote.html', poll=poll, options=options)

@app.route('/results/<int:poll_id>')
def results(poll_id):
    db = get_db()
    poll = db.execute('SELECT * FROM polls WHERE id = ?', [poll_id]).fetchone()
    options = db.execute('SELECT * FROM options WHERE poll_id = ?', [poll_id]).fetchall()
    
    if not poll or not options:
        abort(404)
    
    poll_info = dict(poll)
    poll_info['created_at'] = convert_to_local_time(poll['created_at'])
    
    return render_template('results.html', poll=poll_info, options=options)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(Exception)
def handle_error(e):
    app.logger.error(f'Error: {e}', exc_info=True)
    return render_template('500.html'), 500

# 添加命令行命令
@app.cli.command('init-db')
def init_db_command():
    """初始化数据库."""
    init_db()
    print('数据库初始化完成.')

def ensure_captcha_table():
    """确保验证码表存在"""
    db = get_db()
    # 检查表是否存在
    result = db.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='captcha_sessions'
    """).fetchone()
    
    if not result:
        # 如果表不存在，创建它
        db.executescript(CAPTCHA_SCHEMA)
        db.commit()

if __name__ == '__main__':
    # 在应用启动时初始化验证码表
    with app.app_context():
        ensure_captcha_table()
    app.run(debug=True)