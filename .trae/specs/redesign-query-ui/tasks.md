# Tasks

- [x] Task 1: 重构后端查询API（app.py）
  - [x] 1.1: 修复 SQL_MAP 键名与前端 data-keyword 不一致的 bug（统一使用下划线命名：IS_NULL、IS_NOT_NULL、LIKE_WILDCARD、GROUP_BY、ORDER_ASC、ORDER_DESC、LIMIT_PAGE 等）
  - [x] 1.2: 修复 /csv/export_filtered 路由方法不匹配 bug（同时支持 GET 和 POST）
  - [x] 1.3: 新增 POST /query/build 接口（接收 conditions 数组，动态拼接 WHERE 子句，支持 AND/OR/NOT 逻辑组合，返回 sql/columns/data）
  - [x] 1.4: 新增 POST /query/stat 接口（接收 scene 参数，支持 major_count/major_filter/total_count/age_stats/distinct_major 五种统计场景，返回 sql/columns/data）
  - [x] 1.5: 新增 POST /query/sort 接口（接收 sort_field/sort_order/page 参数，拼接 ORDER BY + LIMIT 分页SQL，返回 sql/columns/data/total/page/total_pages）
  - [x] 1.6: 新增 GET /query/keyword 接口（接收 keyword 参数，返回关键字详情：description/sql/executable/category）
  - [x] 1.7: 新增 POST /query/keyword/execute 接口（接收 keyword 参数，执行可执行的DDL操作，返回 success/message）
  - [x] 1.8: 移除旧的 /query/execute 路由（已被新接口替代）

- [x] Task 2: 重写 query.html 页面结构
  - [x] 2.1: 实现顶部 Tab 导航栏（条件查询/统计分析/排序浏览/SQL实训四个标签），点击切换面板
  - [x] 2.2: 实现"条件查询"面板 — 可视化查询构建器（字段选择+条件行添加/删除+运算符动态适配+AND/OR逻辑选择+快捷筛选按钮区+查询/重置/导出按钮+SQL展示区+结果表格区）
  - [x] 2.3: 实现"统计分析"面板 — 统计场景卡片选择区（5个场景卡片：专业人数分布/热门专业筛选/总人数统计/年龄综合统计/不重复专业列表）+ SQL展示区+结果表格区+导出按钮
  - [x] 2.4: 实现"排序浏览"面板 — 学生数据表格（列头可点击排序+排序箭头指示）+ 分页控件（上一页/页码/下一页+当前页/总页数）+ SQL展示区
  - [x] 2.5: 实现"SQL实训"面板 — 手风琴折叠面板（DDL/DML/事务与约束三个分类）+ 关键字卡片（关键字名称+说明+展开详情：用途说明/示例SQL/执行按钮/危险标记）+ 二次确认弹窗
  - [x] 2.6: 实现SQL语句展示区组件（关键字加粗+蓝色高亮标注）
  - [x] 2.7: 统一导航栏样式与其他页面一致

- [x] Task 3: 新增查询页面CSS样式（style.css）
  - [x] 3.1: Tab 导航样式（tab-bar、tab-item、tab-active）
  - [x] 3.2: 条件查询面板样式（condition-builder、condition-row、operator-select、logic-toggle、quick-filter区）
  - [x] 3.3: 统计分析面板样式（stat-card、stat-card-active、stat-icon）
  - [x] 3.4: 排序浏览面板样式（sortable-table、sort-header、sort-arrow、pagination）
  - [x] 3.5: SQL实训面板样式（accordion、accordion-item、keyword-card、keyword-detail、sql-highlight、keyword-tag）
  - [x] 3.6: SQL展示区样式（sql-display-box、sql-keyword-highlight）
  - [x] 3.7: 空结果提示样式（empty-result）

- [x] Task 4: 新增查询页面JS交互逻辑（main.js）
  - [x] 4.1: Tab 面板切换逻辑
  - [x] 4.2: 条件查询构建器逻辑（添加/删除条件行、运算符切换动态适配值输入区、快捷筛选按钮自动填充条件、查询按钮Ajax提交、重置清空、导出CSV）
  - [x] 4.3: 统计分析逻辑（场景卡片点击Ajax请求、结果渲染、导出）
  - [x] 4.4: 排序浏览逻辑（列头点击排序切换asc/desc/none、分页切换Ajax请求、结果渲染）
  - [x] 4.5: SQL实训逻辑（手风琴展开/收起、关键字卡片展开/收起、关键字详情Ajax加载、执行按钮Ajax提交、危险操作二次确认）
  - [x] 4.6: SQL关键字高亮渲染函数（识别SQL关键字并加粗+蓝色标注）
  - [x] 4.7: 通用：加载状态控制、空结果提示、角色权限按钮禁用

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 1, Task 2, Task 3]
