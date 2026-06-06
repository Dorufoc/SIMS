# 数据库初始化
- [x] init.sql 创建 student_manage 数据库，字符集 utf8，MySQL5.6标准
- [x] init.sql 创建 student_info 表，字段/类型/约束/注释与 PLAN.MD 完全一致（id INT PRIMARY KEY AUTO_INCREMENT NOT NULL / student_no VARCHAR(20) UNIQUE NOT NULL / student_name VARCHAR(30) NOT NULL / gender VARCHAR(6) DEFAULT NULL / age TINYINT DEFAULT NULL / major VARCHAR(50) DEFAULT NULL / grade VARCHAR(20) DEFAULT NULL / class_name VARCHAR(30) DEFAULT NULL / create_time DATETIME DEFAULT CURRENT_TIMESTAMP，ENGINE=InnoDB DEFAULT CHARSET=utf8）
- [x] init.sql 创建 user_info 表，字段/类型/约束/注释与 PLAN.MD 完全一致（uid INT PRIMARY KEY AUTO_INCREMENT / username VARCHAR(32) NOT NULL UNIQUE / password VARCHAR(64) NOT NULL / real_name VARCHAR(20) / role VARCHAR(10) DEFAULT 'user' / create_time DATETIME DEFAULT CURRENT_TIMESTAMP，ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='系统管理员账号表'）

# 后端基础设施
- [x] config.py 包含数据库连接配置（MySQL5.6主机/端口3306/用户名/密码/数据库名student_manage）和 Flask SECRET_KEY
- [x] db_utils.py 提供获取连接get_conn()、执行查询query()、执行增删改execute()工具方法
- [x] csv_handle.py 实现模板生成（内存生成标准表头CSV）、导入解析（跳过表头/空行/校验学号非空+年龄数字/学号重复跳过/事务BEGIN+COMMIT+ROLLBACK/批量INSERT多值语法）、导出生成（首行表头+逐行拼接+utf8编码）

# 用户认证模块
- [x] 注册功能：前端非空校验（用户名/密码/真实姓名），后端INSERT INTO user_info，捕获UNIQUE约束报错返回"账号已被注册"，成功跳转登录页
- [x] 登录功能：SELECT uid,username,role FROM user_info WHERE username=%s AND password=%s，成功写入session[user_id/user_name/user_role]，失败提示错误
- [x] 退出登录：清除session，重定向登录页
- [x] 全局登录拦截器：before_request钩子，未登录访问受保护路由自动重定向login.html

# 用户角色权限
- [x] user_info表含role字段（admin/user），管理员可增删改导入导出，只读用户仅查看和查询
- [x] 后端增删改导入路由校验session[user_role]，只读用户返回"权限不足"
- [x] 前端根据角色隐藏/禁用增删改导入按钮

# 学生CRUD模块
- [x] 学生新增：INSERT INTO student_info，学号UNIQUE冲突提示"学号已存在"
- [x] 学生列表展示：SELECT * FROM student_info LIMIT offset,10 分页显示（每页10条）
- [x] 学生编辑：UPDATE student_info SET ... WHERE id=%s
- [x] 学生删除：DELETE FROM student_info WHERE id=%s，删除前确认

# CSV导入导出模块
- [x] CSV模板下载：内存生成标准表头 `学号,姓名,性别,年龄,专业,年级,班级` 空CSV文件返回下载
- [x] CSV批量导入：跳过表头行+空行，学号为空/年龄非数字/学号重复标记异常跳过，合法数据INSERT VALUES(...),(...)批量插入，事务BEGIN/COMMIT/ROLLBACK，返回成功/失败条数
- [x] CSV前端文件类型限制：仅允许选择.csv后缀文件
- [x] CSV导入预览：上传后先展示预览表格，确认后再入库
- [x] CSV全量导出：SELECT student_no,student_name,gender,age,major,grade,class_name FROM student_info 生成CSV下载，utf8编码
- [x] CSV筛选导出：携带查询条件WHERE语句筛选后生成CSV下载
- [x] manage.html 包含导入导出操作区（下载模板/.csv上传控件/导入预览区/导出全部/导出筛选按钮），导航栏含退出登录按钮

