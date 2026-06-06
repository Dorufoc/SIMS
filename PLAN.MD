# 学生信息管理与查询系统（升级完整版项目实现方案）

适配：**MySQL5.6、Python任意版本、原生HTML+CSS+JS+Flask**
新增三大模块：**用户注册登录模块（独立用户数据表）、CSV批量导入（带模板下载）、CSV批量导出**；全量罗列本科MySQL实训全部关键字+配套落地查询场景，满足高校数据库课程实训全覆盖要求。

## 一、项目更新概述

在原有学生CRUD系统基础上迭代升级：

1. 新增独立**系统用户表user_info**，实现账号注册、登录、会话校验，未登录禁止访问系统所有管理、导入导出接口；
2. 增加CSV批量导入功能：前端提供「下载导入模板」按钮→下载带固定表头CSV→用户填数据上传→后端自动剔除表头、字段匹配、批量入库、异常数据拦截；
3. 增加CSV批量导出功能：选中全量/筛选后数据一键导出本地CSV；
4. 适配数据库环境：**MySQL5.6语法规范（舍弃8.0独有语法，兼容5.6特性）**；
5. 完整收录本科实训全部MySQL关键字，每条关键字绑定本系统真实业务查询场景，全部在项目代码落地实现，无遗漏。

## 二、整体技术栈（修订）

### 后端

- Web框架：Flask
- 数据库：MySQL5.6（字符集utf8mb4）
- 数据库驱动：pymysql
- CSV处理：Python内置 `csv`标准库（无需额外安装第三方表格库，兼容全Python版本）
- 会话：Flask自带session实现登录状态保持

### 前端

原生HTML+CSS+JavaScript/Ajax，无任何UI框架、无第三方JS插件，页面新增登录页、注册页、导入导出操作区。

## 三、数据库设计（新增用户表，原学生表保留，兼容MySQL5.6）

### 3.1 原有数据库：student_manage（utf8编码，MySQL5.6标准）

#### 1）原有学生主表 student_info（不变，适配5.6）

| 字段         | 类型        | 约束                                | 备注                        |
| ------------ | ----------- | ----------------------------------- | --------------------------- |
| id           | INT         | PRIMARY KEY AUTO_INCREMENT NOT NULL | 自增主键                    |
| student_no   | VARCHAR(20) | UNIQUE NOT NULL                     | 学生学号唯一                |
| student_name | VARCHAR(30) | NOT NULL                            | 姓名                        |
| gender       | VARCHAR(6)  | DEFAULT NULL                        | 性别                        |
| age          | TINYINT     | DEFAULT NULL                        | 年龄                        |
| major        | VARCHAR(50) | DEFAULT NULL                        | 专业                        |
| grade        | VARCHAR(20) | DEFAULT NULL                        | 年级                        |
| class_name   | VARCHAR(30) | DEFAULT NULL                        | 班级                        |
| create_time  | DATETIME    | DEFAULT CURRENT_TIMESTAMP           | 录入时间（5.6支持默认时间） |

#### 2）【新增独立用户表 user_info 用于登录注册】

```sql
CREATE TABLE user_info(
    uid INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户主键',
    username VARCHAR(32) NOT NULL UNIQUE COMMENT '登录账号，唯一不可重复',
    password VARCHAR(64) NOT NULL COMMENT '登录密码',
    real_name VARCHAR(20) COMMENT '管理员姓名',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '账号创建时间'
)ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='系统管理员账号表';
```

> 业务规则：
>
> 1. 注册时校验用户名唯一性，重复弹窗提示；
> 2. 登录校验账号密码，正确写入session；
> 3. 所有增删改、导入导出接口增加登录拦截，未登录跳转登录页面。

### 3.2 CSV导入导出字段映射规则（固定表头，后端自动解析）

**标准CSV模板表头（固定，下载模板自带）：**
`学号,姓名,性别,年龄,专业,年级,班级`

