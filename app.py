
import sqlite3
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, g, flash, abort, session

# 创建Flask应用
app = Flask(__name__)
app.config.update(
    DEBUG=False,
    SECRET_KEY='dev'  # 在生产环境中应该使用一个安全的随机密钥
)

# 配置日志记录
file_handler = RotatingFileHandler('app.log', maxBytes=1024 * 1024, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.ERROR)
app.logger.addHandler(file_handler)

# 数据库配置
DATABASE = 'votes.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        # 启用外键约束
        g.db.execute('PRAGMA foreign_keys = ON')
        # 启用自动提交
        g.db.isolation_level = 'DEFERRED'
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        
        # 添加测试数据
        try:
            # 添加一个测试投票
            db.execute('INSERT INTO polls (question) VALUES (?)', 
                      ['您最喜欢的编程语言是？'])
            poll_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            # 添加选项
            options = ['Python', 'JavaScript', 'Java', 'C++']
            for option in options:
                db.execute('INSERT INTO options (poll_id, option_text) VALUES (?, ?)',
                          [poll_id, option])
            
            db.commit()
            print('测试数据添加成功！')
        except Exception as e:
            db.rollback()
            print(f'添加测试数据失败: {str(e)}')

# 数据库操作异常处理
@app.after_request
def apply_caching(response):
    db = g.pop('db', None)
    if db is not None:
        try:
            if response.status_code >= 500:
                db.rollback()
            else:
                db.commit()
        except Exception as e:
            app.logger.error(f"数据库事务处理异常: {str(e)}", exc_info=True)
        finally:
            try:
                if db:
                    db.close()
            except Exception as e:
                app.logger.error(f"数据库关闭异常: {str(e)}", exc_info=True)
    return response

# 路由
@app.route('/')
def index():
    db = get_db()
    polls = db.execute('SELECT * FROM polls ORDER BY id DESC').fetchall()
    
    # 获取用户IP地址
    ip_address = request.remote_addr
    if request.headers.get('X-Forwarded-For'):
        ip_address = request.headers.get('X-Forwarded-For').split(',')[0]
    
    # 为每个投票检查用户是否已投票
    polls_with_status = []
    for poll in polls:
        # 检查是否在24小时内投过票
        last_vote = db.execute('''
            SELECT voted_at FROM vote_records 
            WHERE poll_id = ? AND ip_address = ?
            AND voted_at > datetime('now', '-1 day')
        ''', [poll['id'], ip_address]).fetchone()
        
        # 将投票信息和状态一起存储
        poll_info = dict(poll)
        poll_info['has_voted'] = last_vote is not None
        poll_info['vote_time'] = last_vote['voted_at'] if last_vote else None
        polls_with_status.append(poll_info)
    
    return render_template('index.html', polls=polls_with_status)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        question = request.form['question'].strip()
        options = [opt.strip() for opt in request.form.getlist('options[]') if opt.strip()]
        
        error = None
        if not question:
            error = '问题不能为空'
        elif len(options) < 2:
            error = '至少需要两个有效选项'
        
        if error is not None:
            flash(error)
            return render_template('create.html', question=question, options=options)
        
        db = get_db()
        cursor = db.cursor()
        
        try:
            # 插入投票问题
            cursor.execute('INSERT INTO polls (question) VALUES (?)', [question])
            poll_id = cursor.lastrowid
            
            # 插入选项
            for option in options:
                cursor.execute('INSERT INTO options (poll_id, option_text) VALUES (?, ?)',
                             [poll_id, option])
            
            db.commit()
            flash('投票创建成功！')
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            db.rollback()
            flash('创建投票失败，请稍后重试')
            return render_template('create.html', question=question, options=options)
    
    return render_template('create.html')

@app.route('/vote/<int:poll_id>', methods=['GET', 'POST'])
def vote(poll_id):
    db = get_db()
    poll = db.execute('SELECT * FROM polls WHERE id = ?', [poll_id]).fetchone()
    
    if poll is None:
        abort(404)
    
    options = db.execute('SELECT * FROM options WHERE poll_id = ?', [poll_id]).fetchall()
    if not options:
        abort(404)
    
    # 获取用户IP地址
    ip_address = request.remote_addr
    if request.headers.get('X-Forwarded-For'):
        ip_address = request.headers.get('X-Forwarded-For').split(',')[0]
    
    # 检查用户是否在24小时内已经投过票
    if request.method == 'POST':
        # POST请求时检查IP和指纹
        last_vote = db.execute('''
            SELECT voted_at FROM vote_records 
            WHERE poll_id = ? 
            AND (ip_address = ? OR browser_fingerprint = ?)
            AND voted_at > datetime('now', '-1 day')
            ORDER BY voted_at DESC LIMIT 1
        ''', [poll_id, ip_address, request.form.get('fingerprint', '')]).fetchone()
    else:
        # GET请求时只检查IP
        last_vote = db.execute('''
            SELECT voted_at FROM vote_records 
            WHERE poll_id = ? 
            AND ip_address = ?
            AND voted_at > datetime('now', '-1 day')
            ORDER BY voted_at DESC LIMIT 1
        ''', [poll_id, ip_address]).fetchone()
    
    has_voted = last_vote is not None
    
    if request.method == 'POST':
        if not request.form.get('fingerprint'):
            flash('无法验证浏览器指纹，请确保启用了JavaScript')
            return render_template('vote.html', poll=poll, options=options)
            
        if has_voted:
            flash('您在24小时内已经参与过这个投票了，请稍后再试')
            return redirect(url_for('results', poll_id=poll_id))
            
        option_id = request.form.get('option')
        if not option_id:
            flash('请选择一个选项')
            return render_template('vote.html', poll=poll, options=options)
        
        try:
            # 开始事务
            db.execute('BEGIN TRANSACTION')
            
            # 更新选项票数
            db.execute('UPDATE options SET votes = votes + 1 WHERE id = ? AND poll_id = ?', 
                      [option_id, poll_id])
            
            # 记录投票历史（包含浏览器指纹）
            db.execute('''
                INSERT INTO vote_records (poll_id, option_id, ip_address, browser_fingerprint)
                VALUES (?, ?, ?, ?)
            ''', [poll_id, option_id, ip_address, request.form.get('fingerprint')])
            
            db.commit()
            flash('投票成功！')
            return redirect(url_for('results', poll_id=poll_id))
        except Exception as e:
            db.rollback()
            flash('投票失败，请重试')
            return redirect(url_for('vote', poll_id=poll_id))
    
    return render_template('vote.html', poll=poll, options=options)

@app.route('/results/<int:poll_id>')
def results(poll_id):
    db = get_db()
    poll = db.execute('SELECT * FROM polls WHERE id = ?', [poll_id]).fetchone()
    
    if poll is None:
        abort(404)
    
    options = db.execute('SELECT * FROM options WHERE poll_id = ?', [poll_id]).fetchall()
    if not options:
        abort(404)
    
    return render_template('results.html', poll=poll, options=options)

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

# 错误处理
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'500 Error: {error}', exc_info=True)
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'未处理的异常: {str(e)}', exc_info=True)
    return render_template('500.html'), 500

# 添加命令行命令
@app.cli.command('init-db')
def init_db_command():
    """初始化数据库."""
    init_db()
    print('数据库初始化完成.')

if __name__ == '__main__':
    app.run(debug=True)