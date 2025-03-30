# 投票系统技术文档

一个使用 Flask 和 SQLite 构建的现代化轻量级投票系统。该系统提供直观的用户界面，支持实时投票和结果显示，适合小型到中型的在线投票需求。

## 1. 核心特性

- **创建自定义投票**
  - 支持动态添加多个选项
  - 实时表单验证
  - CSRF 保护机制
  - 密码保护的创建功能

- **投票参与**
  - 直观的单选界面
  - 双重防重复投票机制（IP地址 + 浏览器指纹）
  - 滑块验证码防机器人
  - 实时提交反馈

- **结果展示**
  - 实时更新的投票统计
  - 动态进度条显示
  - 百分比和具体票数显示
  - 创建时间记录（支持本地时区显示）

- **用户界面**
  - 响应式设计，支持移动设备
  - 现代化 UI 设计
  - 平滑动画效果
  - 直观的导航系统

## 2. 技术架构

### 2.1 后端技术
- **Web 框架**: Flask
- **数据库**: SQLite3
- **模板引擎**: Jinja2
- **会话管理**: Flask Session
- **安全**: 
  - Flask-WTF (CSRF 保护)
  - 滑块验证码
  - 验证码Token系统
- **时区处理**: pytz
- **日志系统**: RotatingFileHandler

### 2.2 前端技术
- **样式**: 自定义 CSS3 (支持现代特性)
- **交互**: 原生 JavaScript
- **指纹识别**: FingerprintJS
- **验证码**: 自定义滑块验证
- **布局**: Flexbox 和 Grid
- **动画**: CSS3 Animations 和 Transitions
- **设计**: 响应式设计 + 移动优先

### 2.3 数据库结构

#### polls 表
```sql
CREATE TABLE polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### options 表
```sql
CREATE TABLE options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    option_text TEXT NOT NULL,
    votes INTEGER DEFAULT 0,
    FOREIGN KEY (poll_id) REFERENCES polls (id)
);
```

#### vote_records 表
```sql
CREATE TABLE vote_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    option_id INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    browser_fingerprint TEXT NOT NULL,
    voted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (poll_id) REFERENCES polls (id),
    FOREIGN KEY (option_id) REFERENCES options (id)
);

-- 优化索引
CREATE INDEX idx_vote_records_poll_ip ON vote_records(poll_id, ip_address);
CREATE INDEX idx_vote_records_fingerprint ON vote_records(poll_id, browser_fingerprint);
CREATE INDEX idx_vote_records_time ON vote_records(voted_at);
```

## 3. 文件结构

```
vote/
├── app.py              # Flask应用主文件
├── schema.sql          # 数据库模式定义
├── requirements.txt    # 项目依赖
├── README.md          # 项目文档
├── votes.db           # SQLite数据库文件
├── app.log            # 应用日志文件
├── static/
│   ├── style.css      # 全局样式文件
│   ├── css/
│   │   └── slider-captcha.css  # 滑块验证码样式
│   ├── js/
│   │   └── slider-captcha.js   # 滑块验证码脚本
│   └── icons/
│       └── vote-icon.svg       # 系统图标
└── templates/
    ├── base.html      # 基础模板
    ├── index.html     # 首页模板
    ├── create.html    # 创建投票页面
    ├── vote.html      # 投票页面
    ├── results.html   # 结果页面
    ├── 404.html       # 404错误页面
    └── 500.html       # 500错误页面