1. 用户下载CSV模板→Excel/WPS填写数据；
2. 前端上传文件→后端读取CSV：**自动跳过第一行表头行**，从第二行开始逐行解析；
3. 字段顺序和student_info字段一一匹配：student_no、student_name、gender、age、major、grade、class_name；
4. 数据校验：学号重复则跳过该行并记录异常，合法数据批量INSERT入库。

## 四、后端目录结构（升级后）

```
student_system/
├── config.py        # 数据库配置(MySQL5.6地址、端口、账号密码)、Flask密钥配置
├── app.py           # 项目入口、路由、登录拦截全局钩子
├── db_utils.py      # 数据库通用工具类（用户/学生两张表通用连接）
├── csv_handle.py    # 【新增】CSV导入、导出、模板生成专用工具脚本
├── static/
│   ├── css/
│   └── js/          # 前端上传、下载ajax逻辑
├── templates/
│   ├── login.html       # 登录页面【新增】
│   ├── register.html    # 注册页面【新增】
│   ├── index.html       # 系统首页
│   ├── add_stu.html     # 单条新增
│   ├── manage.html      # 数据管理（含导入导出按钮）
│   └── query.html       # 高级查询页
└── sql/
    └── init.sql     # 建库+student_info+user_info建表语句
```

## 五、新增三大功能详细设计

### 5.1 用户注册&登录模块全流程

#### 5.1.1 注册功能

1. 前端注册页：用户名、密码、真实姓名输入框；
2. 前端简单非空校验；
3. 后端接收参数：执行 `INSERT INTO user_info(...) VALUES(...)`；
4. 捕获用户名唯一冲突（UNIQUE约束报错），返回“账号已被注册”；
5. 注册成功跳转登录页。

#### 5.1.2 登录功能

1. 登录页输入账号密码；
2. SQL：`SELECT uid,username FROM user_info WHERE username=%s AND password=%s`；
3. 查询存在记录→写入session[`user_id`/`user_name`]；
4. 全局拦截器：访问除登录/注册外所有路由，先校验session，失效自动跳转登录。

#### 5.1.3 退出登录

清除session数据，重定向至登录页面。

### 5.2 CSV批量导入功能（核心新增）

#### 5.2.1 前端交互

在学生数据管理页面增加两个按钮：

1. 【下载导入模板】：点击触发后端生成标准表头CSV文件，浏览器直接下载；
2. 【上传CSV批量导入】：文件选择框，仅允许 `.csv`后缀文件，提交上传。

#### 5.2.2 后端处理逻辑（csv_handle.py）

1. **模板生成逻辑**：在内存生成CSV数据流，首行写入固定表头 `学号,姓名,性别,年龄,专业,年级,班级`，无任何数据，直接返回浏览器下载；
2. **上传解析逻辑**
   - 读取上传CSV所有行；
   - `跳过index=0的表头行`，从下标1开始遍历数据；
   - 逐字段格式校验：年龄非数字、学号为空直接标记异常行；
   - 使用 `INSERT INTO student_info(student_no,student_name,gender,age,major,grade,class_name) VALUES(?,?,?,?,?,?,?)`批量插入；
   - 学号重复（唯一键冲突）：跳过本条，汇总成功条数、失败条数返回前端弹窗展示。

> 兼容MySQL5.6批量插入语法：支持单语句多值批量INSERT，减少数据库IO。

### 5.3 CSV批量导出功能

1. 前端：数据列表上方增加【导出当前全部数据】【导出筛选结果】按钮；
2. 全量导出：执行 `SELECT student_no,student_name,gender,age,major,grade,class_name FROM student_info`；
3. 条件导出：携带前端查询条件WHERE语句筛选后导出；
4. 后端生成CSV：首行写入标准表头，后续逐行拼接数据库查询结果，生成文件流浏览器下载。

## 六、本科MySQL全关键字清单+系统落地业务场景（MySQL5.6可用，无遗漏）

