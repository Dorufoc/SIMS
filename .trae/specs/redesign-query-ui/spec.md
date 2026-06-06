# 查询界面场景化重设计 Spec

## Why

当前 query.html 将42个MySQL关键字平铺为按钮列表，缺乏业务场景引导和可视化操作体验。用户无法理解"我为什么要点这个按钮"，操作结果也仅是冷冰冰的SQL文本。需要将关键字列表转化为以实际业务场景驱动的可视化查询界面，让用户在真实操作中自然学习和使用SQL关键字。

## What Changes

* **重构 query.html**：从"关键字按钮列表"改为"场景驱动的多面板查询界面"

* **重构 app.py 查询路由**：新增场景化查询API，修复现有 keyword 与 SQL\_MAP 键名不匹配的 bug

* **重构 style.css**：新增查询面板样式、可视化查询构建器样式、统计卡片样式

* **重构 main.js**：新增查询面板交互逻辑（条件构建器、排序切换、分页控制）

* **修复已知 bug**：前端 data-keyword 与后端 SQL\_MAP 键名不一致、导出接口 GET/POST 方法不匹配

## Impact

* Affected code: `student_system/templates/query.html`（完全重写）、`student_system/app.py`（查询路由重构）、`student_system/static/css/style.css`（新增样式）、`student_system/static/js/main.js`（新增交互逻辑）

* Affected specs: build-sims spec 中"高级查询"相关需求将被本 spec 替代

## ADDED Requirements

### Requirement: 场景驱动的四面板查询架构

系统 SHALL 将查询页面重构为四个业务场景面板，通过顶部 Tab 标签切换：

1. **条件查询** — 可视化查询构建器，用户通过表单控件组合查询条件
2. **统计分析** — 预置业务统计场景，一键查看聚合结果
3. **排序浏览** — 可排序可分页的学生数据浏览表
4. **SQL实训** — 分类关键字探索器，保留教学功能

#### Scenario: 面板切换

* **WHEN** 用户点击顶部 Tab 标签

* **THEN** 切换到对应面板，当前 Tab 高亮，其他面板隐藏

***

### Requirement: 条件查询面板 — 可视化查询构建器

系统 SHALL 提供可视化查询构建器，用户无需手写SQL即可组合复杂查询条件。界面包含：

**查询字段选择区**：下拉选择要查询的字段（学号/姓名/性别/年龄/专业/年级/班级）

**条件构建区**：支持添加多个查询条件行，每行包含：

* 字段下拉框（学号/姓名/性别/年龄/专业/年级/班级）

* 运算符下拉框（= / != / > / < / >= / <= / LIKE / IN / NOT IN / BETWEEN / IS NULL / IS NOT NULL）

* 值输入框（根据运算符动态变化：BETWEEN显示两个输入框，IS NULL/IS NOT NULL隐藏输入框，IN/NOT IN显示多值输入提示）

* 行间逻辑连接词选择（AND / OR）

* 删除该行按钮

**快捷筛选区**：提供常用业务场景一键筛选按钮：

* "计算机专业2022级" → `WHERE major='计算机' AND grade='2022'`

* "计算机或软件工程专业" → `WHERE major='计算机' OR major='软件工程'`

* "非计算机专业" → `WHERE NOT major='计算机'`

* "18\~22岁学生" → `WHERE age BETWEEN 18 AND 22`

* "姓名含'张'" → `WHERE student_name LIKE '%张%'`

* "未填写班级" → `WHERE class_name IS NULL`

* "指定专业枚举" → `WHERE major IN ('计算机','自动化','汉语言')`

**操作按钮区**：

* "查询"按钮：根据构建的条件生成SQL并执行，展示结果表格

* "重置"按钮：清空所有条件行

* "导出结果"按钮：将当前查询结果导出为CSV

**SQL展示区**：查询执行后，在结果表格上方展示对应的SQL语句（带语法高亮标注关键字），让用户理解可视化操作对应的SQL语法

**覆盖关键字**：WHERE, AND, OR, NOT, =, !=, >, <, >=, <=, LIKE, %, \_, IN, NOT IN, BETWEEN, IS NULL, IS NOT NULL, SELECT, FROM, AS