```

## 4. 安装指南

### 4.1 系统要求
- Python 3.7+
- pip（Python包管理器）
- 虚拟环境（推荐）
- 现代浏览器（支持JavaScript）

### 4.1.1 主要依赖版本
- Flask 3.0.0
- Flask-WTF 1.2.1
- Werkzeug 3.0.1
- Jinja2 3.1.2
- pytz 2024.1
- WTForms 3.1.1

### 4.2 安装步骤

1. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 初始化数据库：
```bash
flask init-db
```

### 4.3 生产环境配置

1. 安全配置
   - 设置安全的SECRET_KEY
   - 关闭DEBUG模式
   - 配置HTTPS
   - 设置创建投票密码

2. 服务器配置
   - 使用生产级Web服务器（如Gunicorn）
   - 配置反向代理（如Nginx）
   - 设置适当的访问控制
   - 配置时区（默认Asia/Shanghai）

3. 监控和维护
   - 配置日志轮转（已内置）
   - 定期数据库备份
   - 性能监控

## 5. 使用指南

### 5.1 创建投票

1. 点击导航栏中的"创建投票"
2. 在表单中填写：
   - 投票问题（必填）
   - 至少两个投票选项（必填）
   - 创建密码（必填）
3. 可以通过"添加选项"按钮添加更多选项
4. 点击"创建投票"提交

### 5.2 参与投票

1. 在首页查看可用投票列表
2. 点击"参与投票"按钮
3. 完成滑块验证码验证
4. 选择一个选项
5. 确保启用JavaScript（用于浏览器指纹识别）
6. 点击"提交投票"确认

### 5.3 查看结果

- 投票后自动跳转到结果页面
- 可以通过首页的"查看结果"按钮查看任何投票的当前结果
- 结果页面显示：
  - 每个选项的得票数
  - 投票百分比
  - 动态进度条
  - 总投票数
  - 创建时间（本地时区）

## 6. 开发指南

### 6.1 代码规范

1. **Python 代码规范**
   - 遵循 PEP 8 规范
   - 使用有意义的变量和函数名
   - 添加适当的注释
   - 使用类型提示（Python 3.7+）

2. **HTML/CSS 规范**
   - 使用语义化标签
   - 保持 CSS 类名的一致性
   - 遵循 BEM 命名约定
   - 优先使用 CSS Grid 和 Flexbox 布局

3. **JavaScript 规范**
   - 使用 ES6+ 特性
   - 避免全局变量
   - 使用事件委托优化性能
   - 确保浏览器指纹和验证码功能的可靠性

### 6.2 添加新功能

1. 在 `app.py` 中添加新路由
2. 创建对应的模板文件
3. 更新数据库模式（如需要）
4. 添加必要的静态资源
5. 更新文档

## 7. 安全特性

### 7.1 基础安全措施

1. **CSRF 保护**
   - 所有表单都包含 CSRF 令牌
   - 使用 Flask-WTF 中间件

2. **输入验证**
   - 服务器端验证所有输入
   - 使用参数化 SQL 查询防止注入
   - 滑块验证码防机器人

3. **创建保护**
   - 密码保护的投票创建功能
   - 验证码token系统

### 7.2 防重复投票机制

- 双重验证：IP地址 + 浏览器指纹
- 滑块验证码验证
- 支持代理服务器场景（X-Forwarded-For）
- 使用数据库事务确保数据一致性
- 优化的数据库索引提升查询性能

### 7.3 其他安全特性

- 优雅的错误处理
- 详细的日志记录（使用RotatingFileHandler）
- 数据完整性保护（外键约束）
- 使用事务处理保证操作原子性
- UTC时间存储，本地时间显示

## 8. 部署指南

### 8.1 开发环境
- 使用 Flask 内置服务器
- DEBUG 模式开启
- SQLite 数据库
- 日志详细记录

### 8.2 生产环境配置
1. **Web 服务器**
   - 使用 Gunicorn 或 uWSGI
   - 配置 Nginx 反向代理
   - 启用 HTTPS

2. **数据库**
   - 使用 SQLite（适合中小型部署）
   - 定期备份数据
   - 启用外键约束
   - 优化索引配置

3. **安全设置**
   - 关闭 DEBUG 模式
   - 设置安全的 SECRET_KEY
   - 配置 CORS 策略
   - 设置安全的创建密码

4. **监控**
   - 配置日志轮转
   - 设置错误报告
   - 监控系统资源

## 9. 故障排除

### 9.1 常见问题

1. **数据库连接错误**
   - 检查数据库文件权限
   - 验证外键约束设置
   - 确保数据库未被锁定

2. **500内部服务器错误**
   - 检查轮转日志文件
   - 验证配置设置
   - 检查文件权限

3. **投票失败**
   - 验证CSRF令牌
   - 检查JavaScript是否启用
   - 验证滑块验证码是否完成
   - 验证浏览器指纹是否正确生成
   - 检查IP和指纹限制
   - 确认数据库事务

### 9.2 日志分析
- 使用日志级别正确记录信息
- 定期检查轮转日志
- 设置告警机制
- 监控错误模式

## 10. 维护和更新

### 10.1 日常维护
- 监控系统性能
- 清理过期日志
- 更新安全补丁
- 备份数据库
- 检查日志轮转

### 10.2 版本更新
- 遵循语义化版本控制
- 维护更新日志
- 进行充分测试
- 制定回滚计划

## 11. 改进建议

### 11.1 高优先级（安全相关）

1. **安全性增强**
   - 实现验证码难度动态调整
   - 添加IP黑名单机制
   - 实现投票选项随机排序
   - 加强密码策略
   - 添加API访问限制

2. **核心功能完善**
   - 实现投票时间限制
   - 添加投票编辑功能
   - 实现管理员功能
   - 添加数据导出功能
   - 实现投票模板功能

### 11.2 中优先级（性能优化）

1. **性能优化**
   - 实现结果缓存机制
   - 优化数据库查询
   - 添加结果分页功能
   - 实现异步投票统计
   - 优化前端资源加载

2. **代码架构优化**
   - 实现模块化路由
   - 添加配置文件
   - 完善单元测试
   - 优化错误处理
   - 增强日志系统

### 11.3 低优先级（功能优化）

1. **用户体验提升**
   - 添加结果图表
   - 实现实时更新
   - 优化移动端验证码
   - 添加分享功能
   - 实现多语言支持

2. **其他改进**
   - 添加投票分类
   - 实现用户反馈
   - 添加数据分析
   - 优化时区处理
   - 实现备份恢复

### 11.4 实施计划

1. **第一阶段（1-2周）**
   - 优化验证码机制
   - 实现IP黑名单
   - 加强密码保护

2. **第二阶段（2-4周）**
   - 实现结果缓存
   - 添加分页功能
   - 优化查询性能

3. **第三阶段（4-6周）**
   - 添加图表显示
   - 实现实时更新
   - 优化移动端体验