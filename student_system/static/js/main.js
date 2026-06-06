/* ========== 加载遮罩 ========== */

function show_loading() {
  var overlay = document.getElementById("loading-overlay");
  if (overlay) overlay.classList.add("active");
}

function hide_loading() {
  var overlay = document.getElementById("loading-overlay");
  if (overlay) overlay.classList.remove("active");
}

/* ========== Ajax工具函数 ========== */

/**
 * 通用POST请求
 * @param {string} url - 请求地址
 * @param {object|FormData} data - 请求数据
 * @param {function} callback - 回调函数 callback(success, response)
 * @param {boolean} is_json - 是否发送JSON格式
 */
function ajax_post(url, data, callback, is_json) {
  show_loading();
  var xhr = new XMLHttpRequest();
  xhr.open("POST", url, true);

  if (is_json) {
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(JSON.stringify(data));
  } else {
    if (!(data instanceof FormData)) {
      var fd = new FormData();
      for (var key in data) {
        if (data.hasOwnProperty(key)) {
          fd.append(key, data[key]);
        }
      }
      data = fd;
    }
    xhr.send(data);
  }

  xhr.onreadystatechange = function () {
    if (xhr.readyState === 4) {
      hide_loading();
      var resp;
      try {
        resp = JSON.parse(xhr.responseText);
      } catch (e) {
        resp = xhr.responseText;
      }
      var success = xhr.status >= 200 && xhr.status < 300;
      callback(success, resp);
    }
  };
}

/* ========== 分页逻辑 ========== */

/**
 * 跳转到指定页码
 * @param {number} page - 目标页码
 */
function go_page(page) {
  var url = new URL(window.location.href);
  url.searchParams.set("page", page);
  window.location.href = url.toString();
}

/* ========== 文件上传逻辑 ========== */

/**
 * 上传CSV文件并预览
 */
function upload_csv() {
  var file_input = document.getElementById("csv-file");
  if (!file_input || !file_input.files || file_input.files.length === 0) {
    show_msg("upload-msg", "请先选择CSV文件", "error");
    return;
  }

  var fd = new FormData();
  fd.append("file", file_input.files[0]);

  ajax_post("/csv/preview", fd, function (success, resp) {
    if (success && resp.ok) {
      hide_msg("upload-msg");
      render_preview(resp);
    } else {
      var err_msg = (resp && resp.message) ? resp.message : "预览失败";
      show_msg("upload-msg", err_msg, "error");
      var preview_area = document.getElementById("preview-area");
      if (preview_area) preview_area.innerHTML = "";
    }
  }, false);
}

/**
 * 确认导入CSV数据
 */
function confirm_import() {
  var valid_data_el = document.getElementById("valid-data");
  if (!valid_data_el) return;

  var valid_data;
  try {
    valid_data = JSON.parse(valid_data_el.value);
  } catch (e) {
    show_msg("upload-msg", "数据格式错误", "error");
    return;
  }

  ajax_post("/csv/import", { data: valid_data }, function (success, resp) {
    if (success && resp.ok) {
      show_msg("upload-msg", resp.message || "导入成功", "success");
      cancel_preview();
      setTimeout(function () { location.reload(); }, 1000);
    } else {
      var err_msg = (resp && resp.message) ? resp.message : "导入失败";
      show_msg("upload-msg", err_msg, "error");
    }
  }, true);
}

/**
 * 取消预览，清空预览区
 */
function cancel_preview() {
  var preview_area = document.getElementById("preview-area");
  if (preview_area) preview_area.innerHTML = "";

  var valid_data_el = document.getElementById("valid-data");
  if (valid_data_el) valid_data_el.value = "";

  var file_input = document.getElementById("csv-file");
  if (file_input) file_input.value = "";
}

/* ========== 导入预览逻辑 ========== */

/**
 * 渲染预览表格
 * @param {object} data - 预览数据 { headers, rows, errors, valid_data }
 */
