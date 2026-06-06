# 学生信息管理与查询系统 Spec

## Why

基于 PLAN.MD 开发计划，构建一个功能完整的学生信息管理系统，覆盖用户注册登录、学生CRUD、CSV批量导入导出、高级查询等全部功能，严格兼容 MySQL5.6，满足本科数据库实训全覆盖要求。

## What Changes

* 新增数据库初始化SQL脚本（student\_info + user\_info 双表，MySQL5.6兼容）

* 新增后端 Flask 应用：config.py、app.py、db\_utils.py、csv\_handle.py

* 新增前端页面：login.html、register.html、index.html、add\_stu.html、manage.html、query.html

* 新增前端静态资源：CSS样式、JS交互逻辑

* 实现用户注册/登录/退出/会话拦截

* 实现学生信息单条增删改查

* 实现 CSV 模板下载、批量导入（含事务+容错）、批量导出（全量+筛选）

* 实现高级查询页面，覆盖本科 MySQL 全部关键字场景（DDL/DML/条件筛选/聚合统计/排序分页/运算符别名/事务约束共七大类）

* 实现DDL拓展实训功能（DROP DATABASE后台隐藏、DROP TABLE清空测试表、ALTER TABLE新增/修改字段）

* 实现拓展实训方向（用户角色权限、CSV导入预览）

## Impact

* Affected code: 全新项目，无已有代码影响

* 数据库：需 MySQL5.6 实例，创建 student\_manage 库及双表

## ADDED Requirements

### Requirement: 数据库初始化

系统 SHALL 提供 init.sql 脚本，创建 student\_manage 数据库（utf8编码，MySQL5.6标准），包含 student\_info 和 user\_info 两张表，所有字段类型、约束、注释严格遵循 PLAN.MD 定义。user\_info 表需包含 role 字段（默认值'user'）用于角色权限。

#### Scenario: 初始化数据库

* **WHEN** 执行 init.sql

* **THEN** 创建 student\_manage 数据库，student\_info 表含 id/student\_no/student\_name/gender/age/major/grade/class\_name/create\_time 字段（含全部约束：PRIMARY KEY/AUTO\_INCREMENT/UNIQUE/NOT NULL/DEFAULT/COMMENT），user\_info 表含 uid/username/password/real\_name/role/create\_time 字段（含全部约束），ENGINE=InnoDB DEFAULT CHARSET=utf8

### Requirement: 用户注册

系统 SHALL 提供注册页面，用户输入用户名、密码、真实姓名完成注册。前端进行简单非空校验（用户名/密码/真实姓名均不可为空）。用户名唯一，重复时提示"账号已被注册"。

#### Scenario: 注册成功

* **WHEN** 用户填写不重复的用户名、密码、真实姓名并提交

* **THEN** 执行 INSERT INTO user\_info(...) VALUES(...)，数据写入 user\_info 表，跳转登录页

#### Scenario: 用户名重复

* **WHEN** 用户填写已存在的用户名提交

* **THEN** 捕获UNIQUE约束报错，返回"账号已被注册"，不写入数据库

#### Scenario: 前端非空校验

* **WHEN** 用户未填写用户名或密码或真实姓名就提交

* **THEN** 前端拦截提交，提示必填项不能为空

### Requirement: 用户登录

系统 SHALL 提供登录页面，校验账号密码。SQL：SELECT uid,username,role FROM user\_info WHERE username=%s AND password=%s。成功后写入 session（user\_id/user\_name/user\_role），跳转首页。

#### Scenario: 登录成功

* **WHEN** 用户输入正确的用户名和密码

* **THEN** session 写入 user\_id/user\_name/user\_role，重定向到首页

#### Scenario: 登录失败

* **WHEN** 用户输入错误的用户名或密码

* **THEN** 提示错误信息，停留在登录页

### Requirement: 会话拦截

系统 SHALL 对除登录/注册/静态资源外的所有路由进行登录拦截，未登录访问自动重定向到登录页。

