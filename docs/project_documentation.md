# 投票系统技术文档

## 1. 项目概述

这是一个使用 Flask 和 SQLite 构建的现代化轻量级投票系统。该系统提供了创建投票、参与投票和实时查看结果的功能，具有良好的安全性和用户体验。

### 1.1 核心特性

- 创建自定义投票
- 动态添加投票选项
- 实时投票结果显示
- 防重复投票机制
- 响应式设计
- 完整的错误处理
- 安全性保护

### 1.2 技术栈

- **后端框架**: Flask
- **数据库**: SQLite
- **前端**: HTML5, CSS3, JavaScript
- **安全**: CSRF 保护, 参数化查询
- **日志**: Rotating File Handler

## 2. 系统架构

### 2.1 目录结构

```
vote/
├── app.py              # Flask应用主文件
├── schema.sql          # 数据库模式定义
├── requirements.txt    # 项目依赖
├── static/            # 静态资源
│   ├── icons/        # 图标文件
│   └── style.css     # 样式文件
└── templates/         # HTML模板
    ├── base.html     # 基础模板
    ├── index.html    # 首页
    ├── create.html   # 创建投票
    ├── vote.html     # 投票页面
    ├── results.html  # 结果页面
    ├── 404.html      # 404错误页面
    └── 500.html      # 500错误页面
```

### 2.2 架构设计

- **MVC模式**
  - Model: SQLite数据库
  - View: Jinja2模板
  - Controller: Flask路由和视图函数

- **模块化设计**
  - 数据库操作封装
  - 错误处理中间件
  - CSRF保护
  - 日志系统

## 3. 数据库设计

### 3.1 表结构

#### polls 表 (投票表)
```sql
CREATE TABLE polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### options 表 (选项表)
```sql
CREATE TABLE options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    option_text TEXT NOT NULL,
    votes INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (poll_id) REFERENCES polls(id)
);
```

#### voter_ips 表 (投票记录表)
```sql
CREATE TABLE voter_ips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    country_code CHAR(2) NOT NULL,
    user_agent TEXT NOT NULL,
    is_vpn BOOLEAN DEFAULT 0,
    voted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    request_count INTEGER DEFAULT 1,
    block_until DATETIME,
    UNIQUE(poll_id, ip_address)
);
```

### 3.2 索引设计
- `idx_voter_ips_block`: 用于快速查询被封禁的IP
- `idx_voter_ips_country`: 用于按国家代码查询投票记录

## 4. 核心功能实现

### 4.1 投票创建流程

1. 验证输入数据
   - 问题不能为空
   - 至少需要两个有效选项
2. 事务处理
   - 创建投票记录
   - 添加选项记录
3. 错误处理
   - 数据库异常处理
   - 输入验证失败处理

### 4.2 投票处理流程

1. IP地址验证
   - 检查24小时内是否已投票
   - 支持代理服务器场景
2. 选项验证
   - 确保选项存在且有效
3. 事务处理
   - 更新投票计数
   - 记录投票IP信息
4. 防作弊机制
   - IP地址限制
   - 用户代理记录
   - 国家代码记录

### 4.3 结果显示

- 实时计算投票比例
- 支持动态刷新
- 可视化展示

## 5. 安全特性

### 5.1 CSRF保护
- 使用 Flask-WTF 实现CSRF令牌
- 所有POST请求都需要验证CSRF令牌

### 5.2 SQL注入防护
- 使用参数化查询
- 输入数据验证和清理

### 5.3 防重复投票
- IP地址追踪
- 时间限制（24小时）
- 地理位置记录

### 5.4 错误处理
- 自定义错误页面
- 详细日志记录
- 优雅的异常处理

## 6. 部署指南

### 6.1 环境要求
- Python 3.7+
- SQLite 3
- pip包管理器

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

## 7. 最佳实践

### 7.1 代码规范
- 遵循PEP 8规范
- 使用有意义的变量名
- 添加适当的注释
- 模块化和可维护性

### 7.2 性能优化
- 数据库索引优化
- 缓存策略
- 连接池管理
- 静态资源优化

### 7.3 安全建议
- 定期更新依赖包
- 监控异常访问
- 实施速率限制
- 数据备份策略

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