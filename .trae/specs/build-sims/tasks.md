# Tasks

- [x] Task 1: 创建数据库初始化脚本 sql/init.sql
  - [x] 1.1: 创建 student_manage 数据库（utf8编码，MySQL5.6标准）
  - [x] 1.2: 创建 student_info 表（id INT PRIMARY KEY AUTO_INCREMENT NOT NULL / student_no VARCHAR(20) UNIQUE NOT NULL / student_name VARCHAR(30) NOT NULL / gender VARCHAR(6) DEFAULT NULL / age TINYINT DEFAULT NULL / major VARCHAR(50) DEFAULT NULL / grade VARCHAR(20) DEFAULT NULL / class_name VARCHAR(30) DEFAULT NULL / create_time DATETIME DEFAULT CURRENT_TIMESTAMP，含全部COMMENT注释，ENGINE=InnoDB DEFAULT CHARSET=utf8）
  - [x] 1.3: 创建 user_info 表（uid INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户主键' / username VARCHAR(32) NOT NULL UNIQUE COMMENT '登录账号' / password VARCHAR(64) NOT NULL COMMENT '登录密码' / real_name VARCHAR(20) COMMENT '管理员姓名' / role VARCHAR(10) DEFAULT 'user' COMMENT '角色：admin/user' / create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '账号创建时间'，ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='系统管理员账号表'）

- [x] Task 2: 创建后端基础设施
  - [x] 2.1: 创建 config.py（数据库连接配置：MySQL5.6地址/端口3306/账号/密码/数据库名student_manage，Flask SECRET_KEY密钥配置）
  - [x] 2.2: 创建 db_utils.py（数据库连接工具类：获取连接get_conn()、执行查询query()、执行增删改execute()，用户/学生两张表通用连接）
  - [x] 2.3: 创建 csv_handle.py（CSV模板生成generate_template()：内存生成标准表头CSV；导入解析parse_csv()：跳过表头/空行/校验/事务批量INSERT；导出生成export_csv()：首行表头+逐行拼接数据流）

- [x] Task 3: 实现用户认证模块（app.py路由 + 前端页面）
  - [x] 3.1: 实现注册路由 /register（GET返回register.html，POST处理注册逻辑：INSERT INTO user_info，捕获UNIQUE约束报错返回"账号已被注册"，成功跳转登录页）
  - [x] 3.2: 实现登录路由 /login（GET返回login.html，POST校验：SELECT uid,username,role FROM user_info WHERE username=%s AND password=%s，成功写入session[user_id/user_name/user_role]，失败提示错误）
  - [x] 3.3: 实现退出路由 /logout（清除session，重定向登录页）
  - [x] 3.4: 实现全局登录拦截器（before_request钩子，除/login//register/静态资源外所有路由校验session，失效重定向login.html）
  - [x] 3.5: 创建 templates/login.html（登录页面：账号密码输入框+登录按钮+注册链接，原生HTML/CSS/JS，Ajax提交）
  - [x] 3.6: 创建 templates/register.html（注册页面：用户名/密码/真实姓名输入框+注册按钮+登录链接，前端非空校验，原生HTML/CSS/JS，Ajax提交）

- [x] Task 4: 实现学生信息CRUD模块（app.py路由 + 前端页面）
  - [x] 4.1: 实现首页路由 /（展示系统入口，导航至各功能模块）
  - [x] 4.2: 实现新增路由 /add（GET返回add_stu.html，POST处理：INSERT INTO student_info，学号UNIQUE冲突提示"学号已存在"）
  - [x] 4.3: 实现管理路由 /manage（GET展示学生列表：SELECT * FROM student_info LIMIT offset,10，支持分页参数page）
  - [x] 4.4: 实现编辑路由 /edit/<id>（GET返回编辑页面填充原数据，POST执行：UPDATE student_info SET ... WHERE id=%s）
  - [x] 4.5: 实现删除路由 /delete/<id>（POST执行：DELETE FROM student_info WHERE id=%s）
  - [x] 4.6: 创建 templates/index.html（系统首页：导航链接至管理/新增/查询/退出登录）
  - [x] 4.7: 创建 templates/add_stu.html（单条新增页面：学号/姓名/性别/年龄/专业/年级/班级输入框，Ajax提交）
  - [x] 4.8: 创建 templates/manage.html（数据管理页面：导航栏含退出登录按钮，学生数据表格+分页，操作区含下载模板/上传导入/导出全部/导出筛选按钮，编辑/删除操作列）

- [x] Task 5: 实现CSV批量导入导出模块
  - [x] 5.1: 实现模板下载路由 /csv/template（内存生成标准表头 `学号,姓名,性别,年龄,专业,年级,班级` CSV，返回浏览器下载）
  - [x] 5.2: 实现CSV上传导入路由 /csv/import（读取CSV→跳过表头行→跳过空行→校验学号非空/年龄数字→学号重复跳过→合法数据批量INSERT VALUES(...),(...)/事务BEGIN/COMMIT/ROLLBACK→返回成功/失败条数）
  - [x] 5.3: 实现CSV导入预览路由 /csv/preview（上传CSV解析返回JSON预览数据，前端展示表格，用户确认后调用/csv/import执行导入）
  - [x] 5.4: 实现全量导出路由 /csv/export（SELECT student_no,student_name,gender,age,major,grade,class_name FROM student_info→生成CSV下载，utf8编码）
  - [x] 5.5: 实现筛选导出路由 /csv/export_filtered（携带查询条件WHERE语句筛选后生成CSV下载）
  - [x] 5.6: manage.html 中添加导入导出操作区（下载模板按钮、.csv文件上传控件含类型限制、导入预览区、导出全部/导出筛选按钮）

