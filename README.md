# 投票系统 (Vote System)

一个使用 Flask 和 SQLite 构建的现代化轻量级投票系统。该系统提供直观的用户界面，支持实时投票和结果显示，适合小型到中型的在线投票需求。

![投票系统界面预览](static/icons/vote-icon.svg)

## 快速开始

```bash
# 1. 克隆项目
git clone [项目地址]

# 2. 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
flask init-db

# 5. 运行应用
flask run
```

访问 http://localhost:5000 即可使用系统。

---

## 目录

- [核心特性](#核心特性)
- [技术架构](#技术架构)
- [详细文档](#详细文档)
- [安装部署](#安装部署)
- [使用指南](#使用指南)
- [开发指南](#开发指南)
- [维护指南](#维护指南)
- [故障排除](#故障排除)
- [改进计划](#改进计划)

---

## 核心特性

### 🎯 创建投票
- 支持动态添加多个选项
- 实时表单验证
- CSRF 保护机制
- 密码保护的创建功能

### 🗳️ 投票参与
- 直观的单选界面
- 双重防重复投票机制
- 滑块验证码防机器人
- 实时提交反馈

### 📊 结果展示
- 实时更新的投票统计
- 动态进度条显示
- 百分比和具体票数显示
- 本地时区时间显示

### 💻 用户界面
- 响应式设计，支持移动设备
- 现代化 UI 设计
- 平滑动画效果
- 直观的导航系统

---

## 技术架构

### 后端技术
- **Web 框架**: Flask 3.0.0
- **数据库**: SQLite3
- **模板引擎**: Jinja2 3.1.2
- **表单处理**: Flask-WTF 1.2.1
- **安全组件**: 
  - CSRF 保护
  - 滑块验证码
  - 验证码Token系统

### 前端技术
- **样式**: 自定义 CSS3
- **交互**: 原生 JavaScript
- **指纹识别**: FingerprintJS
- **布局**: Flexbox + Grid
- **设计**: 响应式 + 移动优先

### 数据库结构

```sql
-- 核心表结构
CREATE TABLE polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    option_text TEXT NOT NULL,
    votes INTEGER DEFAULT 0,
    FOREIGN KEY (poll_id) REFERENCES polls (id)
);

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
```

---

## 详细文档

完整的项目文档请查看 [docs/project_documentation.md](docs/project_documentation.md)，包含：

- 详细的安装说明
- API 文档
- 数据库设计
- 安全措施
- 部署指南
- 故障排除
- 开发指南

---

## 安装部署

### 系统要求
- Python 3.7+
- pip（Python包管理器）
- 现代浏览器（支持JavaScript）

### 生产环境配置要点

1. **安全配置**
   ```python
   # config.py
   SECRET_KEY = '生产环境密钥'
   DEBUG = False
   ```

2. **服务器配置**
   - 使用 Gunicorn/uWSGI
   - 配置 Nginx 反向代理
   - 启用 HTTPS

3. **监控配置**
   - 配置日志轮转
   - 设置错误报告
   - 监控系统资源

---

## 使用指南

### 创建投票
1. 访问首页，点击"创建投票"
2. 填写投票问题和选项
3. 设置创建密码
4. 提交创建

### 参与投票
1. 选择要参与的投票
2. 完成滑块验证
3. 选择投票选项
4. 提交投票

### 查看结果
- 投票后自动显示结果
- 可随时查看任何投票的实时结果

---

## 开发指南

### 代码规范
- 遵循 PEP 8
- 使用类型提示
- 编写单元测试
- 添加适当注释

### 添加新功能
1. 在 app.py 添加路由
2. 创建模板文件
3. 更新数据库（如需）
4. 添加测试用例
5. 更新文档

---

## 维护指南

### 日常维护
- 监控系统性能
- 清理过期日志
- 数据库备份
- 更新安全补丁

### 版本更新
- 遵循语义化版本
- 维护更新日志
- 执行自动化测试
- 准备回滚方案

---

## 故障排除

### 常见问题解决

1. **数据库错误**
   - 检查权限设置
   - 验证数据库完整性
   - 检查连接配置

2. **投票失败**
   - 验证会话状态
   - 检查JavaScript启用
   - 确认验证码完成

3. **500错误**
   - 查看错误日志
   - 检查配置文件
   - 验证文件权限

---

## 改进计划

### 近期计划 (1-2月)
- [ ] 优化验证码机制
- [ ] 实现IP黑名单
- [ ] 添加结果图表显示

### 中期计划 (2-4月)
- [ ] 实现实时更新
- [ ] 添加数据分析
- [ ] 优化移动端体验

### 长期计划 (4-6月)
- [ ] 实现多语言支持
- [ ] 添加高级统计
- [ ] 优化性能

---

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。请确保：

1. Fork 项目并创建特性分支
2. 遵循现有的代码风格
3. 编写测试用例
4. 更新相关文档

---

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至 [项目维护者邮箱]
- 访问项目主页 [项目URL]

---

*最后更新时间：2024年2月*