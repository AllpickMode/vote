import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g, flash, abort, session
from flask_wtf.csrf import CSRFProtect, generate_csrf

app = Flask(__name__)
app.config['DEBUG'] = False

# 配置日志记录
import logging
from logging.handlers import RotatingFileHandler

file_handler = RotatingFileHandler('app.log', maxBytes=1024 * 1024, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.ERROR)
app.logger.addHandler(file_handler)

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'500 Error: {error}', exc_info=True)
    return render_template('500.html'), 500

# 新增数据库操作异常处理
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

# 增强vote路由的异常处理
@app.route('/vote/<int:poll_id>', methods=['GET', 'POST'])
def vote(poll_id):
    try:
        db = get_db()
        poll = db.execute('SELECT * FROM polls WHERE id = ?', [poll_id]).fetchone()
        
        if poll is None:
            abort(404)
        
        options = db.execute('SELECT * FROM options WHERE poll_id = ?', [poll_id]).fetchall()
        if not options:
            abort(404)

        # （保持原有代码不变...）

        if request.method == 'POST':
            # 新增输入验证
            option_id = request.form.get('option')
            if not option_id or not option_id.isdigit():
                flash('无效的投票选项', 'error')
                return redirect(url_for('vote', poll_id=poll_id))

            # （保持原有代码不变，增加异常记录...）
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
        with app.open_resource('schema.sql', mode='r') as f:
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
    
    # 获取真实IP（支持代理）
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    
    # 检查是否已投票（24小时内）
    has_voted = db.execute(
        '''SELECT 1 FROM voter_ips 
        WHERE poll_id = ? 
        AND ip_address = ?
        AND timestamp >= datetime('now', '-24 hours')''',
        [poll_id, client_ip]
    ).fetchone() is not None
    
    if has_voted:
        flash('您已经投过票了', 'error')
        return redirect(url_for('results', poll_id=poll_id))
    
    if request.method == 'POST':
        # 检查IP是否已投票
        existing_vote = db.execute(
            'SELECT 1 FROM voter_ips WHERE poll_id = ? AND ip_address = ?',
            [poll_id, client_ip]
        ).fetchone()
        
        if existing_vote:
            flash('该IP地址已参与过本次投票', 'error')
            return redirect(url_for('results', poll_id=poll_id))
            
        option_id = request.form.get('option')
        if not option_id:
            flash('请选择一个选项', 'error')
            return render_template('vote.html', poll=poll, options=options, has_voted=has_voted)
        
            try:
                # 使用事务保证原子性操作
                with db:
                    # 验证选项是否存在
                    option_exists = db.execute(
                        'SELECT 1 FROM options WHERE id = ? AND poll_id = ?',
                        [option_id, poll_id]
                    ).fetchone()

                    if not option_exists:
                        flash('无效的投票选项', 'error')
                        return redirect(url_for('vote', poll_id=poll_id))
                    
                    # 更新投票数并记录IP（事务内操作）
                    db.execute('UPDATE options SET votes = votes + 1 WHERE id = ? AND poll_id = ?',
                              [option_id, poll_id])
                    # 记录IP地址和客户端信息（唯一约束检查）
                    country_code = request.headers.get('CF-IPCountry', 'XX')[:2]
                    user_agent = request.headers.get('User-Agent', '')[:500]
                    db.execute('INSERT INTO voter_ips (poll_id, ip_address, country_code, user_agent) VALUES (?, ?, ?, ?)',
                              [poll_id, client_ip, country_code, user_agent])
                
                flash('投票成功！', 'success')
                return redirect(url_for('results', poll_id=poll_id))
                
            except sqlite3.IntegrityError as e:
                app.logger.error(f'唯一约束冲突: {str(e)}')
                flash('同一IP地址不能重复投票', 'error')
                return redirect(url_for('results', poll_id=poll_id))
                
            except sqlite3.Error as e:
                app.logger.error(f'数据库错误: {str(e)}')
                flash('投票处理失败，请稍后重试', 'error')
                return redirect(url_for('vote', poll_id=poll_id))

                    if not option_exists:
                        flash('无效的投票选项', 'error')
                        return redirect(url_for('vote', poll_id=poll_id))
                    
                    # 更新投票数并记录IP（事务内操作）
                    db.execute('UPDATE options SET votes = votes + 1 WHERE id = ? AND poll_id = ?',
                              [option_id, poll_id])
                    # 记录IP地址和客户端信息（唯一约束检查）
                    country_code = request.headers.get('CF-IPCountry', 'XX')[:2]
                    user_agent = request.headers.get('User-Agent', '')[:500]
                    db.execute('INSERT INTO voter_ips (poll_id, ip_address, country_code, user_agent) VALUES (?, ?, ?, ?)',
                              [poll_id, client_ip, country_code, user_agent])
                
                flash('投票成功！', 'success')
                return redirect(url_for('results', poll_id=poll_id))
                
            except sqlite3.IntegrityError as e:
                app.logger.error(f'唯一约束冲突: {str(e)}')
                flash('同一IP地址不能重复投票', 'error')
                return redirect(url_for('results', poll_id=poll_id))
                
            except sqlite3.Error as e:
                app.logger.error(f'数据库错误: {str(e)}')
                flash('投票处理失败，请稍后重试', 'error')
                return redirect(url_for('vote', poll_id=poll_id))

                    if not option_exists:
                        flash('无效的投票选项', 'error')
                        return redirect(url_for('vote', poll_id=poll_id))
                    
                    # 更新投票数并记录IP（事务内操作）
                    db.execute('UPDATE options SET votes = votes + 1 WHERE id = ? AND poll_id = ?',
                              [option_id, poll_id])
                    # 记录IP地址和客户端信息（唯一约束检查）
                    country_code = request.headers.get('CF-IPCountry', 'XX')[:2]
                    user_agent = request.headers.get('User-Agent', '')[:500]
                    db.execute('INSERT INTO voter_ips (poll_id, ip_address, country_code, user_agent) VALUES (?, ?, ?, ?)',
                              [poll_id, client_ip, country_code, user_agent])
                
                flash('投票成功！', 'success')
                return redirect(url_for('results', poll_id=poll_id))
                
            except sqlite3.IntegrityError as e:
                app.logger.error(f'唯一约束冲突: {str(e)}')
                flash('同一IP地址不能重复投票', 'error')
                return redirect(url_for('results', poll_id=poll_id))
                
            except sqlite3.Error as e:
                app.logger.error(f'数据库错误: {str(e)}')
                flash('投票处理失败，请稍后重试', 'error')
                return redirect(url_for('vote', poll_id=poll_id))

                    if not option_exists:
                        flash('无效的投票选项', 'error')
                        return redirect(url_for('vote', poll_id=poll_id))
                    
                    # 更新投票数并记录IP（事务内操作）
                    db.execute('UPDATE options SET votes = votes + 1 WHERE id = ? AND poll_id = ?',
                              [option_id, poll_id])
                    # 记录IP地址和客户端信息（唯一约束检查）
                    country_code = request.headers.get('CF-IPCountry', 'XX')[:2]
                    user_agent = request.headers.get('User-Agent', '')[:500]
                    db.execute('INSERT INTO voter_ips (poll_id, ip_address, country_code, user_agent) VALUES (?, ?, ?, ?)',
                              [poll_id, client_ip, country_code, user_agent])
                
                flash('投票成功！', 'success')
                return redirect(url_for('results', poll_id=poll_id))
                
            except sqlite3.IntegrityError as e:
                app.logger.error(f'唯一约束冲突: {str(e)}')
                flash('同一IP地址不能重复投票', 'error')
                return redirect(url_for('results', poll_id=poll_id))
                
            except sqlite3.Error as e:
                app.logger.error(f'数据库错误: {str(e)}')
                flash('投票处理失败，请稍后重试', 'error')
                return redirect(url_for('vote', poll_id=poll_id))
                    
                    if not option_exists:
                        flash('无效的投票选项', 'error')
                        return redirect(url_for('vote', poll_id=poll_id))
                    
                    # 更新投票数并记录IP（事务内操作）
                    db.execute('UPDATE options SET votes = votes + 1 WHERE id = ? AND poll_id = ?',
                              [option_id, poll_id])
                    # 记录IP地址和客户端信息（唯一约束检查）
                    country_code = request.headers.get('CF-IPCountry', 'XX')[:2]
                    user_agent = request.headers.get('User-Agent', '')[:500]
                    db.execute('INSERT INTO voter_ips (poll_id, ip_address, country_code, user_agent) VALUES (?, ?, ?, ?)',
                              [poll_id, client_ip, country_code, user_agent])
                
                flash('投票成功！', 'success')
                return redirect(url_for('results', poll_id=poll_id))
                
            except sqlite3.IntegrityError as e:
                app.logger.error(f'唯一约束冲突: {str(e)}')
                flash('同一IP地址不能重复投票', 'error')
                return redirect(url_for('results', poll_id=poll_id))
                
            except sqlite3.Error as e:
                app.logger.error(f'数据库错误: {str(e)}')
                flash('投票处理失败，请稍后重试', 'error')
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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# 配置日志记录
import logging
from logging.handlers import RotatingFileHandler

# 创建日志记录器
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.WARNING)
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
app.logger.addHandler(handler)

# 全局异常处理
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'未处理的异常: {str(e)}', exc_info=True)
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=False)