#### Scenario: 添加查询条件行

* **WHEN** 用户点击"添加条件"按钮

* **THEN** 新增一行条件（字段下拉+运算符下拉+值输入+删除按钮），行间显示AND/OR选择

#### Scenario: 运算符动态适配

* **WHEN** 用户选择 BETWEEN 运算符

* **THEN** 值输入区变为两个输入框（最小值和最大值），中间显示"\~"

* **WHEN** 用户选择 IS NULL 或 IS NOT NULL

* **THEN** 值输入区隐藏

* **WHEN** 用户选择 IN 或 NOT IN

* **THEN** 值输入区显示提示"多个值用英文逗号分隔"

#### Scenario: 快捷筛选一键查询

* **WHEN** 用户点击"计算机专业2022级"快捷按钮

* **THEN** 自动填充条件（专业=计算机 AND 年级=2022），执行查询，展示结果和对应SQL

#### Scenario: 可视化构建生成SQL

* **WHEN** 用户组合条件后点击"查询"

* **THEN** 后端根据条件参数动态拼接SQL，执行查询，返回结果和完整SQL语句，前端展示结果表格和SQL语句

***

### Requirement: 统计分析面板 — 业务统计场景

系统 SHALL 提供预置的业务统计场景，以统计卡片+结果表格的形式展示聚合数据。界面包含：

**统计场景选择区**（以卡片形式展示，每个卡片包含图标、标题、简述）：

1. **专业人数分布** — `SELECT major AS 专业, COUNT(*) AS 人数 FROM student_info GROUP BY major`
2. **热门专业筛选** — `SELECT major AS 专业, COUNT(*) AS 人数 FROM student_info GROUP BY major HAVING COUNT(*)>1`
3. **总人数统计** — `SELECT COUNT(*) AS 总人数, COUNT(age) AS 有年龄数据人数 FROM student_info`
4. **年龄综合统计** — `SELECT major AS 专业, AVG(age) AS 平均年龄, MAX(age) AS 最大年龄, MIN(age) AS 最小年龄, SUM(age) AS 年龄总和 FROM student_info GROUP BY major`
5. **不重复专业列表** — `SELECT DISTINCT major AS 不重复专业 FROM student_info`

**结果展示区**：

* 统计结果以表格展示

* SQL语句在表格上方展示（标注关键字）

* "导出统计结果"按钮

**覆盖关键字**：GROUP BY, HAVING, COUNT, SUM, AVG, MAX, MIN, DISTINCT, AS

#### Scenario: 选择统计场景

* **WHEN** 用户点击某个统计场景卡片

* **THEN** 执行对应SQL，展示统计结果表格和SQL语句

***

### Requirement: 排序浏览面板 — 可排序可分页数据表

系统 SHALL 提供一个完整的学生数据浏览表，支持列头点击排序和分页浏览。界面包含：

**数据表格**：

* 列头可点击排序（首次点击升序ASC，再次点击降序DESC，第三次取消排序）

* 当前排序列显示排序方向箭头（↑升序/↓降序）

* 默认按学号升序排列

**分页控件**：

* 底部分页栏：上一页/页码/下一页

* 每页显示10条（LIMIT分页）

* 显示当前页码和总页数

**SQL展示区**：展示当前查询的SQL语句（包含ORDER BY和LIMIT子句）

**覆盖关键字**：ORDER BY, ASC, DESC, LIMIT, SELECT, FROM

#### Scenario: 列头排序

* **WHEN** 用户点击"年龄"列头

* **THEN** 数据按年龄升序排列，列头显示↑箭头，SQL展示区显示 `ORDER BY age ASC`

* **WHEN** 用户再次点击"年龄"列头

* **THEN** 数据按年龄降序排列，列头显示↓箭头，SQL展示区显示 `ORDER BY age DESC`

#### Scenario: 分页浏览

* **WHEN** 用户点击"下一页"

* **THEN** 表格展示第2页数据（LIMIT 10,10），分页栏更新当前页码

***

### Requirement: 独立管理SQL操作面板 — 分类关键字探索器