function render_preview(data) {
  var preview_area = document.getElementById("preview-area");
  if (!preview_area) return;

  var html = '<table class="preview-table"><thead><tr>';
  html += "<th>状态</th>";
  for (var i = 0; i < data.headers.length; i++) {
    html += "<th>" + escape_html(data.headers[i]) + "</th>";
  }
  html += "</tr></thead><tbody>";

  var error_rows = data.errors || [];
  var error_row_nums = {};
  for (var e = 0; e < error_rows.length; e++) {
    if (error_rows[e].row !== undefined) {
      error_row_nums[error_rows[e].row] = error_rows[e].message || "错误";
    }
  }

  for (var r = 0; r < data.rows.length; r++) {
    var is_error = error_row_nums[r + 1] !== undefined;
    var row_class = is_error ? "row-error" : "row-valid";
    html += '<tr class="' + row_class + '">';
    html += "<td>" + (is_error ? escape_html(error_row_nums[r + 1]) : "OK") + "</td>";
    for (var c = 0; c < data.rows[r].length; c++) {
      html += "<td>" + escape_html(String(data.rows[r][c])) + "</td>";
    }
    html += "</tr>";
  }

  html += "</tbody></table>";

  if (data.valid_data) {
    html += '<input type="hidden" id="valid-data" value=\'' + escape_html(JSON.stringify(data.valid_data)) + '\'>';
  }

  html += '<div style="margin-top:12px;">';
  html += '<button class="btn btn-success" onclick="confirm_import()">确认导入</button> ';
  html += '<button class="btn btn-danger" onclick="cancel_preview()">取消</button>';
  html += "</div>";

  preview_area.innerHTML = html;

  if (error_rows.length > 0) {
    render_errors(error_rows);
  }
}

/**
 * 渲染错误信息列表
 * @param {array} errors - 错误数组 [{row, message}]
 */
function render_errors(errors) {
  var preview_area = document.getElementById("preview-area");
  if (!preview_area || !errors || errors.length === 0) return;

  var html = '<div class="msg-error" style="margin-top:12px;">';
  html += "<strong>以下行存在错误：</strong><ul style='margin:6px 0 0 18px;'>";
  for (var i = 0; i < errors.length; i++) {
    html += "<li>第 " + (errors[i].row || "?") + " 行: " + escape_html(errors[i].message || "未知错误") + "</li>";
  }
  html += "</ul></div>";

  preview_area.innerHTML += html;
}

/* ========== 通用消息提示 ========== */

/**
 * 显示消息
 * @param {string} element_id - 目标元素ID
 * @param {string} msg - 消息内容
 * @param {string} type - 类型 'success' 或 'error'
 */
function show_msg(element_id, msg, type) {
  var el = document.getElementById(element_id);
  if (!el) return;

  el.textContent = msg;
  el.className = type === "success" ? "msg-success" : "msg-error";
  el.style.display = "block";
}

/**
 * 隐藏消息
 * @param {string} element_id - 目标元素ID
 */
function hide_msg(element_id) {
  var el = document.getElementById(element_id);
  if (!el) return;

  el.style.display = "none";
  el.textContent = "";
}

/* ========== 删除确认 ========== */

/**
 * 确认删除学生
 * @param {string|number} student_id - 学生ID
 */
function confirm_delete(student_id) {
  if (!confirm("确定要删除该学生记录吗？此操作不可撤销。")) return;

  ajax_post("/delete/" + student_id, {}, function (success, resp) {
    if (success && resp.ok) {
      show_msg("action-msg", resp.message || "删除成功", "success");
      setTimeout(function () { location.reload(); }, 800);
    } else {
      var err_msg = (resp && resp.message) ? resp.message : "删除失败";
      show_msg("action-msg", err_msg, "error");
    }
  }, true);
}

/* ========== 编辑学生 ========== */

/**
 * 加载学生数据填充模态框
 * @param {string|number} student_id - 学生ID
 */
function load_student(student_id) {
  show_loading();
  var xhr = new XMLHttpRequest();
  xhr.open("GET", "/api/student/" + student_id, true);
  xhr.onreadystatechange = function () {
    if (xhr.readyState === 4) {
      hide_loading();
      if (xhr.status >= 200 && xhr.status < 300) {
        var resp;
        try {
          resp = JSON.parse(xhr.responseText);
        } catch (e) {
          show_msg("action-msg", "数据解析失败", "error");
          return;
        }

        if (resp.ok && resp.data) {
          fill_edit_form(resp.data);
          open_modal("edit-modal");
        } else {
          show_msg("action-msg", resp.message || "获取学生信息失败", "error");
        }
      } else {
        show_msg("action-msg", "请求失败", "error");
      }
    }
  };
  xhr.send();
}

/**
 * 保存编辑的学生信息
 * @param {string|number} student_id - 学生ID
 */
