# 简易投票系统

一个使用 Flask 和 SQLite 构建的现代化轻量级投票系统。该系统提供直观的用户界面，支持实时投票和结果显示，适合小型到中型的在线投票需求。

## 功能特点

- **创建自定义投票**
  - 支持动态添加多个选项
  - 实时表单验证
  - CSRF 保护机制

- **投票参与**
  - 直观的单选界面
  - 防止重复投票（基于会话）
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

### 安装步骤

1. 克隆仓库：
```bash
git clone [repository-url]
cd vote
```

2. 创建并激活虚拟环境：
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 初始化数据库：
```python
python
>>> from app import init_db
>>> init_db()
>>> exit()
```

5. 运行应用：
```bash
python app.py
```

应用将在 http://localhost:5000 启动。

## 使用指南

### 创建投票

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

3. **会话管理**
   - 基于会话的重复投票预防
   - 安全的会话配置

4. **错误处理**
   - 优雅的错误页面
   - 详细的日志记录

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

## 许可证

MIT License

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 支持

如有问题或建议，请创建 issue 或联系维护者。

## 致谢

感谢所有为项目做出贡献的开发者。