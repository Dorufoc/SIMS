# 查询界面架构

- [x] query.html 顶部包含四个 Tab 标签（条件查询/统计分析/排序浏览/SQL实训），点击可切换面板
- [x] 默认展示"条件查询"面板

# 条件查询面板

- [x] 可视化查询构建器支持添加多行查询条件（字段下拉+运算符下拉+值输入+删除按钮）
- [x] 运算符下拉包含：= / != / > / < / >= / <= / LIKE / IN / NOT IN / BETWEEN / IS NULL / IS NOT NULL
- [x] 选择 BETWEEN 时值输入区变为两个输入框（最小值~最大值）
- [x] 选择 IS NULL / IS NOT NULL 时值输入区隐藏
- [x] 选择 IN / NOT IN 时值输入区显示"多个值用英文逗号分隔"提示
- [x] 条件行之间有 AND/OR 逻辑选择
- [x] 快捷筛选区包含7个业务场景一键筛选按钮
- [x] 点击"查询"按钮后 Ajax 提交至 /query/build，展示结果表格和SQL语句
- [x] SQL语句中关键字加粗+蓝色高亮
- [x] 点击"重置"清空所有条件行
- [x] 点击"导出结果"将当前查询结果导出为CSV

# 统计分析面板

- [x] 5个统计场景以卡片形式展示（专业人数分布/热门专业筛选/总人数统计/年龄综合统计/不重复专业列表）
- [x] 点击场景卡片执行对应SQL，展示结果表格和SQL语句
- [x] SQL语句中关键字加粗+蓝色高亮
- [x] 提供"导出统计结果"按钮

# 排序浏览面板

- [x] 学生数据表格列头可点击排序（首次升序、再次降序、第三次取消排序）
- [x] 当前排序列显示排序方向箭头（↑/↓）
- [x] 默认按学号升序
- [x] 底部分页控件（上一页/页码/下一页，每页10条）
- [x] 显示当前页码和总页数
- [x] SQL展示区显示当前 ORDER BY + LIMIT 语句

# SQL实训面板

- [x] 手风琴折叠面板组织三个分类（DDL/DML/事务与约束），点击展开/收起
- [x] 每个关键字以卡片形式展示（关键字名称+一句话说明）
- [x] 点击卡片展开详情（用途说明+示例SQL+执行按钮）
- [x] DDL可执行操作（ALTER TABLE）有执行按钮
- [x] 危险操作（DROP DATABASE/DROP TABLE）有红色警告标识，执行需二次确认
- [x] 只读用户无法执行DDL操作，按钮禁用
- [x] DML和事务约束关键字仅展示SQL示例，不可执行

# 后端API

- [x] SQL_MAP 键名与前端 data-keyword 完全一致（使用下划线命名）
- [x] /csv/export_filtered 同时支持 GET 和 POST
- [x] POST /query/build 接收 conditions 数组，动态拼接 WHERE 子句返回结果
- [x] POST /query/stat 接收 scene 参数，返回对应统计结果
- [x] POST /query/sort 接收 sort_field/sort_order/page，返回排序分页结果
- [x] GET /query/keyword 接收 keyword 参数，返回关键字详情
- [x] POST /query/keyword/execute 接收 keyword 参数，执行DDL操作
- [x] 旧的 /query/execute 路由已移除

# 交互规范

- [x] 所有查询使用 Ajax 异步提交，页面无刷新
- [x] 查询过程中显示加载状态
- [x] 查询结果为空时显示"暂无匹配数据"
- [x] 管理员可执行DDL操作，只读用户按钮禁用
- [x] 危险操作必须二次确认
- [x] 导航栏与其他页面保持一致

# MySQL关键字覆盖

- [x] 条件查询面板覆盖：WHERE, AND, OR, NOT, =, !=, >, <, >=, <=, LIKE, %, _, IN, NOT IN, BETWEEN, IS NULL, IS NOT NULL, SELECT, FROM, AS
- [x] 统计分析面板覆盖：GROUP BY, HAVING, COUNT, SUM, AVG, MAX, MIN, DISTINCT, AS
- [x] 排序浏览面板覆盖：ORDER BY, ASC, DESC, LIMIT, SELECT, FROM
- [x] SQL实训面板覆盖：DDL全部关键字(7个)、DML全部关键字(7个)、事务约束全部关键字(6个)