#### Scenario: 未登录访问受保护页面

* **WHEN** 用户未登录时访问管理页面

* **THEN** 自动重定向到 login.html

### Requirement: 退出登录

系统 SHALL 提供退出登录功能，清除 session 数据，重定向到登录页。manage.html 导航栏 SHALL 包含【退出登录】按钮。

#### Scenario: 退出登录

* **WHEN** 用户点击退出登录

* **THEN** session 清除，重定向到 login.html

### Requirement: 用户角色权限

系统 SHALL 支持两种用户角色：管理员（admin）和只读用户（user）。管理员可执行增删改导入导出全部操作，只读用户仅可查看数据和查询，不可新增/编辑/删除/导入。

#### Scenario: 管理员操作

* **WHEN** 管理员角色用户访问增删改导入导出功能

* **THEN** 允许操作

#### Scenario: 只读用户受限

* **WHEN** 只读用户角色尝试新增/编辑/删除/导入操作

* **THEN** 提示权限不足，拒绝操作

### Requirement: 学生信息新增

系统 SHALL 提供单条学生信息新增页面，字段包括学号、姓名、性别、年龄、专业、年级、班级，学号唯一不可重复。执行 INSERT INTO student\_info(...) VALUES(...)。

#### Scenario: 新增成功

* **WHEN** 用户填写合法学生信息并提交

* **THEN** 数据写入 student\_info 表，提示成功

#### Scenario: 学号重复

* **WHEN** 用户填写已存在的学号

* **THEN** 提示学号已存在，不写入数据库

### Requirement: 学生信息查询与展示

系统 SHALL 在管理页面展示学生数据列表，支持分页显示（每页10条，使用 LIMIT 0,10 / LIMIT 10,10 分页），显示所有字段。

#### Scenario: 数据列表展示

* **WHEN** 用户访问管理页面

* **THEN** 显示学生数据列表，支持分页

### Requirement: 学生信息编辑

系统 SHALL 支持编辑学生信息，执行 UPDATE student\_info SET ... WHERE id=%s，修改后更新数据库记录。

#### Scenario: 编辑成功

* **WHEN** 用户修改学生信息并提交

* **THEN** 数据库记录更新，提示成功

### Requirement: 学生信息删除

系统 SHALL 支持单条删除学生数据，执行 DELETE FROM student\_info WHERE id=%s，删除前确认。

#### Scenario: 删除成功

* **WHEN** 用户确认删除某条学生数据

* **THEN** 数据库记录删除，列表刷新

### Requirement: CSV模板下载

系统 SHALL 提供标准CSV模板下载，模板首行为固定表头 `学号,姓名,性别,年龄,专业,年级,班级`，无数据行。在内存生成CSV数据流返回浏览器下载。

#### Scenario: 下载模板

* **WHEN** 用户点击下载导入模板按钮

* **THEN** 浏览器下载标准CSV模板文件，首行为表头，无数据行

### Requirement: CSV批量导入

系统 SHALL 支持上传CSV文件批量导入学生数据。前端仅允许选择 `.csv` 后缀文件。后端处理：

1. 读取上传CSV所有行
2. 自动跳过第一行（index=0表头行），从下标1开始遍历
3. 空行自动跳过
4. 逐字段校验：学号为空或年龄非数字标记异常跳过
5. 学号重复（UNIQUE冲突）跳过该行，记录异常
6. 合法数据使用 INSERT INTO student\_info(...) VALUES(...),(...),... 批量插入（兼容MySQL5.6多值INSERT语法）
7. 开启事务（BEGIN）：全部合法COMMIT，异常ROLLBACK
8. 返回成功条数和失败条数

#### Scenario: 全部合法导入

* **WHEN** 上传CSV所有数据行合法

* **THEN** 事务COMMIT，全部数据入库，返回成功条数

#### Scenario: 部分数据异常

