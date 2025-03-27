# 简易投票系统

一个使用 Flask 和 SQLite 构建的轻量级投票系统。该系统允许用户创建投票、参与投票并实时查看投票结果。

## 功能特点

- 创建自定义投票
- 动态添加投票选项
- 实时投票结果显示
- 响应式设计，支持移动设备
- 使用 SQLite 数据库，无需复杂配置

## 技术栈

- **后端框架**: Flask
- **数据库**: SQLite
- **前端**: HTML5, CSS3, JavaScript
- **设计**: 响应式设计，现代UI

## 快速开始

### 前置要求

- Python 3.7+
- pip（Python包管理器）

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
2. 输入投票问题
3. 添加至少两个投票选项（可以点击"添加选项"添加更多）
4. 点击"创建投票"提交

### 参与投票

1. 在首页查看所有可用投票
2. 点击"参与投票"按钮
3. 选择一个选项
4. 点击"提交投票"

### 查看结果

- 投票后自动跳转到结果页面
- 可以通过首页的"查看结果"按钮查看任何投票的当前结果
- 结果页面显示：
  - 每个选项的得票数
  - 投票百分比
  - 可视化进度条
  - 总投票数

## 项目结构

```
vote/
├── app.py              # Flask应用主文件
├── schema.sql          # 数据库模式定义
├── requirements.txt    # 项目依赖
├── README.md          # 项目文档
├── static/
│   └── style.css      # 样式文件
└── templates/
    ├── base.html      # 基础模板
    ├── index.html     # 首页模板
    ├── create.html    # 创建投票页面
    ├── vote.html      # 投票页面
    └── results.html   # 结果页面
```

## 数据库结构

### polls 表
- `id`: INTEGER PRIMARY KEY
- `question`: TEXT
- `created_at`: TIMESTAMP

### options 表
- `id`: INTEGER PRIMARY KEY
- `poll_id`: INTEGER (外键关联到polls表)
- `option_text`: TEXT
- `votes`: INTEGER

## 开发说明

### 添加新功能

1. 在 `app.py` 中添加新的路由
2. 在 templates 目录中创建对应的模板
3. 根据需要更新数据库模式
4. 更新样式文件

### 代码风格

- 遵循 PEP 8 Python代码规范
- 使用有意义的变量和函数名
- 添加适当的注释
- 保持代码简洁清晰

## 安全考虑

- 数据库查询使用参数化语句防止SQL注入
- 表单提交包含CSRF保护
- 输入数据进行适当验证和清理
- 错误处理和日志记录

## 部署建议

### 开发环境
- 使用 Flask 内置服务器
- DEBUG 模式开启
- SQLite 数据库

### 生产环境
- 使用生产级Web服务器（如 Gunicorn）
- 配置反向代理（如 Nginx）
- 关闭 DEBUG 模式
- 配置适当的日志记录
- 考虑使用更强大的数据库（如 PostgreSQL）

## 维护和更新

- 定期更新依赖包
- 备份数据库
- 监控应用性能
- 处理用户反馈和bug报告

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