> 说明：所有关键字全部在本项目查询/增删改/统计功能中落地，严格遵循MySQL5.6语法，无8.0专属函数、窗口函数。

### （一）DDL 数据库定义关键字（库、表结构）

| 关键字          | 实训使用场景（本系统落地位置）                               |
| --------------- | ------------------------------------------------------------ |
| CREATE DATABASE | 初始化创建student_manage数据库                               |
| DROP DATABASE   | 实训拓展：可选一键删除测试库（后台隐藏功能）                 |
| CREATE TABLE    | 创建student_info、user_info两张数据表                        |
| DROP TABLE      | 实训拓展：清空测试表                                         |
| ALTER TABLE     | 拓展实训：新增字段/修改字段类型（比如给学生表新增phone字段） |
| COMMENT         | 建表、字段注释，在建表SQL全部使用                            |
| ENGINE/CHARSET  | 建表指定InnoDB引擎、utf8字符集，适配MySQL5.6                 |

### （二）DML 数据操作关键字（增删改查核心，系统主体功能）

| 关键字                        | 落地业务场景                                         |
| ----------------------------- | ---------------------------------------------------- |
| INSERT                        | 单条新增学生、注册用户、CSV批量导入数据              |
| INSERT ... VALUES (...),(...) | CSV批量导入多条数据批量插入                          |
| UPDATE                        | 编辑学生信息、后台重置管理员密码                     |
| DELETE                        | 单条删除学生数据、清空测试数据（谨慎使用）           |
| SELECT                        | 全系统所有查询、导出CSV数据源基础语句                |
| FROM                          | 所有SELECT必带，指定查询数据表student_info/user_info |
| WHERE                         | 精准删改、条件查询、筛选导出（按专业/年级筛选数据）  |

### （三）条件筛选类关键字（WHERE从句实训）

| 关键字      | 落地场景                                                                                            |
| ----------- | --------------------------------------------------------------------------------------------------- |
| AND         | 多条件组合：查询【计算机专业+2022年级】学生：where major='计算机' and grade='2022'                  |
| OR          | 多条件任选：查询计算机或软件工程专业全部学生：where major='计算机' or major='软件工程'              |
| NOT         | 反向筛选：查询不是计算机专业的学生：where not major='计算机'                                        |
| IS NULL     | 查询未填写班级信息的学生：where class_name is null                                                  |
| IS NOT NULL | 查询已录入年龄数据的学生：where age is not null                                                     |
| BETWEEN     | 年龄区间筛选：年龄18~22岁学生 where age between 18 and 22                                           |
| IN          | 多枚举匹配：查询专业在('计算机','自动化','汉语言')的学生 where major in('计算机','自动化','汉语言') |
| NOT IN      | 反向枚举：排除上述三个专业的学生 where major not in(...)                                            |
| LIKE        | 模糊查询：姓名带“张”、专业含“工程”：student_name like '%张%'                                    |
| %/_         | 通配符搭配LIKE：_匹配单个字符，'张_'匹配张三、张四；%匹配任意字符                                 |

### （四）聚合统计&分组关键字（高级查询页面核心实训）

| 关键字   | 落地场景                                                                 |
| -------- | ------------------------------------------------------------------------ |
| GROUP BY | 按专业分组统计各专业人数：GROUP BY major                                 |
| HAVING   | 分组后筛选：筛选专业总人数>10的分组 GROUP BY major HAVING COUNT(*)>10    |
| COUNT    | 统计总人数、分组人数：COUNT(*)统计全表数量，COUNT(age)统计有年龄数据人数 |
| SUM      | 拓展实训：统计所有学生年龄总和 SUM(age)                                  |
| AVG      | 计算各专业平均年龄 AVG(age) GROUP BY major                               |
| MAX/MIN  | 各专业最大年龄、最小年龄 MAX(age),MIN(age) GROUP BY major                |