系统 SHALL 提供分类的SQL关键字探索器，以手风琴（Accordion）折叠面板组织，每个类别可展开/收起。界面包含：

**分类折叠面板**：

1. **DDL 数据库定义** — 展开后显示关键字卡片列表
2. **DML 数据操作** — 展开后显示关键字卡片列表
3. **事务与约束** — 展开后显示关键字卡片列表

**关键字卡片**（每个关键字一张卡片）：

* 卡片头部：关键字名称（大字）+ 一句话说明

* 卡片内容（默认收起，点击展开）：

  * **用途说明**：该关键字在学生管理系统中的实际应用场景描述

  * **示例SQL**：带语法高亮的SQL语句

  * **执行按钮**（仅可执行的关键字显示）：点击执行SQL并展示结果

  * **危险标记**（DROP DATABASE/DROP TABLE）：红色警告标识，执行需二次确认

**DDL关键字卡片**：

| 关键字             | 说明                   | 可执行         |
| --------------- | -------------------- | ----------- |
| CREATE DATABASE | 创建student\_manage数据库 | 否（仅展示）      |
| DROP DATABASE   | 删除数据库                | 是（需确认，仅管理员） |
| CREATE TABLE    | 展示建表SQL              | 否（仅展示）      |
| DROP TABLE      | 清空测试表                | 是（需确认，仅管理员） |
| ALTER TABLE     | 新增/修改字段              | 是（仅管理员）     |
| COMMENT         | 字段注释说明               | 否（仅展示）      |
| ENGINE/CHARSET  | 引擎和字符集               | 否（仅展示）      |

**DML关键字卡片**：

| 关键字      | 说明      | 可执行        |
| -------- | ------- | ---------- |
| INSERT   | 单条新增学生  | 否（展示SQL示例） |
| INSERT多值 | CSV批量导入 | 否（展示SQL示例） |
| UPDATE   | 编辑学生信息  | 否（展示SQL示例） |
| DELETE   | 删除学生数据  | 否（展示SQL示例） |
| SELECT   | 查询数据    | 否（展示SQL示例） |
| FROM     | 指定数据表   | 否（展示SQL示例） |
| WHERE    | 条件筛选    | 否（展示SQL示例） |

**事务与约束关键字卡片**：

| 关键字                   | 说明   | 可执行            |
| --------------------- | ---- | -------------- |
| PRIMARY KEY           | 主键约束 | 否（展示建表SQL中的定义） |
| AUTO\_INCREMENT       | 自增主键 | 否（展示建表SQL中的定义） |
| UNIQUE                | 唯一约束 | 否（展示建表SQL中的定义） |
| NOT NULL              | 非空约束 | 否（展示建表SQL中的定义） |
| DEFAULT               | 默认值  | 否（展示建表SQL中的定义） |
| BEGIN/COMMIT/ROLLBACK | 事务控制 | 否（展示CSV导入事务流程） |

#### Scenario: 展开分类面板

* **WHEN** 用户点击"DDL 数据库定义"折叠面板标题

* **THEN** 展开显示该分类下所有关键字卡片，其他分类面板收起

#### Scenario: 展开关键字卡片

* **WHEN** 用户点击某张关键字卡片

* **THEN** 展开显示用途说明、示例SQL、执行按钮（如有）

#### Scenario: 执行DDL操作

* **WHEN** 管理员在ALTER TABLE卡片中点击执行

* **THEN** 执行ALTER TABLE语句，展示执行结果

* **WHEN** 只读用户尝试执行DDL操作

* **THEN** 按钮禁用，提示权限不足

#### Scenario: 危险操作确认

* **WHEN** 用户点击DROP DATABASE或DROP TABLE的执行按钮

* **THEN** 弹出二次确认弹窗，确认后执行

***

### Requirement: 后端查询API重构

系统 SHALL 重构查询相关后端API，修复已知bug并新增场景化查询接口：

**修复Bug**：

