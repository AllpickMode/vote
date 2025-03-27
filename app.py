import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g, flash, abort, session
from flask_wtf.csrf import CSRFProtect, generate_csrf

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'  # 在生产环境中应该使用一个安全的随机密钥
csrf = CSRFProtect(app)

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# 数据库配置
DATABASE = 'votes.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
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
        db.commit()

# 路由
@app.route('/')
def index():
    db = get_db()
    polls = db.execute('SELECT * FROM polls ORDER BY id DESC').fetchall()
    return render_template('index.html', polls=polls)

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
    last_vote = db.execute('''
        SELECT voted_at FROM vote_records 
        WHERE poll_id = ? AND ip_address = ? 
        AND voted_at > datetime('now', '-1 day')
        ORDER BY voted_at DESC LIMIT 1
    ''', [poll_id, ip_address]).fetchone()
    
    has_voted = last_vote is not None
    
    if request.method == 'POST':
        if has_voted:
            flash('您在24小时内已经参与过这个投票了，请稍后再试')
            return redirect(url_for('results', poll_id=poll_id))
            
        option_id = request.form.get('option')
        if not option_id:
            flash('请选择一个选项')
            return render_template('vote.html', poll=poll, options=options, has_voted=has_voted)
        
        try:
            # 开始事务
            db.execute('BEGIN TRANSACTION')
            
            # 更新选项票数
            db.execute('UPDATE options SET votes = votes + 1 WHERE id = ? AND poll_id = ?', 
                      [option_id, poll_id])
            
            # 记录投票历史
            db.execute('''
                INSERT INTO vote_records (poll_id, option_id, ip_address)
                VALUES (?, ?, ?)
            ''', [poll_id, option_id, ip_address])
            
            db.commit()
            flash('投票成功！')
            return redirect(url_for('results', poll_id=poll_id))
        except sqlite3.Error:
            db.rollback()
            flash('投票失败，请稍后重试')
    
    return render_template('vote.html', poll=poll, options=options, has_voted=has_voted)

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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)