function save_student(student_id) {
  var form = document.getElementById("edit-form");
  if (!form) return;

  var data = {};
  var inputs = form.querySelectorAll(".form-control");
  for (var i = 0; i < inputs.length; i++) {
    var input = inputs[i];
    if (input.name) {
      data[input.name] = input.value;
    }
  }

  ajax_post("/edit/" + student_id, data, function (success, resp) {
    if (success && resp.ok) {
      show_msg("action-msg", resp.message || "保存成功", "success");
      close_modal("edit-modal");
      setTimeout(function () { location.reload(); }, 800);
    } else {
      var err_msg = (resp && resp.message) ? resp.message : "保存失败";
      show_msg("edit-msg", err_msg, "error");
    }
  }, true);
}

/* ========== 模态框辅助 ========== */

/**
 * 打开模态框
 * @param {string} modal_id - 模态框元素ID
 */
function open_modal(modal_id) {
  var modal = document.getElementById(modal_id);
  if (modal) modal.classList.add("active");
}

/**
 * 关闭模态框
 * @param {string} modal_id - 模态框元素ID
 */
function close_modal(modal_id) {
  var modal = document.getElementById(modal_id);
  if (modal) modal.classList.remove("active");
}

/* ========== 表单填充辅助 ========== */

/**
 * 填充编辑表单
 * @param {object} data - 学生数据
 */
function fill_edit_form(data) {
  var form = document.getElementById("edit-form");
  if (!form) return;

  var inputs = form.querySelectorAll(".form-control");
  for (var i = 0; i < inputs.length; i++) {
    var input = inputs[i];
    if (input.name && data[input.name] !== undefined) {
      input.value = data[input.name];
    }
  }
}

/* ========== 工具函数 ========== */

/**
 * HTML转义，防止XSS
 * @param {string} str - 原始字符串
 * @returns {string} 转义后的字符串
 */