1. 前端 data-keyword 值与后端 SQL\_MAP 键名统一（使用下划线命名如 `IS_NULL`、`GROUP_BY`、`ORDER_ASC`、`ORDER_DESC`、`LIMIT_PAGE`）
2. `/csv/export_filtered` 路由同时支持 GET 和 POST 方法

**新增API**：

1. `POST /query/build` — 条件查询构建器接口

   * 请求参数：`{conditions: [{field, operator, value, logic}], export: boolean}`

   * 后端根据 conditions 动态拼接 WHERE 子句

   * 返回：`{sql: "完整SQL", columns: [...], data: [[...], ...]}` 或 CSV文件下载

2. `POST /query/stat` — 统计分析接口

   * 请求参数：`{scene: "major_count" | "major_filter" | "total_count" | "age_stats" | "distinct_major"}`

   * 返回：`{sql: "完整SQL", columns: [...], data: [[...], ...]}`

3. `POST /query/sort` — 排序浏览接口

   * 请求参数：`{sort_field, sort_order: "asc"|"desc"|"none", page: number}`

   * 返回：`{sql: "完整SQL", columns: [...], data: [[...], ...], total: number, page: number, total_pages: number}`

4. `GET /query/keyword` — SQL实训关键字详情接口

   * 请求参数：`?keyword=CREATE_DATABASE`

   * 返回：`{keyword: "CREATE DATABASE", description: "...", sql: "...", executable: true/false, category: "ddl"|"dml"|"constraint"}`

5. `POST /query/keyword/execute` — SQL实训关键字执行接口

   * 请求参数：`{keyword: "ALTER_TABLE"}`

   * 返回：`{success: true/false, message: "执行结果描述"}`

#### Scenario: 条件查询构建

* **WHEN** 前端发送 `{conditions: [{field:"major", operator:"=", value:"计算机", logic:"AND"}, {field:"grade", operator:"=", value:"2022", logic:""}]}`

* **THEN** 后端拼接 `SELECT * FROM student_info WHERE major='计算机' AND grade='2022'`，执行查询返回结果

#### Scenario: 排序浏览

* **WHEN** 前端发送 `{sort_field:"age", sort_order:"desc", page:1}`

* **THEN** 后端拼接 `SELECT * FROM student_info ORDER BY age DESC LIMIT 0,10`，返回结果和分页信息

***

### Requirement: SQL语句展示与关键字标注

系统在所有查询结果上方 SHALL 展示对应的完整SQL语句，并对SQL关键字进行视觉标注（加粗+颜色高亮），帮助用户理解SQL语法结构。标注的关键字包括：SELECT, FROM, WHERE, AND, OR, NOT, IN, BETWEEN, LIKE, IS NULL, IS NOT NULL, GROUP BY, HAVING, ORDER BY, ASC, DESC, LIMIT, DISTINCT, AS, COUNT, SUM, AVG, MAX, MIN, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, TABLE, DATABASE, PRIMARY KEY, AUTO\_INCREMENT, UNIQUE, NOT NULL, DEFAULT, COMMENT, ENGINE, CHARSET, BEGIN, COMMIT, ROLLBACK。

#### Scenario: SQL关键字高亮

* **WHEN** 查询执行后展示SQL语句 `SELECT * FROM student_info WHERE major='计算机' AND grade='2022'`

* **THEN** SELECT、FROM、WHERE、AND 以加粗+蓝色显示，其余文本正常显示

***

### Requirement: 前端交互规范

系统查询页面 SHALL 遵循以下交互规范：

1. 所有查询操作使用 Ajax 异步提交，页面无刷新
2. 查询过程中显示加载状态
3. 查询结果为空时显示友好提示"暂无匹配数据"
4. 操作按钮根据用户角色动态显示/禁用（管理员可执行DDL，只读用户禁用）
5. 危险操作（DROP DATABASE/DROP TABLE）必须二次确认
6. 导航栏与系统其他页面保持一致

#### Scenario: 加载状态

* **WHEN** 用户点击查询按钮

* **THEN** 按钮显示加载中状态，结果区域显示加载提示，查询完成后恢复

#### Scenario: 空结果提示

* **WHEN** 查询结果为空

* **THEN** 结果区域显示"暂无匹配数据"提示