* **WHEN** 上传CSV包含学号重复或格式错误行

* **THEN** 异常行跳过不入库，合法数据入库，返回成功和失败条数

#### Scenario: 事务回滚

* **WHEN** 批量导入过程中发生数据库异常

* **THEN** 事务ROLLBACK，整批数据回滚，不入库

#### Scenario: 前端文件类型限制

* **WHEN** 用户选择非.csv文件上传

* **THEN** 前端拦截，提示仅允许CSV文件

### Requirement: CSV导入预览

系统 SHALL 支持CSV导入预览功能：前端上传后先预览表格数据，用户确认后再入库。

#### Scenario: 预览后确认导入

* **WHEN** 用户上传CSV文件

* **THEN** 先展示预览表格，用户确认后执行导入

#### Scenario: 预览后取消

* **WHEN** 用户上传CSV文件后点击取消

* **THEN** 不执行导入，清空预览

### Requirement: CSV批量导出

系统 SHALL 支持两种CSV导出：全表导出和筛选结果导出。导出字段顺序：student\_no,student\_name,gender,age,major,grade,class\_name。导出CSV首行为标准表头 `学号,姓名,性别,年龄,专业,年级,班级`，编码utf8。

#### Scenario: 全表导出

* **WHEN** 用户点击导出全部数据按钮

* **THEN** 执行 SELECT student\_no,student\_name,gender,age,major,grade,class\_name FROM student\_info，生成CSV下载

#### Scenario: 筛选导出

* **WHEN** 用户在高级查询筛选后点击导出筛选数据按钮

* **THEN** 携带查询条件WHERE语句筛选后生成CSV下载

### Requirement: 高级查询

系统 SHALL 提供高级查询页面，覆盖本科MySQL全部关键字场景（七大类），每个关键字绑定真实业务查询，用户可一键执行查看结果。覆盖的关键字类别及具体场景：

1. **DDL数据库定义关键字**（在高级查询页面提供DDL实训展示区）：

   * CREATE DATABASE：初始化创建student\_manage数据库（展示建库SQL）

   * DROP DATABASE：后台隐藏功能，一键删除测试库（需二次确认）

   * CREATE TABLE：展示student\_info、user\_info建表SQL

   * DROP TABLE：清空测试表（需二次确认）

   * ALTER TABLE：新增字段/修改字段类型（如给学生表新增phone字段）

   * COMMENT：建表/字段注释展示

   * ENGINE/CHARSET：建表指定InnoDB引擎、utf8字符集展示

2. **DML数据操作关键字**（在高级查询页面提供DML实训展示区）：

   * INSERT：单条新增学生、注册用户、CSV批量导入数据

   * INSERT ... VALUES (...),(...)：CSV批量导入多值批量插入

   * UPDATE：编辑学生信息、后台重置管理员密码

   * DELETE：单条删除学生数据、清空测试数据

   * SELECT：全系统所有查询、导出CSV数据源基础语句

   * FROM：所有SELECT指定查询数据表student\_info/user\_info

   * WHERE：精准删改、条件查询、筛选导出

3. **条件筛选类关键字**（WHERE从句实训）：

   * AND：查询【计算机专业+2022年级】学生 WHERE major='计算机' AND grade='2022'

   * OR：查询计算机或软件工程专业 WHERE major='计算机' OR major='软件工程'

   * NOT：查询不是计算机专业的学生 WHERE NOT major='计算机'

   * IS NULL：查询未填写班级信息的学生 WHERE class\_name IS NULL

   * IS NOT NULL：查询已录入年龄数据的学生 WHERE age IS NOT NULL

   * BETWEEN：年龄18\~22岁学生 WHERE age BETWEEN 18 AND 22

   * IN：查询专业在('计算机','自动化','汉语言')的学生 WHERE major IN(...)

   * NOT IN：排除指定专业的学生 WHERE major NOT IN(...)

   * LIKE：姓名带"张"模糊查询 student\_name LIKE '%张%'

   * %/\_：通配符 \_匹配单字符、%匹配任意字符

