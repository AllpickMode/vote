
import sqlite3
import logging
import secrets
import random
from datetime import datetime, timedelta
import pytz
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, g, flash, abort, session, jsonify, send_file, make_response, send_from_directory
from io import BytesIO
from PIL import Image, ImageDraw
from functools import wraps

app = Flask(__name__)
app.config.update(
    DEBUG=False,
    SECRET_KEY='dev',
    DATABASE='votes.db',
    CAPTCHA_TOLERANCE=10,  # 验证码允许的误差范围（像素）
    CAPTCHA_EXPIRE_SECONDS=300  # 验证码过期时间（秒）
)

# 新增数据库表结构
CAPTCHA_SCHEMA = """
CREATE TABLE IF NOT EXISTS captcha_data (
    token TEXT PRIMARY KEY,
    target_pos INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verification_tokens (
    token TEXT PRIMARY KEY,
    expires REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def init_captcha_tables():
    """初始化验证码相关数据表"""
    with app.app_context():
        db = get_db()
        db.executescript(CAPTCHA_SCHEMA)
        db.commit()

def generate_captcha_signature(token, target_pos):
    """生成验证码数据的HMAC签名"""
    secret_key = app.config['SECRET_KEY'].encode()
    # 加入时间戳要素防止重放攻击
    timestamp = str(int(datetime.now(pytz.UTC).timestamp()))
    message = f"{token}:{target_pos}:{timestamp}".encode()
    return hmac.new(secret_key, message, hashlib.sha256).hexdigest()

def store_verification_token(token, expires):
    """存储验证令牌到数据库"""
    db = get_db()
    db.execute(
        'INSERT INTO verification_tokens (token, expires) VALUES (?, ?)',
        (token, expires)
    )
    db.commit()

def store_captcha_data(token, target_pos):
    """存储验证码数据到数据库"""
    db = get_db()
    db.execute(
        'INSERT INTO captcha_data (token, target_pos) VALUES (?, ?)',
        (token, target_pos)
    )
    db.commit()

def get_stored_target_pos(token):
    """从数据库获取存储的目标位置"""
    db = get_db()
    result = db.execute(
        'SELECT target_pos FROM captcha_data WHERE token = ?',
        (token,)
    ).fetchone()
    return result['target_pos'] if result else None

def generate_captcha(verification_token):
    """生成验证码图片并存储到数据库"""
    # 创建背景图
    bg_width, bg_height = 280, 150
    bg = Image.new('RGB', (bg_width, bg_height), (255, 255, 255))
    draw = ImageDraw.Draw(bg)
    
    # 绘制随机干扰线
    for _ in range(5):
        draw.line([
            (secrets.randbelow(bg_width), secrets.randbelow(bg_height)),
            (secrets.randbelow(bg_width), secrets.randbelow(bg_height))
        ], fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), width=2)

    # 生成拼图滑块位置
    target_pos = secrets.randbelow(200) + 40  # 40-240之间的随机位置
    puzzle_size = 40
    
    # 绘制目标缺口
    draw.rounded_rectangle(
        (target_pos, 50, target_pos + puzzle_size, 90),
        radius=8, fill=(200, 200, 200), outline=(0, 0, 0), width=2
    )
    
    # 在前景绘制滑块图形（用户不可见，仅用于后端记录）
    slider = Image.new('RGBA', (puzzle_size, 40))
    slider_draw = ImageDraw.Draw(slider)
    slider_draw.rounded_rectangle(
        (0, 0, puzzle_size, 40),
        radius=8, fill=(255, 255, 255, 0), outline=(0, 0, 0), width=2
    )
    # 添加随机旋转（-15到+15度）
    bg.paste(slider.rotate(random.randint(-15, 15), expand=True), 
           (target_pos, 50), slider.rotate(random.randint(-15, 15), expand=True))
    
    # 将图片保存到字节流
    img_byte_arr = BytesIO()
    bg.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    # 存储到数据库
    store_captcha_data(verification_token, target_pos)
    return img_byte_arr

import base64
import hmac
import hashlib

@app.route('/api/captcha/generate', methods=['GET'])
def generate_captcha_api():
    """生成新的验证码"""
    # 生成验证令牌
    verification_token = secrets.token_urlsafe(32)
    expires = datetime.now(pytz.UTC).timestamp() + app.config['CAPTCHA_EXPIRE_SECONDS']
    
    # 生成验证码图片并存储到数据库
    img_byte_arr = generate_captcha(verification_token)
    
    # 存储验证令牌有效期
    store_verification_token(verification_token, expires)
    
    # 直接返回图片二进制流
    # 设置禁止缓存的响应头
    response = make_response(send_file(
        img_byte_arr,
        mimetype='image/png',
        as_attachment=False,
        download_name='captcha.png'
    ))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/captcha/verify', methods=['POST'])
def verify_captcha():
    """验证滑块位置"""
    data = request.get_json()
    required_fields = ['position', 'verification_token']
    if not data or any(field not in data for field in required_fields):
        return jsonify({'success': False, 'message': '无效的请求参数'}), 400

    db = get_db()
    # 从数据库获取验证令牌和存储的目标位置
    record = db.execute(
        '''SELECT v.expires, c.target_pos 
           FROM verification_tokens v
           JOIN captcha_data c ON v.token = c.token
           WHERE v.token = ?''',
        (data['verification_token'],)
    ).fetchone()

    if not record:
        return jsonify({'success': False, 'message': '验证令牌无效'}), 400
        
    # 检查过期时间
    now = datetime.now(pytz.UTC).timestamp()
    if now > record['expires']:
        db.execute(
            'DELETE FROM verification_tokens WHERE token = ?',
            (data['verification_token'],)
        )
        db.commit()
        return jsonify({'success': False, 'message': '验证码已过期'}), 400

    # 从数据库获取目标位置
    target_pos = record['target_pos']
    tolerance = app.config['CAPTCHA_TOLERANCE']
    
    # 获取请求签名
    received_signature = request.headers.get('X-Captcha-Signature')
    
    # 使用数据库存储的目标位置生成签名
    expected_signature = generate_captcha_signature(data['verification_token'], target_pos)
    if not hmac.compare_digest(received_signature, expected_signature):
        return jsonify({'success': False, 'message': '签名验证失败'}), 400
    
    # 验证滑块位置
    if abs(data['position'] - target_pos) > tolerance:
        return jsonify({'success': False, 'message': '验证未通过'}), 400

    # 生成最终验证令牌（用于业务逻辑）
    final_token = secrets.token_urlsafe(32)
    
    # 清理已使用的验证数据
    db.execute(
        'DELETE FROM verification_tokens WHERE token = ?',
        (data['verification_token'],)
    )
    db.execute(
        'DELETE FROM captcha_data WHERE token = ?',
        (data['verification_token'],)
    )
    db.commit()
    
    return jsonify({
        'success': True,
        'final_token': final_token
    })

def verify_captcha_token(token):
    """验证一次性验证token"""
    db = get_db()
    # 从数据库验证最终令牌
    token_record = db.execute(
        'SELECT expires FROM verification_tokens WHERE token = ?',
        (token,)
    ).fetchone()

    if not token_record:
        return False

    # 检查过期时间
    now = datetime.now(pytz.UTC).timestamp()
    if now > token_record['expires']:
        db.execute(
            'DELETE FROM verification_tokens WHERE token = ?',
            (token,)
        )
        db.commit()
        return False

    # 验证后立即删除令牌
    db.execute(
        'DELETE FROM verification_tokens WHERE token = ?',
        (token,)
    )
    db.commit()
    return True


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
    with app.app_context():
        db = get_db()
        with open('schema.sql', 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        
        # 初始化验证码相关数据表
        init_captcha_tables()
        
        try:
            utc_now = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
            db.execute('INSERT INTO polls (question, created_at) VALUES (?, ?)', 
                      ['您最喜欢的编程语言是？', utc_now])
            poll_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            for option in ['Python', 'JavaScript', 'Java', 'C++']:
                db.execute('INSERT INTO options (poll_id, option_text) VALUES (?, ?)',
                          [poll_id, option])
            
            db.commit()
            print('数据库初始化完成')
        except Exception as e:
            db.rollback()
            print(f'初始化失败: {e}')

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
        verification_token = request.form.get('verification_token')

        if not verification_token or not verify_captcha_token(verification_token):
            flash('验证码验证失败，请重新完成验证')
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

# 临时调试路由
@app.route('/debug/db')
def debug_db():
    db = get_db()
    polls = db.execute('SELECT * FROM polls').fetchall()
    options = db.execute('SELECT * FROM options').fetchall()
    
    debug_info = {
        'polls': [dict(poll) for poll in polls],
        'options': [dict(opt) for opt in options]
    }
    return debug_info

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

if __name__ == '__main__':
    app.run(debug=True)
