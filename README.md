# 投票系统技术文档

一个使用 Flask 和 SQLite 构建的现代化轻量级投票系统。该系统提供直观的用户界面，支持实时投票和结果显示，适合小型到中型的在线投票需求。

这是一个使用 Flask 和 SQLite 构建的现代化轻量级投票系统。该系统提供了创建投票、参与投票和实时查看结果的功能，具有良好的安全性和用户体验。

### 1.1 核心特性

- **创建自定义投票**
  - 支持动态添加多个选项
  - 实时表单验证
  - CSRF 保护机制

- **投票参与**
  - 直观的单选界面
  - 防止重复投票（基于IP地址和时间限制）
  - 24小时投票限制
  - 实时提交反馈

- **结果展示**
  - 实时更新的投票统计
  - 动态进度条显示
  - 百分比和具体票数显示
  - 创建时间记录

- **用户界面**
  - 响应式设计，支持移动设备
  - 现代化 UI 设计
  - 平滑动画效果
  - 直观的导航系统

## 技术架构

### 后端技术
- **Web 框架**: Flask
- **数据库**: SQLite3
- **模板引擎**: Jinja2
- **会话管理**: Flask Session
- **安全**: Flask-WTF (CSRF 保护)

### 前端技术
- **样式**: 自定义 CSS3 (支持现代特性)
- **交互**: 原生 JavaScript
- **布局**: Flexbox 和 Grid
- **动画**: CSS3 Animations 和 Transitions
- **设计**: 响应式设计 + 移动优先

### 数据库结构

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
    voted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (poll_id) REFERENCES polls (id),
    FOREIGN KEY (option_id) REFERENCES options (id)
);

-- 优化索引
CREATE INDEX idx_vote_records_poll_ip ON vote_records(poll_id, ip_address);
CREATE INDEX idx_vote_records_time ON vote_records(voted_at);
```

## 文件结构

```
vote/
├── app.py              # Flask应用主文件
├── schema.sql          # 数据库模式定义
├── requirements.txt    # 项目依赖
├── README.md          # 项目文档
├── votes.db           # SQLite数据库文件
├── static/
│   ├── style.css      # 全局样式文件
│   └── icons/
│       └── vote-icon.svg  # 系统图标
└── templates/
    ├── base.html      # 基础模板
    ├── index.html     # 首页模板
    ├── create.html    # 创建投票页面
    ├── vote.html      # 投票页面
    ├── results.html   # 结果页面
    └── 404.html       # 错误页面
```

## 安装指南

### 系统要求
- Python 3.7+
- pip（Python包管理器）
- 虚拟环境（推荐）

### 6.2 安装步骤

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
```python
python
>>> from app import init_db
>>> init_db()
>>> exit()
```

### 6.3 生产环境配置

1. 安全配置
   - 设置安全的SECRET_KEY
   - 关闭DEBUG模式
   - 配置HTTPS

2. 服务器配置
   - 使用生产级Web服务器（如Gunicorn）
   - 配置反向代理（如Nginx）
   - 设置适当的访问控制

3. 监控和维护
   - 配置日志轮转
   - 定期数据库备份
   - 性能监控

1. 点击导航栏中的"创建投票"
2. 在表单中填写：
   - 投票问题（必填）
   - 至少两个投票选项（必填）
3. 可以通过"添加选项"按钮添加更多选项
4. 点击"创建投票"提交

### 参与投票

1. 在首页查看可用投票列表
2. 点击"参与投票"按钮
3. 选择一个选项
4. 点击"提交投票"确认

### 查看结果

- 投票后自动跳转到结果页面
- 可以通过首页的"查看结果"按钮查看任何投票的当前结果
- 结果页面显示：
  - 每个选项的得票数
  - 投票百分比
  - 动态进度条
  - 总投票数
  - 创建时间

## 开发指南

### 代码规范

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

### 添加新功能

1. 在 `app.py` 中添加新路由
2. 创建对应的模板文件
3. 更新数据库模式（如需要）
4. 添加必要的静态资源
5. 更新文档

## 安全特性

1. **CSRF 保护**
   - 所有表单都包含 CSRF 令牌
   - 使用 Flask-WTF 中间件

2. **输入验证**
   - 服务器端验证所有输入
   - 使用参数化 SQL 查询防止注入

3. **防重复投票机制**
   - 基于IP地址的投票追踪
   - 24小时投票时间限制
   - 支持代理服务器场景（X-Forwarded-For）
   - 使用数据库事务确保数据一致性
   - 优化的数据库索引提升查询性能

4. **错误处理**
   - 优雅的错误页面
   - 详细的日志记录

5. **数据完整性**
   - 使用外键约束确保数据关系完整性
   - 使用事务处理保证投票操作的原子性
   - 记录详细的投票历史用于审计

## 部署指南

### 开发环境
- 使用 Flask 内置服务器
- DEBUG 模式开启
- SQLite 数据库

### 生产环境建议
1. **Web 服务器**
   - 使用 Gunicorn 或 uWSGI
   - 配置 Nginx 反向代理
   - 启用 HTTPS

2. **数据库**
   - 考虑使用 PostgreSQL
   - 定期备份数据
   - 优化数据库配置

3. **安全设置**
   - 关闭 DEBUG 模式
   - 设置安全的 SECRET_KEY
   - 配置 CORS 策略

4. **监控**
   - 设置日志记录
   - 配置错误报告
   - 监控系统资源

## 维护指南

### 日常维护
1. 定期更新依赖包
2. 检查日志文件
3. 清理过期数据
4. 优化数据库

### 故障排除
1. 检查日志文件
2. 验证数据库连接
3. 确认文件权限
4. 测试网络连接

### 性能优化
1. 使用数据库索引
2. 实现缓存机制
3. 优化静态资源
4. 监控响应时间

## 8. 故障排除

### 8.1 常见问题
1. 数据库连接错误
   - 检查数据库文件权限
   - 验证连接字符串
   - 确保数据库未被锁定

2. 500内部服务器错误
   - 检查日志文件
   - 验证配置设置
   - 检查文件权限

3. 投票失败
   - 验证CSRF令牌
   - 检查IP限制
   - 确认数据库事务

### 8.2 日志分析
- 使用日志级别正确记录信息
- 定期检查错误日志
- 设置告警机制

## 9. 维护和更新

### 9.1 日常维护
- 监控系统性能
- 清理过期数据
- 更新安全补丁
- 备份重要数据

### 9.2 版本更新
- 遵循语义化版本控制
- 维护更新日志
- 进行充分测试
- 制定回滚计划

## 10. 结论

该投票系统采用现代化的技术栈和最佳实践，提供了安全、可靠的投票功能。通过合理的架构设计和严格的安全措施，确保了系统的稳定性和可靠性。系统的模块化设计也为未来的扩展和维护提供了便利。