4. **聚合统计&分组关键字**：

   * GROUP BY：按专业分组统计各专业人数 GROUP BY major

   * HAVING：筛选专业总人数>10的分组 GROUP BY major HAVING COUNT(\*)>10

   * COUNT：统计总人数COUNT(\*)、有年龄数据人数COUNT(age)

   * SUM：统计所有学生年龄总和 SUM(age)

   * AVG：计算各专业平均年龄 AVG(age) GROUP BY major

   * MAX/MIN：各专业最大/最小年龄 MAX(age),MIN(age) GROUP BY major

5. **排序、分页、去重关键字**：

   * ORDER BY：按学号升序、年龄降序排序 ORDER BY age DESC / ORDER BY student\_no ASC

   * ASC/DESC：升序/降序修饰ORDER BY

   * LIMIT：数据分页展示 LIMIT 0,10 第一页 / LIMIT 10,10 第二页

   * DISTINCT：去重查询所有不重复专业 SELECT DISTINCT major FROM student\_info

6. **运算符、别名关键字**：

   * AS：字段别名/表别名 SELECT student\_name AS 姓名 FROM student\_info

   * \= / > / < / >= / <=：WHERE条件数值、字符串对比 age>20、grade>'2020'

7. **事务、约束关键字**（实训展示区）：

   * PRIMARY KEY：两张表主键定义展示

   * AUTO\_INCREMENT：id自增主键配置展示

   * UNIQUE：学号、账号唯一约束展示

   * NOT NULL：必填字段约束展示

   * DEFAULT：字段默认值配置展示（create\_time默认当前时间）

   * BEGIN/COMMIT/ROLLBACK：批量导入CSV事务展示

#### Scenario: 执行高级查询

* **WHEN** 用户选择查询条件或点击预设查询按钮

* **THEN** 执行对应SQL查询，展示结果

#### Scenario: DDL拓展操作

* **WHEN** 用户在DDL实训区点击ALTER TABLE按钮

* **THEN** 执行ALTER TABLE语句（如新增phone字段），展示执行结果

#### Scenario: DDL危险操作确认

* **WHEN** 用户点击DROP DATABASE或DROP TABLE按钮

* **THEN** 弹出二次确认对话框，确认后执行

### Requirement: 前端设计规范

系统前端 SHALL 使用原生HTML+CSS+JavaScript/Ajax，无任何UI框架和第三方JS插件。页面设计需遵循 frontend-skill 规范：简洁克制、层次分明、信息密度合理、操作便捷。

#### Scenario: 页面风格一致

* **WHEN** 用户浏览系统任意页面

* **THEN** 页面风格统一，布局清晰，操作直观

### Requirement: MySQL5.6兼容性

系统所有SQL语句 SHALL 严格兼容MySQL5.6语法，不使用8.0独有语法（如窗口函数）。

#### Scenario: SQL兼容性

* **WHEN** 系统执行任意SQL语句

* **THEN** 在MySQL5.6环境下正常运行无报错

### Requirement: 数据库配置

系统 SHALL 提供 config.py 集中管理数据库连接配置（主机、端口3306、用户名、密码、数据库名student\_manage）和Flask密钥配置。

#### Scenario: 配置修改

* **WHEN** 部署环境变更

* **THEN** 仅需修改 config.py 即可适配新环境

### Requirement: 项目目录结构与命名规范

系统 SHALL 严格遵循规范化的目录结构和命名约定，确保项目结构清晰、命名统一、可维护性强。

#### 目录结构规范

项目根目录下 SHALL 按以下结构组织，各层级职责分明，不允许随意创建额外目录或文件：