### （五）排序、分页、去重关键字

| 关键字   | 落地场景                                                             |
| -------- | -------------------------------------------------------------------- |
| ORDER BY | 按学号升序、年龄降序排序：ORDER BY age DESC；ORDER BY student_no ASC |
| ASC/DESC | 升序、降序修饰ORDER BY，全部在高级查询可选排序                       |
| LIMIT    | 数据分页展示：LIMIT 0,10 第一页10条；LIMIT 10,10第二页               |
| DISTINCT | 去重查询：查询所有不重复专业 SELECT DISTINCT major FROM student_info |

### （六）运算符、别名关键字

| 关键字              | 落地场景                                                        |
| ------------------- | --------------------------------------------------------------- |
| AS                  | 字段别名、表别名：SELECT student_name AS 姓名 FROM student_info |
| = / > / < / >= / <= | WHERE条件数值、字符串对比：age>20、grade>'2020'                 |

### （七）事务、约束关键字（实训拓展功能）

| 关键字                | 落地场景                                                                                  |
| --------------------- | ----------------------------------------------------------------------------------------- |
| PRIMARY KEY           | 两张表主键定义                                                                            |
| AUTO_INCREMENT        | id自增主键配置                                                                            |
| UNIQUE                | 学号、账号唯一约束                                                                        |
| NOT NULL              | 必填字段约束（姓名、学号、账号密码）                                                      |
| DEFAULT               | 字段默认值配置（create_time默认当前时间）                                                 |
| BEGIN/COMMIT/ROLLBACK | 批量导入CSV增加事务：全部成功再COMMIT，异常整批ROLLBACK回滚，保证数据一致性（重要实训点） |

> 补充：以上关键字覆盖**本科《数据库原理》课内实训100%考点**，无缺漏，全部在系统页面有对应查询按钮可一键执行查看结果。

## 七、CSV导入导出细节约束（适配MySQL5.6+业务容错）

1. **导入容错规则**
   - 空行自动跳过；
   - 学号重复（UNIQUE冲突）：本条舍弃，统计失败数据；
   - 年龄非数字格式：本条标记异常不入库；
   - 开启MySQL事务：一批CSV要么全部合法全入库，要么异常全部回滚，避免半截入库脏数据。
2. **导出规则**
   - 导出CSV编码utf8，避免Excel打开乱码；
   - 支持两种导出：全表导出、筛选结果导出（用户在高级查询筛选后直接导出当前结果）。

## 八、前端页面更新明细

1. 新增：`login.html`登录页、`register.html`注册页；
2. manage.html（数据管理页）导航栏新增【退出登录】；操作区新增：
   - 【下载导入模板】按钮→下载标准表头CSV；
   - 【选择CSV文件+批量导入】上传控件；
   - 【导出全部数据】【导出筛选数据】按钮；
3. 所有页面增加登录鉴权：未登录访问自动跳转login.html。

## 九、项目部署&环境说明

1. MySQL：5.6版本，创建student_manage数据库，执行init.sql完成双表初始化；
2. Python：任意版本，安装依赖：`pip install flask pymysql`；
3. 修改config.py：填写本机MySQL5.6 IP、端口3306、账号、密码；
4. 启动app.py，浏览器访问，先注册管理员账号后登录使用全部功能。

## 十、最终交付清单（升级后）

1. 完整项目设计方案文档（本文档）；
2. MySQL建库建表SQL脚本（student_info+user_info）；
3. 全套前后端源码（含新增登录注册、CSV导入导出代码）；
4. 本科MySQL关键字清单+对应系统操作指引文档；
5. CSV标准导入模板（内置在后端代码，一键下载）；
6. 部署说明文档。

## 十一、必须实现的拓展实训方向

1. 增加用户角色（管理员/只读用户），新增role字段，不同账号权限不同；
2. CSV导入预览功能：前端上传后先预览表格数据，确认后再入库。