function escape_html(str) {
  var div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

/* ========== 查询页面交互逻辑 ========== */
(function() {
    // 仅在查询页面执行
    if (!document.getElementById('panel-condition')) return;

    /* ---------- 1. Tab 面板切换逻辑 ---------- */
    var tab_items = document.querySelectorAll('.tab-item');
    var panels = {
        'condition': document.getElementById('panel-condition'),
        'stat': document.getElementById('panel-stat'),
        'sort': document.getElementById('panel-sort'),
        'training': document.getElementById('panel-training')
    };

    for (var i = 0; i < tab_items.length; i++) {
        tab_items[i].addEventListener('click', function() {
            var target = this.getAttribute('data-tab');
            // 移除所有tab-active
            for (var j = 0; j < tab_items.length; j++) {
                tab_items[j].classList.remove('tab-active');
            }
            this.classList.add('tab-active');
            // 切换面板
            for (var key in panels) {
                if (panels.hasOwnProperty(key)) {
                    panels[key].classList.remove('panel-active');
                }
            }
            panels[target].classList.add('panel-active');
            // 切换到排序浏览面板时自动加载数据
            if (target === 'sort' && !sort_loaded) {
                load_sort_data();
            }
        });
    }

    /* ---------- 2. 条件查询构建器逻辑 ---------- */
    var condition_builder = document.getElementById('condition-builder');
    var btn_add = document.querySelector('.btn-add-condition');

    btn_add.addEventListener('click', function() {
        add_condition_row();
    });

    function add_condition_row(field, operator, value, value_to, logic, not_checked) {
        var row = document.createElement('div');
        row.className = 'condition-row';

        // 逻辑选择（非第一行才显示）
        var existing_rows = condition_builder.querySelectorAll('.condition-row');
        if (existing_rows.length > 0) {
            var logic_select = document.createElement('select');
            logic_select.className = 'form-control condition-logic';
            logic_select.innerHTML = '<option value="AND">AND</option><option value="OR">OR</option>';
            if (logic) logic_select.value = logic;
            row.appendChild(logic_select);
        }

        // NOT 复选框
        var not_label = document.createElement('label');
        not_label.className = 'condition-not-label';
        var not_checkbox = document.createElement('input');
        not_checkbox.type = 'checkbox';
        not_checkbox.className = 'condition-not';
        if (not_checked) not_checkbox.checked = true;
        not_label.appendChild(not_checkbox);
        not_label.appendChild(document.createTextNode('NOT'));
        row.appendChild(not_label);

        // 字段下拉
        var field_select = document.createElement('select');
        field_select.className = 'form-control condition-field';
        field_select.innerHTML = '<option value="student_no">学号</option><option value="student_name">姓名</option><option value="gender">性别</option><option value="age">年龄</option><option value="major">专业</option><option value="grade">年级</option><option value="class_name">班级</option>';
        if (field) field_select.value = field;
        row.appendChild(field_select);

        // 运算符下拉
        var operator_select = document.createElement('select');
        operator_select.className = 'form-control condition-operator';
        operator_select.innerHTML = '<option value="=">=</option><option value="!=">!=</option><option value=">">></option><option value="<"><</option><option value=">=">>=</option><option value="<="><=</option><option value="LIKE">LIKE</option><option value="IN">IN</option><option value="NOT_IN">NOT IN</option><option value="BETWEEN">BETWEEN</option><option value="IS_NULL">IS NULL</option><option value="IS_NOT_NULL">IS NOT NULL</option>';
        if (operator) operator_select.value = operator;
        row.appendChild(operator_select);

        // 值输入区
        var value_area = document.createElement('span');
        value_area.className = 'condition-value-area';
        // 默认单值输入
        var value_input = document.createElement('input');
        value_input.type = 'text';
        value_input.className = 'form-control condition-value';
        if (value) value_input.value = value;
        value_area.appendChild(value_input);
        row.appendChild(value_area);

        // 删除按钮（非第一行才显示）
        if (existing_rows.length > 0) {
            var btn_remove = document.createElement('button');
            btn_remove.className = 'btn btn-sm btn-remove-condition';
            btn_remove.textContent = '删除';
            btn_remove.addEventListener('click', function() {
                row.parentNode.removeChild(row);
            });
            row.appendChild(btn_remove);
        }

        condition_builder.appendChild(row);

        // 运算符切换事件
        operator_select.addEventListener('change', function() {
            update_value_area(row, this.value);
        });

        // 如果传入了operator，立即更新值输入区
        if (operator) {
            update_value_area(row, operator);
            // 填充值
            if (operator === 'BETWEEN' && value && value_to) {
                var from_input = row.querySelector('.condition-value-from');
                var to_input = row.querySelector('.condition-value-to');
                if (from_input) from_input.value = value;
                if (to_input) to_input.value = value_to;
            } else {
                var val_input = row.querySelector('.condition-value');
                if (val_input && value) val_input.value = value;
            }
        }
    }

    function update_value_area(row, operator) {
        var value_area = row.querySelector('.condition-value-area');
        value_area.innerHTML = '';

        if (operator === 'IS_NULL' || operator === 'IS_NOT_NULL') {
            // 无需输入值
            return;
        }

        if (operator === 'BETWEEN') {
            var from_input = document.createElement('input');
            from_input.type = 'text';
            from_input.className = 'form-control condition-value-from';
            from_input.placeholder = '最小值';
            value_area.appendChild(from_input);

            var tilde = document.createTextNode(' ~ ');
            value_area.appendChild(tilde);

            var to_input = document.createElement('input');
            to_input.type = 'text';
            to_input.className = 'form-control condition-value-to';
            to_input.placeholder = '最大值';
            value_area.appendChild(to_input);
            return;
        }

        var value_input = document.createElement('input');
        value_input.type = 'text';
        value_input.className = 'form-control condition-value';
        if (operator === 'IN' || operator === 'NOT_IN') {
            value_input.placeholder = '多个值用英文逗号分隔';
        } else if (operator === 'LIKE') {
            value_input.placeholder = '如：%张%';
        }
        value_area.appendChild(value_input);

        if (operator === 'IN' || operator === 'NOT_IN') {
            var hint = document.createElement('span');
            hint.className = 'condition-hint';
            hint.textContent = '多个值用英文逗号分隔';
            value_area.appendChild(hint);
        }
    }

    // 快捷筛选按钮
    var quick_filter_btns = document.querySelectorAll('.quick-filter-btn');
    for (var i = 0; i < quick_filter_btns.length; i++) {
        quick_filter_btns[i].addEventListener('click', function() {
            var preset = this.getAttribute('data-preset');
            apply_preset(preset);
        });
    }

    function apply_preset(preset) {
        // 清空现有条件
        condition_builder.innerHTML = '';

        switch (preset) {
            case 'cs_2022':
                add_condition_row('major', '=', '计算机', '', 'AND', false);
                add_condition_row('grade', '=', '2022', '', '', false);
                break;
            case 'cs_or_se':
                add_condition_row('major', '=', '计算机', '', 'OR', false);
                add_condition_row('major', '=', '软件工程', '', '', false);
                break;
            case 'not_cs':
                add_condition_row('major', '=', '计算机', '', '', true);  // NOT
                break;
            case 'age_18_22':
                add_condition_row('age', 'BETWEEN', '18', '22', '', false);
                break;
            case 'name_zhang':
                add_condition_row('student_name', 'LIKE', '%张%', '', '', false);
                break;
            case 'no_class':
                add_condition_row('class_name', 'IS_NULL', '', '', '', false);
                break;
            case 'major_in':
                add_condition_row('major', 'IN', '计算机,自动化,汉语言', '', '', false);
                break;
        }
        // 自动执行查询
        execute_condition_query();
    }

    // 查询按钮
    var btn_query = document.getElementById('btn-condition-query');
    btn_query.addEventListener('click', function() {
        execute_condition_query();
    });

    function execute_condition_query(export_mode) {
        var rows = condition_builder.querySelectorAll('.condition-row');
        var conditions = [];

        for (var i = 0; i < rows.length; i++) {
            var row = rows[i];
            var field = row.querySelector('.condition-field');
            var operator = row.querySelector('.condition-operator');
            var not_checkbox = row.querySelector('.condition-not');
            var logic = row.querySelector('.condition-logic');

            if (!field || !operator) continue;

            var condition = {
                field: field.value,
                operator: operator.value,
                not: not_checkbox ? not_checkbox.checked : false,
                logic: logic ? logic.value : ''
            };

            // 获取值
            if (operator.value === 'BETWEEN') {
                var from = row.querySelector('.condition-value-from');
                var to = row.querySelector('.condition-value-to');
                condition.value = from ? from.value : '';
                condition.value_to = to ? to.value : '';
            } else if (operator.value !== 'IS_NULL' && operator.value !== 'IS_NOT_NULL') {
                var val = row.querySelector('.condition-value');
                condition.value = val ? val.value : '';
            } else {
                condition.value = '';
            }

            conditions.push(condition);
        }

        if (conditions.length === 0 && !export_mode) {
            alert('请至少添加一个查询条件');
            return;
        }

        var url = export_mode ? '/query/build' : '/query/build';
        var data = { conditions: conditions, export: !!export_mode };

        if (export_mode) {
            // 导出模式：POST后下载CSV
            export_condition_csv(conditions);
            return;
        }

        ajax_post(url, data, function(success, resp) {
            if (success) {
                render_condition_result(resp);
            } else {
                alert('查询失败');
            }
        }, true);
    }

    function export_condition_csv(conditions) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/query/build', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.responseType = 'blob';
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                hide_loading();
                if (xhr.status === 200) {
                    var blob = xhr.response;
                    var url = window.URL.createObjectURL(blob);
                    var a = document.createElement('a');
                    a.href = url;
                    a.download = 'student_data.csv';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                } else {
                    alert('导出失败');
                }
            }
        };
        show_loading();
        xhr.send(JSON.stringify({ conditions: conditions, export: true }));
    }

    // 重置按钮
    var btn_reset = document.getElementById('btn-condition-reset');
    btn_reset.addEventListener('click', function() {
        condition_builder.innerHTML = '';
        add_condition_row();
        // 隐藏结果区
        document.getElementById('condition-sql').classList.remove('sql-visible');
        document.getElementById('condition-result').style.display = 'none';
        document.getElementById('condition-empty').classList.remove('empty-visible');
    });

    // 导出按钮
    var btn_export = document.getElementById('btn-condition-export');
    btn_export.addEventListener('click', function() {
        var rows = condition_builder.querySelectorAll('.condition-row');
        if (rows.length === 0) {
            alert('请先执行查询');
            return;
        }
        execute_condition_query(true);
    });

    // 渲染条件查询结果
    var current_condition_sql = '';

    function render_condition_result(resp) {
        var sql_box = document.getElementById('condition-sql');
        var result_wrapper = document.getElementById('condition-result');
        var empty_box = document.getElementById('condition-empty');
        var table = document.getElementById('condition-table');

        current_condition_sql = resp.sql || '';

        // 展示SQL
        sql_box.innerHTML = highlight_sql(resp.sql || '');
        sql_box.classList.add('sql-visible');

        // 构建表格
        var columns = resp.columns || [];
        var data = resp.data || [];

        if (data.length === 0) {
            result_wrapper.style.display = 'none';
            empty_box.classList.add('empty-visible');
            return;
        }

        empty_box.classList.remove('empty-visible');
        result_wrapper.style.display = 'block';

        var thead = '<thead><tr>';
        for (var i = 0; i < columns.length; i++) {
            thead += '<th>' + escape_html(columns[i]) + '</th>';
        }
        thead += '</tr></thead>';

        var tbody = '<tbody>';
        for (var r = 0; r < data.length; r++) {
            tbody += '<tr>';
            for (var c = 0; c < columns.length; c++) {
                var val = data[r][columns[c]];
                tbody += '<td>' + escape_html(val !== null && val !== undefined ? String(val) : '') + '</td>';
            }
            tbody += '</tr>';
        }
        tbody += '</tbody>';

        table.innerHTML = thead + tbody;
    }

    /* ---------- 3. 统计分析逻辑 ---------- */
    var stat_cards = document.querySelectorAll('.stat-card');
    var current_stat_sql = '';

    for (var i = 0; i < stat_cards.length; i++) {
        stat_cards[i].addEventListener('click', function() {
            // 移除其他卡片的active
            for (var j = 0; j < stat_cards.length; j++) {
                stat_cards[j].classList.remove('stat-card-active');
            }
            this.classList.add('stat-card-active');

            var scene = this.getAttribute('data-scene');
            execute_stat_query(scene);
        });
    }

    function execute_stat_query(scene) {
        ajax_post('/query/stat', { scene: scene }, function(success, resp) {
            if (success) {
                render_stat_result(resp);
            } else {
                alert('查询失败');
            }
        }, true);
    }

    function render_stat_result(resp) {
        var sql_box = document.getElementById('stat-sql');
        var result_wrapper = document.getElementById('stat-result');
        var empty_box = document.getElementById('stat-empty');
        var table = document.getElementById('stat-table');
        var btn_export = document.getElementById('btn-stat-export');

        current_stat_sql = resp.sql || '';

        sql_box.innerHTML = highlight_sql(resp.sql || '');
        sql_box.classList.add('sql-visible');

        var columns = resp.columns || [];
        var data = resp.data || [];

        if (data.length === 0) {
            result_wrapper.style.display = 'none';
            btn_export.style.display = 'none';
            empty_box.classList.add('empty-visible');
            return;
        }

        empty_box.classList.remove('empty-visible');
        result_wrapper.style.display = 'block';
        btn_export.style.display = 'inline-block';

        var thead = '<thead><tr>';
        for (var i = 0; i < columns.length; i++) {
            thead += '<th>' + escape_html(columns[i]) + '</th>';
        }
        thead += '</tr></thead>';

        var tbody = '<tbody>';
        for (var r = 0; r < data.length; r++) {
            tbody += '<tr>';
            for (var c = 0; c < columns.length; c++) {
                var val = data[r][columns[c]];
                if (typeof val === 'number' && !Number.isInteger(val)) {
                    val = val.toFixed(2);
                }
                tbody += '<td>' + escape_html(val !== null && val !== undefined ? String(val) : '') + '</td>';
            }
            tbody += '</tr>';
        }
        tbody += '</tbody>';

        table.innerHTML = thead + tbody;
    }

    // 统计导出
    var btn_stat_export = document.getElementById('btn-stat-export');
    if (btn_stat_export) {
        btn_stat_export.addEventListener('click', function() {
            if (!current_stat_sql) {
                alert('请先执行统计查询');
                return;
            }
            window.location.href = '/csv/export_filtered?sql=' + encodeURIComponent(current_stat_sql);
        });
    }

    /* ---------- 4. 排序浏览逻辑 ---------- */
    var sort_loaded = false;
    var sort_state = { field: 'student_no', order: 'asc', page: 1 };
    var sort_total = 0;
    var sort_total_pages = 0;

    function load_sort_data() {
        ajax_post('/query/sort', {
            sort_field: sort_state.field,
            sort_order: sort_state.order,
            page: sort_state.page
        }, function(success, resp) {
            if (success) {
                render_sort_result(resp);
                sort_loaded = true;
            } else {
                alert('加载失败');
            }
        }, true);
    }

    function render_sort_result(resp) {
        var sql_box = document.getElementById('sort-sql');
        var empty_box = document.getElementById('sort-empty');
        var table = document.getElementById('sort-table');
        var page_info = document.getElementById('page-info');
        var btn_prev = document.getElementById('page-prev');
        var btn_next = document.getElementById('page-next');

        sql_box.innerHTML = highlight_sql(resp.sql || '');
        sql_box.classList.add('sql-visible');

        var columns = resp.columns || [];
        var data = resp.data || [];
        sort_total = resp.total || 0;
        sort_total_pages = resp.total_pages || 0;

        if (data.length === 0) {
            table.style.display = 'none';
            empty_box.classList.add('empty-visible');
            return;
        }

        empty_box.classList.remove('empty-visible');
        table.style.display = 'table';

        // 列头
        var field_labels = {
            'student_no': '学号', 'student_name': '姓名', 'gender': '性别',
            'age': '年龄', 'major': '专业', 'grade': '年级', 'class_name': '班级'
        };

        var thead = '<thead><tr>';
        for (var i = 0; i < columns.length; i++) {
            var field = columns[i];
            var label = field_labels[field] || field;
            var arrow = '';
            var cls = 'sort-header';
            if (field === sort_state.field) {
                arrow = sort_state.order === 'asc' ? ' ↑' : (sort_state.order === 'desc' ? ' ↓' : '');
                cls += ' sort-active';
            }
            thead += '<th class="' + cls + '" data-field="' + field + '">' + escape_html(label) + '<span class="sort-arrow">' + arrow + '</span></th>';
        }
        thead += '</tr></thead>';

        var tbody = '<tbody>';
        for (var r = 0; r < data.length; r++) {
            tbody += '<tr>';
            for (var c = 0; c < columns.length; c++) {
                var val = data[r][columns[c]];
                tbody += '<td>' + escape_html(val !== null && val !== undefined ? String(val) : '') + '</td>';
            }
            tbody += '</tr>';
        }
        tbody += '</tbody>';

        table.innerHTML = thead + tbody;

        // 绑定列头排序事件
        var headers = table.querySelectorAll('.sort-header');
        for (var h = 0; h < headers.length; h++) {
            headers[h].addEventListener('click', function() {
                var field = this.getAttribute('data-field');
                if (sort_state.field === field) {
                    if (sort_state.order === 'asc') {
                        sort_state.order = 'desc';
                    } else if (sort_state.order === 'desc') {
                        sort_state.order = 'none';
                        sort_state.field = 'student_no';
                        sort_state.order = 'asc';
                    }
                } else {
                    sort_state.field = field;
                    sort_state.order = 'asc';
                }
                sort_state.page = 1;
                load_sort_data();
            });
        }

        // 分页信息
        page_info.textContent = '第 ' + sort_state.page + ' 页 / 共 ' + sort_total_pages + ' 页';
        btn_prev.disabled = sort_state.page <= 1;
        btn_next.disabled = sort_state.page >= sort_total_pages;
    }

    // 分页按钮
    document.getElementById('page-prev').addEventListener('click', function() {
        if (sort_state.page > 1) {
            sort_state.page--;
            load_sort_data();
        }
    });

    document.getElementById('page-next').addEventListener('click', function() {
        if (sort_state.page < sort_total_pages) {
            sort_state.page++;
            load_sort_data();
        }
    });

    /* ---------- 5. SQL实训逻辑 ---------- */
    // 手风琴展开/收起
    var accordion_titles = document.querySelectorAll('.accordion-title');
    for (var i = 0; i < accordion_titles.length; i++) {
        accordion_titles[i].addEventListener('click', function() {
            var item = this.parentNode;
            // 收起其他
            var all_items = document.querySelectorAll('.accordion-item');
            for (var j = 0; j < all_items.length; j++) {
                if (all_items[j] !== item) {
                    all_items[j].classList.remove('accordion-open');
                }
            }
            item.classList.toggle('accordion-open');
        });
    }

    // 关键字卡片展开/收起
    var keyword_headers = document.querySelectorAll('.keyword-header');
    for (var i = 0; i < keyword_headers.length; i++) {
        keyword_headers[i].addEventListener('click', function() {
            var card = this.parentNode;
            card.classList.toggle('keyword-open');

            // 如果展开且内容为空，加载关键字详情
            if (card.classList.contains('keyword-open')) {
                var detail = card.querySelector('.keyword-detail');
                if (detail && !detail.getAttribute('data-loaded')) {
                    var keyword = card.getAttribute('data-keyword');
                    load_keyword_detail(keyword, detail);
                }
            }
        });
    }

    function load_keyword_detail(keyword, detail_el) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/query/keyword?keyword=' + encodeURIComponent(keyword), true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    var resp = JSON.parse(xhr.responseText);
                    render_keyword_detail(resp, detail_el);
                    detail_el.setAttribute('data-loaded', 'true');
                }
            }
        };
        xhr.send();
    }

    function render_keyword_detail(info, detail_el) {
        var html = '';

        // 用途说明
        html += '<div class="keyword-desc">' + escape_html(info.description || '') + '</div>';

        // 示例SQL
        if (info.sql) {
            html += '<div class="sql-display-box sql-visible">' + highlight_sql(info.sql) + '</div>';
        }

        // 执行按钮（仅可执行的关键字）
        if (info.executable) {
            var is_admin = document.querySelector('.role-badge-admin') !== null;
            html += '<button class="btn btn-primary btn-keyword-execute" data-keyword="' + escape_html(info.keyword || '') + '"' + (is_admin ? '' : ' disabled title="仅管理员可执行"') + '>执行</button>';
        }
        if (info.keyword === 'DROP_DATABASE' || info.keyword === 'DROP_TABLE') {
            html += '<span class="keyword-danger-tag">危险</span>';
        }

        detail_el.innerHTML = html;

        // 绑定执行按钮事件
        var exec_btn = detail_el.querySelector('.btn-keyword-execute');
        if (exec_btn && !exec_btn.disabled) {
            exec_btn.addEventListener('click', function() {
                var kw = this.getAttribute('data-keyword');
                // 危险操作二次确认
                if (kw === 'DROP_DATABASE' || kw === 'DROP_TABLE') {
                    show_danger_confirm(kw);
                } else {
                    execute_keyword(kw);
                }
            });
        }
    }

    function execute_keyword(keyword) {
        ajax_post('/query/keyword/execute', { keyword: keyword }, function(success, resp) {
            if (success) {
                alert(resp.message || (resp.success ? '执行成功' : '执行失败'));
            } else {
                alert('执行失败');
            }
        }, true);
    }

    function show_danger_confirm(keyword) {
        var overlay = document.getElementById('confirm-overlay');
        var msg = document.getElementById('confirm-message');
        var keyword_text = keyword === 'DROP_DATABASE' ? 'DROP DATABASE（删除数据库）' : 'DROP TABLE（删除数据表）';
        msg.textContent = '即将执行危险操作：' + keyword_text + '，该操作不可恢复，是否确认？';
        overlay.style.display = 'flex';

        var btn_yes = document.getElementById('btn-confirm-yes');
        var btn_no = document.getElementById('btn-confirm-no');

        var new_yes = btn_yes.cloneNode(true);
        var new_no = btn_no.cloneNode(true);
        btn_yes.parentNode.replaceChild(new_yes, btn_yes);
        btn_no.parentNode.replaceChild(new_no, btn_no);

        new_yes.addEventListener('click', function() {
            overlay.style.display = 'none';
            execute_keyword(keyword);
        });

        new_no.addEventListener('click', function() {
            overlay.style.display = 'none';
        });
    }

    /* ---------- 6. SQL关键字高亮渲染函数 ---------- */
    function highlight_sql(sql) {
        if (!sql) return '';
        var keywords = [
            'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'BETWEEN',
            'LIKE', 'IS NULL', 'IS NOT NULL', 'GROUP BY', 'HAVING', 'ORDER BY',
            'ASC', 'DESC', 'LIMIT', 'DISTINCT', 'AS', 'COUNT', 'SUM', 'AVG',
            'MAX', 'MIN', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE',
            'CREATE', 'DROP', 'ALTER', 'TABLE', 'DATABASE', 'PRIMARY KEY',
            'AUTO_INCREMENT', 'UNIQUE', 'NOT NULL', 'DEFAULT', 'COMMENT',
            'ENGINE', 'CHARSET', 'BEGIN', 'COMMIT', 'ROLLBACK', 'IF EXISTS',
            'IF NOT EXISTS', 'CURRENT_TIMESTAMP'
        ];

        // 先转义HTML
        var escaped = escape_html(sql);

        // 按关键字长度降序排列，避免短关键字匹配到长关键字的一部分
        keywords.sort(function(a, b) { return b.length - a.length; });

        for (var i = 0; i < keywords.length; i++) {
            var kw = keywords[i];
            var regex = new RegExp('\\b' + kw.replace(/ /g, '\\s+') + '\\b', 'gi');
            escaped = escaped.replace(regex, '<span class="sql-keyword-highlight">$&</span>');
        }

        return escaped;
    }

    /* ---------- 7. 初始化 ---------- */
    // 初始化：添加第一行条件
    add_condition_row();
})();