```
student_system/
├── config.py        # 配置层：集中管理所有配置
├── app.py           # 入口层：Flask应用入口、路由注册、全局钩子
├── db_utils.py      # 数据层：数据库连接与操作工具
├── csv_handle.py    # 业务层：CSV导入导出专用工具
├── static/          # 静态资源层
│   ├── css/         # 样式文件，仅允许 .css 文件
│   │   └── style.css
│   └── js/          # 脚本文件，仅允许 .js 文件
│       └── main.js
├── templates/       # 模板层：Flask Jinja2 模板，仅允许 .html 文件
│   ├── login.html
│   ├── register.html
│   ├── index.html
│   ├── add_stu.html
│   ├── manage.html
│   └── query.html
└── sql/             # 数据库脚本层，仅允许 .sql 文件
    └── init.sql
```

#### 命名规范

1. **Python文件命名**：全小写+下划线分隔（snake_case），如 `db_utils.py`、`csv_handle.py`
2. **Python函数/方法命名**：全小写+下划线分隔（snake_case），如 `get_conn()`、`parse_csv()`
3. **Python变量命名**：全小写+下划线分隔（snake_case），如 `student_no`、`class_name`
4. **Python类命名**：大驼峰（PascalCase），如 `DBHelper`
5. **HTML文件命名**：全小写+下划线分隔（snake_case），如 `add_stu.html`、`manage.html`
6. **CSS文件命名**：全小写+连字符分隔（kebab-case），如 `style.css`
7. **JS文件命名**：全小写+下划线分隔（snake_case），如 `main.js`
8. **CSS类名命名**：全小写+连字符分隔（kebab-case），如 `btn-primary`、`nav-header`、`table-data`
9. **JS变量/函数命名**：全小写+下划线分隔（snake_case），如 `handle_submit`、`page_size`
10. **SQL文件命名**：全小写+下划线分隔（snake_case），如 `init.sql`
11. **数据库表名命名**：全小写+下划线分隔（snake_case），如 `student_info`、`user_info`
12. **数据库字段名命名**：全小写+下划线分隔（snake_case），如 `student_no`、`create_time`
13. **路由URL命名**：全小写+斜杠分隔，如 `/add`、`/csv/import`、`/query/execute`
14. **Flask路由函数命名**：全小写+下划线分隔，与路由路径对应，如 `def add_student()`、`def csv_import()`

#### 代码组织规范

1. **单一职责**：每个Python文件只负责一个功能模块（config.py管配置、db_utils.py管数据库、csv_handle.py管CSV）
2. **禁止冗余文件**：不允许创建未在目录结构中定义的额外文件（如临时脚本、测试数据文件等）
3. **禁止空目录**：每个目录下必须有实际文件，不允许存在空目录
4. **导入规范**：Python文件导入顺序为 标准库→第三方库→本地模块，每组之间空一行
5. **注释规范**：每个Python文件顶部需有模块功能说明注释，每个函数需有简要功能注释

#### Scenario: 目录结构完整且规范
- **WHEN** 项目开发完成
- **THEN** 目录结构与规范定义一致，无多余文件和空目录

#### Scenario: 命名规范一致
- **WHEN** 审查项目任意文件/变量/函数/类名
- **THEN** 命名符合上述规范，风格统一

### Requirement: 技术栈约束

系统 SHALL 严格使用 PLAN.MD 规定的技术栈，不得引入额外依赖：
- Web框架：Flask（唯一Web框架）
- 数据库驱动：pymysql（唯一数据库驱动）
- CSV处理：Python内置 `csv` 标准库（禁止使用 pandas、openpyxl 等第三方表格库）
- 会话管理：Flask自带 session（禁止使用 Flask-Login 等第三方会话库）
- 前端：原生HTML+CSS+JavaScript/Ajax（禁止使用任何UI框架和第三方JS插件）
- 依赖安装仅需：`pip install flask pymysql`

#### Scenario: 技术栈合规
- **WHEN** 审查项目依赖
- **THEN** 仅依赖 flask 和 pymysql，无其他第三方库

