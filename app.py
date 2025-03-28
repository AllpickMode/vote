
import sqlite3
import logging
from datetime import datetime
import pytz
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, g, flash, abort
from functools import wraps

app = Flask(__name__)
app.config.update(
    DEBUG=False,
    SECRET_KEY='dev',
    DATABASE='votes.db'
)

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
        question = request.form['question'].strip()
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
        flash('您已经参与过这个投票了')
        return redirect(url_for('results', poll_id=poll_id))
    
    if request.method == 'POST':
        fingerprint = request.form.get('fingerprint')
        option_id = request.form.get('option')
        
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