# 高级查询模块
- [x] DDL关键字实训展示：CREATE DATABASE/DROP DATABASE/CREATE TABLE/DROP TABLE/ALTER TABLE/COMMENT/ENGINE/CHARSET（危险操作需二次确认）
- [x] DML关键字实训展示：INSERT/INSERT多值/UPDATE/DELETE/SELECT/FROM/WHERE
- [x] 条件筛选关键字预设查询：AND(计算机+2022年级)/OR(计算机或软件工程)/NOT(非计算机)/IS NULL(班级为空)/IS NOT NULL(年龄非空)/BETWEEN(18~22岁)/IN(多枚举专业)/NOT IN(排除专业)/LIKE(姓名含张)/%和_(通配符)
- [x] 聚合统计关键字预设查询：GROUP BY(按专业分组)/HAVING(人数>10)/COUNT(总人数+有年龄人数)/SUM(年龄总和)/AVG(各专业平均年龄)/MAX/MIN(各专业最大最小年龄)
- [x] 排序分页去重关键字预设查询：ORDER BY(学号升序/年龄降序)/ASC/DESC/LIMIT(分页0,10和10,10)/DISTINCT(不重复专业)
- [x] 运算符别名关键字预设查询：AS(字段别名)/=/>/</>=/<=（数值和字符串对比）
- [x] 事务约束关键字展示：PRIMARY KEY/AUTO_INCREMENT/UNIQUE/NOT NULL/DEFAULT/BEGIN/COMMIT/ROLLBACK（建表SQL约束定义+事务使用场景）

# 前端规范
- [x] 所有SQL语句兼容MySQL5.6，无8.0独有语法（窗口函数等）
- [x] 前端使用原生HTML+CSS+JavaScript/Ajax，无UI框架和第三方JS插件
- [x] 前端页面风格统一，布局清晰，操作直观
- [x] 项目目录结构与spec定义完全一致，无多余文件和空目录

# 项目结构规范化与命名规范
- [x] 目录结构完整：config.py/app.py/db_utils.py/csv_handle.py/static/css/style.css/static/js/main.js/templates(6个html)/sql/init.sql，无冗余文件和空目录
- [x] Python文件命名：snake_case（db_utils.py/csv_handle.py/config.py/app.py）
- [x] Python函数/方法命名：snake_case（get_conn()/parse_csv()/export_csv()）
- [x] Python变量命名：snake_case（student_no/class_name/page_size）
- [x] Python类命名：PascalCase
- [x] HTML文件命名：snake_case（add_stu.html/manage.html/query.html）
- [x] CSS类名命名：kebab-case（btn-primary/nav-header/table-data）
- [x] JS变量/函数命名：snake_case（handle_submit/page_size）
- [x] 路由URL命名：全小写+斜杠分隔（/add、/csv/import、/query/execute）
- [x] Flask路由函数命名：snake_case，与路由路径对应
- [x] 数据库表名/字段名命名：snake_case（student_info/user_info/student_no/create_time）
- [x] Python文件导入顺序：标准库→第三方库→本地模块，每组间空一行
- [x] 每个Python文件顶部有模块功能说明注释，每个函数有简要功能注释
- [x] 项目依赖仅为flask和pymysql，无其他第三方库（CSV使用内置csv标准库，会话使用Flask自带session）

# 测试
- [x] db_utils.py 单元测试通过（连接/查询/增删改）— 数据库不可用时正确skip
- [x] csv_handle.py 单元测试通过（模板生成/导入解析含空行+学号重复+年龄非数字+事务回滚/导出生成）— 8个测试全部通过
- [x] app.py 路由集成测试通过（注册含用户名重复+登录含成功失败+CRUD含学号重复+CSV导入导出+高级查询+角色权限拦截）— 数据库不可用时正确skip