- [x] Task 6: 实现高级查询模块
  - [x] 6.1: 实现高级查询路由 /query（GET返回query.html）
  - [x] 6.2: 实现查询执行路由 /query/execute（POST接收查询条件，构建SQL执行返回JSON结果）
  - [x] 6.3: 创建 templates/query.html（高级查询页面：DDL实训区+DML实训区+条件筛选区+聚合统计区+排序分页区+事务约束展示区+预设查询按钮+导出筛选数据按钮）
  - [x] 6.4: 实现DDL关键字实训展示（CREATE DATABASE/DROP DATABASE/CREATE TABLE/DROP TABLE/ALTER TABLE/COMMENT/ENGINE/CHARSET，危险操作需二次确认）
  - [x] 6.5: 实现DML关键字实训展示（INSERT/INSERT多值/UPDATE/DELETE/SELECT/FROM/WHERE，展示对应SQL和执行结果）
  - [x] 6.6: 实现条件筛选关键字预设查询（AND/OR/NOT/IS NULL/IS NOT NULL/BETWEEN/IN/NOT IN/LIKE/%/_，每个关键字绑定PLAN.MD规定的业务场景）
  - [x] 6.7: 实现聚合统计关键字预设查询（GROUP BY/HAVING/COUNT/SUM/AVG/MAX/MIN，每个关键字绑定PLAN.MD规定的业务场景）
  - [x] 6.8: 实现排序分页去重关键字预设查询（ORDER BY/ASC/DESC/LIMIT/DISTINCT）
  - [x] 6.9: 实现运算符别名关键字预设查询（AS/=/>/</>=/<=，数值和字符串对比）
  - [x] 6.10: 实现事务约束关键字展示（PRIMARY KEY/AUTO_INCREMENT/UNIQUE/NOT NULL/DEFAULT/BEGIN/COMMIT/ROLLBACK，展示建表SQL中的约束定义和事务使用场景）

- [x] Task 7: 实现用户角色权限控制
  - [x] 7.1: 在增删改导入路由中增加角色校验，session[user_role]='user'时拒绝操作返回"权限不足"
  - [x] 7.2: 前端根据角色隐藏/禁用增删改导入按钮（只读用户仅显示查看和查询功能）

- [x] Task 8: 创建前端静态资源（严格遵循命名规范：CSS类名kebab-case、JS变量函数snake_case）
  - [x] 8.1: 创建 static/css/style.css（全局样式：简洁克制风格，统一配色/字体/间距/表格样式/按钮样式/表单样式，CSS类名使用kebab-case如btn-primary/nav-header/table-data）
  - [x] 8.2: 创建 static/js/main.js（全局Ajax工具函数、页面交互逻辑、分页逻辑、文件上传逻辑、导入预览逻辑，JS变量函数使用snake_case如handle_submit/page_size）

- [x] Task 9: 编写测试
  - [x] 9.1: 编写 db_utils.py 单元测试（数据库连接、查询、增删改）
  - [x] 9.2: 编写 csv_handle.py 单元测试（模板生成、导入解析含空行/学号重复/年龄非数字/事务回滚、导出生成）
  - [x] 9.3: 编写 app.py 路由集成测试（注册含用户名重复、登录含成功失败、CRUD含学号重复、CSV导入导出、高级查询、角色权限拦截）

- [x] Task 10: 项目结构规范化验证
  - [x] 10.1: 验证目录结构与spec定义完全一致，无多余文件和空目录
  - [x] 10.2: 验证所有Python文件/函数/变量命名符合snake_case规范，类名符合PascalCase规范
  - [x] 10.3: 验证所有HTML文件命名符合snake_case规范，CSS类名符合kebab-case规范
  - [x] 10.4: 验证所有路由URL和Flask路由函数命名规范一致
  - [x] 10.5: 验证Python文件导入顺序规范（标准库→第三方库→本地模块）
  - [x] 10.6: 验证每个Python文件顶部有模块功能说明注释，每个函数有简要功能注释
  - [x] 10.7: 验证项目依赖仅为flask和pymysql，无其他第三方库

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 2]
- [Task 5] depends on [Task 2, Task 4]
- [Task 6] depends on [Task 2]
- [Task 7] depends on [Task 3, Task 4]
- [Task 8] depends on [Task 3, Task 4, Task 5, Task 6]
- [Task 9] depends on [Task 1, Task 2, Task 3, Task 4, Task 5, Task 6, Task 7]
- [Task 10] depends on [Task 1, Task 2, Task 3, Task 4, Task 5, Task 6, Task 7, Task 8, Task 9]
