/* ========== 侧边栏折叠/展开 ========== */

function toggleSidebar() {
    var sidebar = document.getElementById('sidebar');
    var mainWrapper = document.getElementById('main-wrapper');
    if (sidebar && mainWrapper) {
        sidebar.classList.toggle('collapsed');
        mainWrapper.classList.toggle('expanded');
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    }
}

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
}

/**
 * 隐藏消息
 * @param {string} element_id - 目标元素ID
 */
function hide_msg(element_id) {
  var el = document.getElementById(element_id);
  if (!el) return;

  el.className = "";
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

/* ========== CSV解析与验证 ========== */

/**
 * 解析CSV文本内容
 * @param {string} text - CSV原始文本
 * @returns {{headers: string[], rows: string[][], errors: string[]}}
 */
function parse_csv_content(text) {
    var lines = text.split('\n');
    var headers = [];
    var data_rows = [];
    var errors = [];

    for (var i = 0; i < lines.length; i++) {
        var line = lines[i].trim();
        if (line === '') continue;

        var cells = line.split(',');
        // 去除每个单元格的引号和首尾空格
        cells = cells.map(function(c) {
            c = c.trim();
            if ((c.startsWith('"') && c.endsWith('"')) || (c.startsWith("'") && c.endsWith("'"))) {
                c = c.slice(1, -1);
            }
            return c;
        });

        if (i === 0) {
            headers = cells;
        } else {
            data_rows.push(cells);
        }
    }

    return {headers: headers, rows: data_rows, errors: errors};
}

/**
 * 验证CSV解析后的数据行
 * @param {string[][]} rows - CSV数据行（不含表头）
 * @returns {{valid_data: string[][], errors: string[]}}
 */
function validate_csv_data(rows) {
    var valid_data = [];
    var errors = [];
    var seen_student_no = {};

    for (var i = 0; i < rows.length; i++) {
        var row = rows[i];
        var row_num = i + 2;  // +2 because header is row 1, 0-indexed
        var row_errors = [];

        // 学号非空校验（索引0）
        if (!row[0] || row[0].trim() === '') {
            row_errors.push('第' + row_num + '行：学号不能为空');
        }
        // 学号重复校验
        else if (seen_student_no[row[0].trim()]) {
            row_errors.push('第' + row_num + '行：学号 "' + row[0].trim() + '" 在文件中重复');
        }

        // 年龄数字校验（索引3）
        if (row[3] && row[3].trim() !== '') {
            var age_val = Number(row[3].trim());
            if (isNaN(age_val) || !Number.isInteger(age_val) || age_val < 0 || age_val > 150) {
                row_errors.push('第' + row_num + '行：年龄 "' + row[3].trim() + '" 不是有效的整数（0-150）');
            }
        }

        if (row_errors.length === 0) {
            if (row[0] && row[0].trim() !== '') {
                seen_student_no[row[0].trim()] = true;
            }
            valid_data.push(row);
        } else {
            errors = errors.concat(row_errors);
        }
    }

    return {valid_data: valid_data, errors: errors};
}

/* ========== 查询页面交互逻辑 ========== */
(function() {
    // 仅在查询页面执行（检查新的筛选查询面板）
    if (!document.getElementById('panel-filter')) return;

    /* ---------- 1. Tab 面板切换逻辑 ---------- */
    var tab_items = document.querySelectorAll('.tab-item');
    var panels = {
        'filter': document.getElementById('panel-filter'),
        'stat': document.getElementById('panel-stat'),
        'sort': document.getElementById('panel-sort'),
        'training': document.getElementById('panel-training')
    };

    for (var i = 0; i < tab_items.length; i++) {
        tab_items[i].addEventListener('click', function() {
            var target = this.getAttribute('data-tab');
            for (var j = 0; j < tab_items.length; j++) {
                tab_items[j].classList.remove('tab-active');
            }
            this.classList.add('tab-active');
            for (var key in panels) {
                if (panels.hasOwnProperty(key)) {
                    panels[key].classList.remove('panel-active');
                }
            }
            panels[target].classList.add('panel-active');
        });
    }

    /* ---------- 2. 筛选查询逻辑 ---------- */
    // 口语化筛选条件配置
    var FILTER_CONFIG = {
        'student_no': {label: '学号', type: 'text', operators: {'equals': '是', 'contains': '包含'}},
        'student_name': {label: '姓名', type: 'text', operators: {'equals': '是', 'contains': '包含'}},
        'gender': {label: '性别', type: 'gender', operators: {'equals': '是'}},
        'age': {label: '年龄', type: 'number', operators: {'equals': '是', 'gt': '大于', 'lt': '小于', 'between': '在...到...之间'}},
        'dept_name': {label: '学院', type: 'multi_select', operators: {'in': '在...中'}},
        'major_name': {label: '专业', type: 'text', operators: {'equals': '是', 'contains': '包含'}},
        'grade': {label: '年级', type: 'text', operators: {'equals': '是'}},
        'class_name': {label: '班级', type: 'multi_select', operators: {'in': '在...中'}}
    };

    // 多选数据源
    var multiSelectData = {
        'dept_name': [],
        'class_name': []
    };

    // 当前筛选项计数
    var filterItemCount = 0;
    var currentFilterSQL = '';
    var currentFilterPage = 1;
    var currentFilterParams = null;

    // 加载学院和班级列表数据
    function loadMultiSelectData() {
        // 加载学院列表
        var xhr1 = new XMLHttpRequest();
        xhr1.open('GET', '/api/departments', true);
        xhr1.onreadystatechange = function() {
            if (xhr1.readyState === 4 && xhr1.status === 200) {
                try {
                    var resp = JSON.parse(xhr1.responseText);
                    if (resp.ok && resp.data) {
                        multiSelectData.dept_name = resp.data;
                    }
                } catch (e) {}
            }
        };
        xhr1.send();

        // 加载班级列表
        var xhr2 = new XMLHttpRequest();
        xhr2.open('GET', '/api/classes', true);
        xhr2.onreadystatechange = function() {
            if (xhr2.readyState === 4 && xhr2.status === 200) {
                try {
                    var resp = JSON.parse(xhr2.responseText);
                    if (resp.ok && resp.data) {
                        multiSelectData.class_name = resp.data;
                    }
                } catch (e) {}
            }
        };
        xhr2.send();
    }

    // 初始化加载多选数据
    loadMultiSelectData();

    // 快捷场景按钮点击事件
    var sceneButtons = document.querySelectorAll('.filter-scene-btn');
    for (var i = 0; i < sceneButtons.length; i++) {
        sceneButtons[i].addEventListener('click', function() {
            var scene = this.getAttribute('data-scene');
            applyScenePreset(scene);
        });
    }

    // 快捷场景预设
    function applyScenePreset(scene) {
        // 清空现有筛选项
        clearAllFilterItems();

        switch (scene) {
            case 'cs_2022':
                // 计算机学院2022级
                addFilterItem('dept_name', 'in', ['计算机学院']);
                addFilterItem('grade', 'equals', '2022');
                break;
            case 'age_18_22':
                // 18-22岁
                addFilterItem('age', 'between', ['18', '22']);
                break;
            case 'name_zhang':
                // 姓名包含"张"
                addFilterItem('student_name', 'contains', '张');
                break;
            case 'male':
                // 男生
                addFilterItem('gender', 'equals', '男');
                break;
            case 'female':
                // 女生
                addFilterItem('gender', 'equals', '女');
                break;
        }
    }

    // 添加筛选项
    function addFilterItem(field, operator, value) {
        var container = document.getElementById('filter-items-container');
        if (!container) return;

        filterItemCount++;
        var itemId = 'filter-item-' + filterItemCount;

        var config = FILTER_CONFIG[field];
        if (!config) return;

        var html = '<div class="filter-item" id="' + itemId + '" data-field="' + field + '">';
        html += '<span class="filter-item-label">' + escape_html(config.label) + '</span>';
        html += '<span class="filter-item-operator">' + escape_html(config.operators[operator] || operator) + '</span>';
        html += '<span class="filter-item-value">' + formatFilterValue(value) + '</span>';
        html += '<button class="filter-item-remove" data-item="' + itemId + '">×</button>';
        html += '<input type="hidden" class="filter-field" value="' + field + '">';
        html += '<input type="hidden" class="filter-operator" value="' + operator + '">';
        html += '<input type="hidden" class="filter-value" value="' + escape_html(JSON.stringify(value)) + '">';
        html += '</div>';

        container.insertAdjacentHTML('beforeend', html);

        // 绑定删除按钮事件
        var removeBtn = container.querySelector('#' + itemId + ' .filter-item-remove');
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                var item = document.getElementById(this.getAttribute('data-item'));
                if (item) item.remove();
            });
        }
    }

    // 格式化筛选值显示
    function formatFilterValue(value) {
        if (Array.isArray(value)) {
            return escape_html(value.join('、'));
        }
        return escape_html(String(value));
    }

    // 清空所有筛选项
    function clearAllFilterItems() {
        var container = document.getElementById('filter-items-container');
        if (container) container.innerHTML = '';
        filterItemCount = 0;
    }

    // 动态添加筛选项按钮
    var btnAddFilter = document.getElementById('btn-add-filter');
    if (btnAddFilter) {
        btnAddFilter.addEventListener('click', function() {
            showFilterSelector();
        });
    }

    // 显示筛选条件选择器
    function showFilterSelector() {
        var selector = document.getElementById('filter-field-selector');
        if (selector) {
            selector.classList.remove('hidden');
            selector.removeAttribute('style');
            // 重置选择器
            var fieldSelect = document.getElementById('filter-field-select');
            var operatorSelect = document.getElementById('filter-operator-select');
            if (fieldSelect) fieldSelect.value = '';
            if (operatorSelect) {
                operatorSelect.innerHTML = '<option value="">请选择运算符</option>';
                operatorSelect.disabled = true;
            }
            // 清空值输入区
            var valueContainer = document.getElementById('filter-value-container');
            if (valueContainer) valueContainer.innerHTML = '';
        }
    }

    // 字段选择变化事件
    var fieldSelect = document.getElementById('filter-field-select');
    if (fieldSelect) {
        fieldSelect.addEventListener('change', function() {
            var field = this.value;
            var operatorSelect = document.getElementById('filter-operator-select');
            var valueContainer = document.getElementById('filter-value-container');

            if (!field) {
                if (operatorSelect) {
                    operatorSelect.innerHTML = '<option value="">请选择运算符</option>';
                    operatorSelect.disabled = true;
                }
                if (valueContainer) valueContainer.innerHTML = '';
                return;
            }

            var config = FILTER_CONFIG[field];
            if (config && operatorSelect) {
                var html = '<option value="">请选择运算符</option>';
                for (var op in config.operators) {
                    if (config.operators.hasOwnProperty(op)) {
                        html += '<option value="' + op + '">' + escape_html(config.operators[op]) + '</option>';
                    }
                }
                operatorSelect.innerHTML = html;
                operatorSelect.disabled = false;
            }

            if (valueContainer) valueContainer.innerHTML = '';
        });
    }

    // 运算符选择变化事件
    var operatorSelect = document.getElementById('filter-operator-select');
    if (operatorSelect) {
        operatorSelect.addEventListener('change', function() {
            var field = fieldSelect ? fieldSelect.value : '';
            var operator = this.value;
            var valueContainer = document.getElementById('filter-value-container');

            if (!field || !operator || !valueContainer) return;

            var config = FILTER_CONFIG[field];
            if (!config) return;

            renderValueInput(valueContainer, field, operator, config.type);
        });
    }

    // 根据字段类型渲染值输入组件
    function renderValueInput(container, field, operator, type) {
        var html = '';

        switch (type) {
            case 'text':
                html = '<input type="text" id="filter-input-value" class="form-control" placeholder="请输入' + FILTER_CONFIG[field].label + '">';
                break;
            case 'gender':
                html = '<div class="radio-group">';
                html += '<label><input type="radio" name="filter-gender" value="男" checked> 男</label>';
                html += '<label><input type="radio" name="filter-gender" value="女"> 女</label>';
                html += '</div>';
                break;
            case 'number':
                if (operator === 'between') {
                    html = '<div class="range-input">';
                    html += '<input type="number" id="filter-input-value1" class="form-control" placeholder="最小值" min="0" max="150">';
                    html += '<span class="range-separator">至</span>';
                    html += '<input type="number" id="filter-input-value2" class="form-control" placeholder="最大值" min="0" max="150">';
                    html += '</div>';
                } else {
                    html = '<input type="number" id="filter-input-value" class="form-control" placeholder="请输入' + FILTER_CONFIG[field].label + '" min="0" max="150">';
                }
                break;
            case 'multi_select':
                html = renderMultiSelect(field);
                break;
        }

        container.innerHTML = html;

        // 绑定多选下拉框事件
        if (type === 'multi_select') {
            bindMultiSelectEvents(container, field);
        }
    }

    // 渲染多选下拉框
    function renderMultiSelect(field) {
        var data = multiSelectData[field] || [];
        var html = '<div class="multi-select-dropdown">';
        html += '<div class="multi-select-trigger" id="multi-select-trigger">';
        html += '<span class="multi-select-placeholder">请选择' + FILTER_CONFIG[field].label + '</span>';
        html += '<span class="multi-select-arrow">▼</span>';
        html += '</div>';
        html += '<div class="multi-select-options" id="multi-select-options" style="display:none;">';

        for (var i = 0; i < data.length; i++) {
            html += '<div class="multi-select-option" data-value="' + escape_html(data[i]) + '">';
            html += '<input type="checkbox" value="' + escape_html(data[i]) + '"> ';
            html += escape_html(data[i]);
            html += '</div>';
        }

        html += '</div>';
        html += '<div class="multi-select-selected" id="multi-select-selected"></div>';
        html += '</div>';

        return html;
    }

    // 绑定多选下拉框交互事件
    function bindMultiSelectEvents(container, field) {
        var trigger = container.querySelector('#multi-select-trigger');
        var options = container.querySelector('#multi-select-options');
        var selected = container.querySelector('#multi-select-selected');

        if (!trigger || !options) return;

        // 展开/收起下拉框
        trigger.addEventListener('click', function(e) {
            e.stopPropagation();
            var isVisible = !options.classList.contains('hidden');
            if (isVisible) {
                options.classList.add('hidden');
            } else {
                options.classList.remove('hidden');
                options.removeAttribute('style');
            }
            trigger.classList.toggle('open', !isVisible);
        });

        // 选项选择事件
        var optionItems = options.querySelectorAll('.multi-select-option');
        for (var i = 0; i < optionItems.length; i++) {
            optionItems[i].addEventListener('click', function(e) {
                e.stopPropagation();
                var checkbox = this.querySelector('input[type="checkbox"]');
                checkbox.checked = !checkbox.checked;
                this.classList.toggle('selected', checkbox.checked);
                updateMultiSelectDisplay(selected, options);
            });
        }

        // 点击外部关闭下拉框
        document.addEventListener('click', function(e) {
            if (!container.contains(e.target)) {
                options.classList.add('hidden');
                trigger.classList.remove('open');
            }
        });
    }

    // 更新多选显示
    function updateMultiSelectDisplay(selectedContainer, optionsContainer) {
        if (!selectedContainer || !optionsContainer) return;

        var checked = optionsContainer.querySelectorAll('input[type="checkbox"]:checked');
        var values = [];
        for (var i = 0; i < checked.length; i++) {
            values.push(checked[i].value);
        }

        if (values.length === 0) {
            selectedContainer.innerHTML = '';
        } else {
            var html = '';
            for (var j = 0; j < values.length; j++) {
                html += '<span class="multi-select-tag">' + escape_html(values[j]) + '</span>';
            }
            selectedContainer.innerHTML = html;
        }
    }

    // 确认添加筛选项
    var btnConfirmFilter = document.getElementById('btn-confirm-filter');
    if (btnConfirmFilter) {
        btnConfirmFilter.addEventListener('click', function() {
            var field = fieldSelect ? fieldSelect.value : '';
            var operator = operatorSelect ? operatorSelect.value : '';

            if (!field || !operator) {
                alert('请选择字段和运算符');
                return;
            }

            var config = FILTER_CONFIG[field];
            var value = getFilterValue(field, operator, config.type);

            if (value === null || value === undefined || value === '') {
                alert('请输入筛选值');
                return;
            }

            if (Array.isArray(value) && value.length === 0) {
                alert('请至少选择一个选项');
                return;
            }

            addFilterItem(field, operator, value);

            // 隐藏选择器
            var selector = document.getElementById('filter-field-selector');
            if (selector) selector.classList.add('hidden');
        });
    }

    // 取消添加筛选项
    var btnCancelFilter = document.getElementById('btn-cancel-filter');
    if (btnCancelFilter) {
        btnCancelFilter.addEventListener('click', function() {
            var selector = document.getElementById('filter-field-selector');
            if (selector) selector.classList.add('hidden');
        });
    }

    // 获取筛选值
    function getFilterValue(field, operator, type) {
        switch (type) {
            case 'text':
            case 'number':
                if (operator === 'between') {
                    var val1 = document.getElementById('filter-input-value1');
                    var val2 = document.getElementById('filter-input-value2');
                    if (val1 && val2) {
                        return [val1.value.trim(), val2.value.trim()];
                    }
                } else {
                    var input = document.getElementById('filter-input-value');
                    if (input) return input.value.trim();
                }
                break;
            case 'gender':
                var radios = document.getElementsByName('filter-gender');
                for (var i = 0; i < radios.length; i++) {
                    if (radios[i].checked) return radios[i].value;
                }
                break;
            case 'multi_select':
                var options = document.getElementById('multi-select-options');
                if (options) {
                    var checked = options.querySelectorAll('input[type="checkbox"]:checked');
                    var values = [];
                    for (var j = 0; j < checked.length; j++) {
                        values.push(checked[j].value);
                    }
                    return values;
                }
                break;
        }
        return null;
    }

    // 查询按钮逻辑
    var btnFilterQuery = document.getElementById('btn-filter-query');
    if (btnFilterQuery) {
        btnFilterQuery.addEventListener('click', function() {
            executeFilterQuery(1);
        });
    }

    // 执行筛选查询
    function executeFilterQuery(page) {
        var filters = collectFilters();
        if (filters.length === 0) {
            alert('请至少添加一个筛选条件');
            return;
        }

        currentFilterParams = { filters: filters, page: page };
        currentFilterPage = page;

        show_loading();
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/query/filter', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                hide_loading();
                if (xhr.status === 200) {
                    try {
                        var resp = JSON.parse(xhr.responseText);
                        if (resp.ok) {
                            renderFilterResult(resp);
                        } else {
                            alert(resp.message || '查询失败');
                        }
                    } catch (e) {
                        alert('响应解析失败');
                    }
                } else {
                    alert('请求失败');
                }
            }
        };
        xhr.send(JSON.stringify(currentFilterParams));
    }

    // 收集所有筛选项
    function collectFilters() {
        var filters = [];
        var items = document.querySelectorAll('.filter-item');

        for (var i = 0; i < items.length; i++) {
            var field = items[i].getAttribute('data-field');
            var operatorInput = items[i].querySelector('.filter-operator');
            var valueInput = items[i].querySelector('.filter-value');;

            if (field && operatorInput && valueInput) {
                var value;
                try {
                    value = JSON.parse(valueInput.value);
                } catch (e) {
                    value = valueInput.value;
                }

                filters.push({
                    field: field,
                    operator: operatorInput.value,
                    value: value
                });
            }
        }

        return filters;
    }

    // 渲染筛选结果
    function renderFilterResult(resp) {
        currentFilterSQL = resp.sql || '';

        // 显示SQL
        var sqlBox = document.getElementById('filter-sql');
        if (sqlBox) {
            sqlBox.innerHTML = highlight_sql(resp.sql || '');
            sqlBox.classList.add('sql-visible');
        }

        // 显示结果表格
        var resultWrapper = document.getElementById('filter-result');
        var emptyBox = document.getElementById('filter-empty');
        var table = document.getElementById('filter-table');

        var columns = resp.columns || [];
        var data = resp.data || [];

        if (data.length === 0) {
            if (resultWrapper) { resultWrapper.classList.add('hidden'); }
            if (emptyBox) emptyBox.classList.add('empty-visible');
            return;
        }

        if (emptyBox) emptyBox.classList.remove('empty-visible');
        if (resultWrapper) { resultWrapper.classList.remove('hidden'); resultWrapper.removeAttribute('style'); }

        // 渲染表头
        var thead = '<thead><tr>';
        for (var i = 0; i < columns.length; i++) {
            thead += '<th>' + escape_html(columns[i]) + '</th>';
        }
        thead += '</tr></thead>';

        // 渲染表体
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

        if (table) table.innerHTML = thead + tbody;

        // 更新分页
        updateFilterPagination(resp.page || 1, resp.total_pages || 1);
    }

    // 更新分页控件
    function updateFilterPagination(currentPage, totalPages) {
        var pageInfo = document.getElementById('filter-page-info');
        var prevBtn = document.getElementById('filter-page-prev');
        var nextBtn = document.getElementById('filter-page-next');

        if (pageInfo) {
            pageInfo.textContent = '第 ' + currentPage + ' 页 / 共 ' + totalPages + ' 页';
        }

        if (prevBtn) {
            prevBtn.disabled = currentPage <= 1;
            prevBtn.onclick = function() {
                if (currentPage > 1) {
                    executeFilterQuery(currentPage - 1);
                }
            };
        }

        if (nextBtn) {
            nextBtn.disabled = currentPage >= totalPages;
            nextBtn.onclick = function() {
                if (currentPage < totalPages) {
                    executeFilterQuery(currentPage + 1);
                }
            };
        }
    }

    // 重置按钮逻辑
    var btnFilterReset = document.getElementById('btn-filter-reset');
    if (btnFilterReset) {
        btnFilterReset.addEventListener('click', function() {
            clearAllFilterItems();
            currentFilterSQL = '';
            currentFilterParams = null;

            var sqlBox = document.getElementById('filter-sql');
            var resultWrapper = document.getElementById('filter-result');
            var emptyBox = document.getElementById('filter-empty');

            if (sqlBox) {
                sqlBox.innerHTML = '';
                sqlBox.classList.remove('sql-visible');
            }
            if (resultWrapper) { resultWrapper.classList.add('hidden'); }
            if (emptyBox) emptyBox.classList.remove('empty-visible');
        });
    }

    // 导出按钮逻辑
    var btnFilterExport = document.getElementById('btn-filter-export');
    if (btnFilterExport) {
        btnFilterExport.addEventListener('click', function() {
            if (!currentFilterParams) {
                alert('请先执行查询');
                return;
            }

            show_loading();
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/query/filter', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.responseType = 'blob';
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    hide_loading();
                    if (xhr.status === 200) {
                        var blob = new Blob([xhr.response], {type: 'text/csv'});
                        var link = document.createElement('a');
                        link.href = URL.createObjectURL(blob);
                        link.download = 'filter_query_result.csv';
                        link.click();
                    } else {
                        alert('导出失败');
                    }
                }
            };
            var exportParams = JSON.parse(JSON.stringify(currentFilterParams));
            exportParams.export = true;
            xhr.send(JSON.stringify(exportParams));
        });
    }

    /* ---------- 3. 统计分析逻辑 ---------- */
    var stat_cards = document.querySelectorAll('.stat-card');
    var current_stat_sql = '';

    for (var i = 0; i < stat_cards.length; i++) {
        stat_cards[i].addEventListener('click', function() {
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

    /* ---------- 3.1 分类统计模块 - 快捷操作功能 ---------- */
    (function() {
        // 快捷操作配置
        var QUICK_ACTIONS = {
            'major_count': {
                label: '专业人数统计',
                description: '统计各专业学生人数，可设置人数阈值',
                params: [
                    { name: 'threshold', label: '人数阈值', type: 'number', placeholder: '例如：10', min: 0 }
                ]
            },
            'age_distribution': {
                label: '年龄分布统计',
                description: '按指定年龄段统计学生分布',
                params: [
                    { name: 'ages', label: '年龄段', type: 'text', placeholder: '例如：18,19,20,21,22' }
                ]
            },
            'grade_count': {
                label: '年级人数统计',
                description: '统计各年级学生人数',
                params: []
            },
            'dept_count': {
                label: '学院人数统计',
                description: '统计各学院学生人数',
                params: []
            },
            'custom_age_range': {
                label: '自定义年龄范围',
                description: '统计指定年龄范围内的学生',
                params: [
                    { name: 'min_age', label: '最小年龄', type: 'number', placeholder: '例如：18', min: 0, max: 150 },
                    { name: 'max_age', label: '最大年龄', type: 'number', placeholder: '例如：22', min: 0, max: 150 }
                ]
            }
        };

        var currentQuickAction = null;

        // 初始化快捷操作卡片
        function initQuickActionCards() {
            var container = document.getElementById('quick-action-cards');
            if (!container) return;

            var html = '';
            for (var actionKey in QUICK_ACTIONS) {
                if (QUICK_ACTIONS.hasOwnProperty(actionKey)) {
                    var action = QUICK_ACTIONS[actionKey];
                    html += '<div class="quick-action-card" data-action="' + actionKey + '">';
                    html += '<div class="quick-action-header">';
                    html += '<span class="quick-action-title">' + escape_html(action.label) + '</span>';
                    html += '<span class="quick-action-toggle">▼</span>';
                    html += '</div>';
                    html += '<div class="quick-action-body" style="display:none;">';
                    html += '<p class="quick-action-desc">' + escape_html(action.description) + '</p>';

                    if (action.params.length > 0) {
                        html += '<div class="quick-action-params">';
                        for (var i = 0; i < action.params.length; i++) {
                            var param = action.params[i];
                            html += '<div class="quick-action-param-row">';
                            html += '<label>' + escape_html(param.label) + '：</label>';
                            if (param.type === 'number') {
                                html += '<input type="number" class="form-control quick-param-input" data-param="' + param.name + '"';
                                html += ' placeholder="' + (param.placeholder || '') + '"';
                                if (param.min !== undefined) html += ' min="' + param.min + '"';
                                if (param.max !== undefined) html += ' max="' + param.max + '"';
                                html += '>';
                            } else {
                                html += '<input type="text" class="form-control quick-param-input" data-param="' + param.name + '"';
                                html += ' placeholder="' + (param.placeholder || '') + '">';
                            }
                            html += '</div>';
                        }
                        html += '</div>';
                    }

                    html += '<div class="quick-action-footer">';
                    html += '<button class="btn btn-primary btn-quick-execute" data-action="' + actionKey + '">立即统计</button>';
                    html += '</div>';
                    html += '</div>';
                    html += '</div>';
                }
            }

            container.innerHTML = html;

            // 绑定卡片点击事件
            var cards = container.querySelectorAll('.quick-action-card');
            for (var j = 0; j < cards.length; j++) {
                cards[j].addEventListener('click', function(e) {
                    // 如果点击的是输入框或按钮，不触发折叠
                    if (e.target.tagName === 'INPUT' || e.target.tagName === 'BUTTON') {
                        return;
                    }

                    var body = this.querySelector('.quick-action-body');
                    var toggle = this.querySelector('.quick-action-toggle');
                    var isVisible = !body.classList.contains('hidden');

                    // 先关闭所有其他卡片
                    var allCards = container.querySelectorAll('.quick-action-card');
                    for (var k = 0; k < allCards.length; k++) {
                        var otherBody = allCards[k].querySelector('.quick-action-body');
                        var otherToggle = allCards[k].querySelector('.quick-action-toggle');
                        if (otherBody) otherBody.classList.add('hidden');
                        if (otherToggle) otherToggle.textContent = '▼';
                        allCards[k].classList.remove('quick-action-active');
                    }

                    // 切换当前卡片
                    if (!isVisible) {
                        body.classList.remove('hidden');
                        body.removeAttribute('style');
                        toggle.textContent = '▲';
                        this.classList.add('quick-action-active');
                        currentQuickAction = this.getAttribute('data-action');
                    } else {
                        currentQuickAction = null;
                    }
                });
            }

            // 绑定执行按钮事件
            var executeBtns = container.querySelectorAll('.btn-quick-execute');
            for (var m = 0; m < executeBtns.length; m++) {
                executeBtns[m].addEventListener('click', function(e) {
                    e.stopPropagation();
                    var actionKey = this.getAttribute('data-action');
                    executeQuickAction(actionKey, this.closest('.quick-action-card'));
                });
            }
        }

        // 执行快捷操作
        function executeQuickAction(actionKey, cardEl) {
            var action = QUICK_ACTIONS[actionKey];
            if (!action) return;

            var params = { action: actionKey };

            // 收集参数
            if (action.params.length > 0) {
                for (var i = 0; i < action.params.length; i++) {
                    var paramConfig = action.params[i];
                    var input = cardEl.querySelector('.quick-param-input[data-param="' + paramConfig.name + '"]');
                    if (input) {
                        var value = input.value.trim();
                        if (value === '') {
                            alert('请填写' + paramConfig.label);
                            return;
                        }
                        if (paramConfig.type === 'number') {
                            params[paramConfig.name] = parseInt(value, 10);
                        } else {
                            params[paramConfig.name] = value;
                        }
                    }
                }
            }

            // 发送请求
            show_loading();
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/query/stat-with-params', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    hide_loading();
                    if (xhr.status === 200) {
                        try {
                            var resp = JSON.parse(xhr.responseText);
                            if (resp.ok) {
                                renderQuickActionResult(resp, action.label);
                            } else {
                                alert(resp.message || '查询失败');
                            }
                        } catch (e) {
                            alert('响应解析失败');
                        }
                    } else {
                        alert('请求失败');
                    }
                }
            };
            xhr.send(JSON.stringify(params));
        }

        // 渲染快捷操作结果
        function renderQuickActionResult(resp, actionLabel) {
            var resultWrapper = document.getElementById('quick-action-result');
            var sqlBox = document.getElementById('quick-action-sql');
            var table = document.getElementById('quick-action-table');
            var emptyBox = document.getElementById('quick-action-empty');
            var titleEl = document.getElementById('quick-action-result-title');

            if (titleEl) {
                titleEl.textContent = actionLabel + ' 结果';
            }

            if (sqlBox) {
                sqlBox.innerHTML = highlight_sql(resp.sql || '');
                sqlBox.classList.add('sql-visible');
            }

            var columns = resp.columns || [];
            var data = resp.data || [];

            if (data.length === 0) {
                if (resultWrapper) { resultWrapper.classList.add('hidden'); }
                if (emptyBox) emptyBox.classList.add('empty-visible');
                return;
            }

            if (emptyBox) emptyBox.classList.remove('empty-visible');
            if (resultWrapper) { resultWrapper.classList.remove('hidden'); resultWrapper.removeAttribute('style'); }

            // 渲染表头
            var thead = '<thead><tr>';
            for (var i = 0; i < columns.length; i++) {
                thead += '<th>' + escape_html(columns[i]) + '</th>';
            }
            thead += '</tr></thead>';

            // 渲染表体
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

            if (table) table.innerHTML = thead + tbody;
        }

        // 初始化
        initQuickActionCards();
    })();

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
            result_wrapper.classList.add('hidden');
            btn_export.classList.add('hidden');
            empty_box.classList.add('empty-visible');
            return;
        }

        empty_box.classList.remove('empty-visible');
        result_wrapper.classList.remove('hidden');
        result_wrapper.removeAttribute('style');
        btn_export.classList.remove('hidden');
        btn_export.removeAttribute('style');

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

    /* ---------- 3. SQL实训逻辑 ---------- */
    var accordion_titles = document.querySelectorAll('.accordion-title');
    for (var i = 0; i < accordion_titles.length; i++) {
        accordion_titles[i].addEventListener('click', function() {
            var item = this.parentNode;
            var all_items = document.querySelectorAll('.accordion-item');
            for (var j = 0; j < all_items.length; j++) {
                if (all_items[j] !== item) {
                    all_items[j].classList.remove('accordion-open');
                }
            }
            item.classList.toggle('accordion-open');
        });
    }

    var keyword_headers = document.querySelectorAll('.keyword-header');
    for (var i = 0; i < keyword_headers.length; i++) {
        keyword_headers[i].addEventListener('click', function() {
            var card = this.parentNode;
            card.classList.toggle('keyword-open');

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

        html += '<div class="keyword-desc">' + escape_html(info.description || '') + '</div>';

        if (info.sql) {
            html += '<div class="sql-display-box sql-visible">' + highlight_sql(info.sql) + '</div>';
        }

        if (info.executable) {
            var is_admin = document.querySelector('.role-badge-admin') !== null;
            html += '<button class="btn btn-primary btn-keyword-execute" data-keyword="' + escape_html(info.keyword || '') + '"' + (is_admin ? '' : ' disabled title="仅管理员可执行"') + '>执行</button>';
        }
        if (info.keyword === 'DROP_DATABASE' || info.keyword === 'DROP_TABLE') {
            html += '<span class="keyword-danger-tag">危险</span>';
        }

        detail_el.innerHTML = html;

        var exec_btn = detail_el.querySelector('.btn-keyword-execute');
        if (exec_btn && !exec_btn.disabled) {
            exec_btn.addEventListener('click', function() {
                var kw = this.getAttribute('data-keyword');
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
        overlay.classList.remove('hidden');
        overlay.removeAttribute('style');

        var btn_yes = document.getElementById('btn-confirm-yes');
        var btn_no = document.getElementById('btn-confirm-no');

        var new_yes = btn_yes.cloneNode(true);
        var new_no = btn_no.cloneNode(true);
        btn_yes.parentNode.replaceChild(new_yes, btn_yes);
        btn_no.parentNode.replaceChild(new_no, btn_no);

        new_yes.addEventListener('click', function() {
            overlay.classList.add('hidden');
            execute_keyword(keyword);
        });

        new_no.addEventListener('click', function() {
            overlay.classList.add('hidden');
        });
    }

    /* ---------- 4. SQL关键字高亮渲染函数 ---------- */
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

        var escaped = escape_html(sql);

        keywords.sort(function(a, b) { return b.length - a.length; });

        for (var i = 0; i < keywords.length; i++) {
            var kw = keywords[i];
            var regex = new RegExp('\\b' + kw.replace(/ /g, '\\s+') + '\\b', 'gi');
            escaped = escaped.replace(regex, '<span class="sql-keyword-highlight">$&</span>');
        }

        return escaped;
    }
})();

/* ========== 场景化查询 ========== */
var scene_select = document.getElementById('scene-select');
var scene_params = document.getElementById('scene-params');
var btn_scene_query = document.getElementById('btn-scene-query');
var btn_scene_reset = document.getElementById('btn-scene-reset');
var btn_scene_export = document.getElementById('btn-scene-export');

// 场景参数模板
var SCENE_PARAM_TEMPLATES = {
    'by_student_no': '<div class="scene-param-row"><label>请输入学号：</label><input type="text" id="param-val1" placeholder="例如：2024001"></div>',
    'by_student_name': '<div class="scene-param-row"><label>请输入姓名：</label><input type="text" id="param-val1" placeholder="例如：张三"></div>',
    'by_major': '<div class="scene-param-row"><label>请输入专业名称：</label><input type="text" id="param-val1" placeholder="例如：计算机"></div>',
    'by_dept': '<div class="scene-param-row"><label>请输入学院名称：</label><input type="text" id="param-val1" placeholder="例如：信息工程学院"></div>',
    'by_grade': '<div class="scene-param-row"><label>请输入年级：</label><input type="text" id="param-val1" placeholder="例如：2022"></div>',
    'by_age_range': '<div class="scene-param-row"><label>最小年龄：</label><input type="number" id="param-val1" placeholder="例如：18" min="1" max="150"><span class="param-separator">至</span><label>最大年龄：</label><input type="number" id="param-val2" placeholder="例如：22" min="1" max="150"></div>',
    'by_gender': '<div class="scene-param-row"><label>请选择性别：</label><select id="param-val1"><option value="男">男</option><option value="女">女</option></select></div>',
    'by_class': '<div class="scene-param-row"><label>请输入班级名称：</label><input type="text" id="param-val1" placeholder="例如：计科1班"></div>',
    'by_name_like': '<div class="scene-param-row"><label>请输入姓名关键字：</label><input type="text" id="param-val1" placeholder="例如：张"></div>',
    'by_major_or': '<div class="scene-param-row"><label>专业一：</label><input type="text" id="param-val1" placeholder="例如：计算机"><span class="param-separator">或</span><label>专业二：</label><input type="text" id="param-val2" placeholder="例如：软件工程"></div>',
    'by_not_major': '<div class="scene-param-row"><label>要排除的专业：</label><input type="text" id="param-val1" placeholder="例如：计算机"></div>',
    'by_major_and_grade': '<div class="scene-param-row"><label>专业：</label><input type="text" id="param-val1" placeholder="例如：计算机"><span class="param-separator"></span><label>年级：</label><input type="text" id="param-val2" placeholder="例如：2022"></div>',
    'by_age_gt': '<div class="scene-param-row"><label>年龄大于：</label><input type="number" id="param-val1" placeholder="例如：20" min="1" max="150"></div>',
    'by_age_lt': '<div class="scene-param-row"><label>年龄小于：</label><input type="number" id="param-val1" placeholder="例如：20" min="1" max="150"></div>'
};

if (scene_select) {
    scene_select.addEventListener('change', function() {
        var scene = scene_select.value;
        scene_params.innerHTML = '';
        if (scene && SCENE_PARAM_TEMPLATES[scene]) {
            scene_params.innerHTML = SCENE_PARAM_TEMPLATES[scene];
            scene_params.classList.remove('hidden');
        } else {
            scene_params.classList.add('hidden');
        }
    });

    btn_scene_query.addEventListener('click', function() {
        var scene = scene_select.value;
        if (!scene) {
            alert('请先选择查询场景');
            return;
        }

        var params = {};
        var val1 = document.getElementById('param-val1');
        var val2 = document.getElementById('param-val2');
        if (val1) params.val1 = val1.value.trim();
        if (val2) params.val2 = val2.value.trim();

        // 基本非空校验
        if (scene !== 'by_age_range' && scene !== 'by_major_or' && scene !== 'by_major_and_grade') {
            if (!params.val1) {
                alert('请填写查询参数');
                return;
            }
        } else if (scene === 'by_age_range') {
            if (!params.val1 || !params.val2) {
                alert('请填写完整的年龄范围');
                return;
            }
        } else if (scene === 'by_major_or' || scene === 'by_major_and_grade') {
            if (!params.val1 || !params.val2) {
                alert('请填写完整的查询参数');
                return;
            }
        }

        show_loading();
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/query/scene', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                hide_loading();
                if (xhr.status === 200) {
                    try {
                        var res = JSON.parse(xhr.responseText);
                        var resultDiv = document.getElementById('condition-result');
                        var sqlDiv = document.getElementById('condition-sql');
                        
                        if (res.desc) {
                            sqlDiv.innerHTML = '<div class="scene-desc">' + escape_html(res.desc) + '</div>';
                        }
                        if (res.sql) {
                            sqlDiv.innerHTML += '<div class="sql-label">生成的SQL：</div><div class="sql-text">' + highlight_sql(escape_html(res.sql)) + '</div>';
                        }
                        
                        if (res.data && res.data.length > 0) {
                            var thead = document.getElementById('condition-thead');
                            var tbody = document.getElementById('condition-tbody');
                            thead.innerHTML = '';
                            tbody.innerHTML = '';
                            
                            var tr = document.createElement('tr');
                            res.columns.forEach(function(col) {
                                var th = document.createElement('th');
                                th.textContent = col;
                                tr.appendChild(th);
                            });
                            thead.appendChild(tr);
                            
                            res.data.forEach(function(row) {
                                var tr2 = document.createElement('tr');
                                res.columns.forEach(function(col) {
                                    var td = document.createElement('td');
                                    td.textContent = row[col] !== null ? row[col] : '';
                                    tr2.appendChild(td);
                                });
                                tbody.appendChild(tr2);
                            });
                            
                            resultDiv.classList.remove('hidden');
                            var emptyEl = document.getElementById('condition-empty');
                            if (emptyEl) emptyEl.classList.add('hidden');
                        } else {
                            resultDiv.classList.remove('hidden');
                            var tableEl = document.getElementById('condition-table');
                            if (tableEl) tableEl.classList.add('hidden');
                            var emptyEl = document.getElementById('condition-empty');
                            if (emptyEl) emptyEl.classList.remove('hidden');
                        }
                    } catch (err) {
                        alert('查询结果解析失败');
                    }
                } else {
                    alert('查询请求失败');
                }
            }
        };
        xhr.send(JSON.stringify({scene: scene, params: params}));
    });

    btn_scene_reset.addEventListener('click', function() {
        scene_select.value = '';
        scene_params.innerHTML = '';
        scene_params.classList.add('hidden');
        document.getElementById('condition-result').classList.add('hidden');
        document.getElementById('condition-sql').innerHTML = '';
    });

    btn_scene_export.addEventListener('click', function() {
        var scene = scene_select.value;
        if (!scene) {
            alert('请先执行查询再导出');
            return;
        }
        var params = {};
        var val1 = document.getElementById('param-val1');
        var val2 = document.getElementById('param-val2');
        if (val1) params.val1 = val1.value.trim();
        if (val2) params.val2 = val2.value.trim();
        
        show_loading();
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/query/scene', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.responseType = 'blob';
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                hide_loading();
                if (xhr.status === 200) {
                    var blob = new Blob([xhr.response], {type: 'text/csv'});
                    var link = document.createElement('a');
                    link.href = URL.createObjectURL(blob);
                    link.download = 'scene_query_result.csv';
                    link.click();
                } else {
                    alert('导出失败');
                }
            }
        };
        xhr.send(JSON.stringify({scene: scene, params: params, export: true}));
    });
}

/* ========== 排序浏览 - 多字段排序 ========== */
(function() {
    // 排序字段选项配置
    var SORT_FIELD_OPTIONS = [
        { value: 'student_no', label: '学号' },
        { value: 'student_name', label: '姓名' },
        { value: 'gender', label: '性别' },
        { value: 'age', label: '年龄' },
        { value: 'class_name', label: '班级' },
        { value: 'grade', label: '年级' },
        { value: 'major_name', label: '专业' },
        { value: 'dept_name', label: '学院' }
    ];

    var MAX_SORT_FIELDS = 5;
    var sortFields = []; // 存储排序字段配置
    var sortCurrentPage = 1;
    var sortTotalPages = 1;

    // 初始化多字段排序模块
    function initMultiSort() {
        var container = document.getElementById('multi-sort-container');
        var btnAdd = document.getElementById('btn-add-sort-field');
        var btnApply = document.getElementById('btn-sort-apply');
        var btnReset = document.getElementById('btn-sort-reset');

        if (!container) return;

        // 绑定添加排序字段按钮
        if (btnAdd) {
            btnAdd.addEventListener('click', function() {
                addSortField();
            });
        }

        // 绑定应用排序按钮
        if (btnApply) {
            btnApply.addEventListener('click', function() {
                sortCurrentPage = 1;
                executeMultiSort(1);
            });
        }

        // 绑定重置按钮
        if (btnReset) {
            btnReset.addEventListener('click', function() {
                resetSortFields();
            });
        }

        // 默认添加一个排序字段
        addSortField();

        // 绑定分页按钮
        var btnPrev = document.getElementById('sort-page-prev');
        var btnNext = document.getElementById('sort-page-next');

        if (btnPrev) {
            btnPrev.addEventListener('click', function() {
                if (sortCurrentPage > 1) {
                    executeMultiSort(sortCurrentPage - 1);
                }
            });
        }

        if (btnNext) {
            btnNext.addEventListener('click', function() {
                if (sortCurrentPage < sortTotalPages) {
                    executeMultiSort(sortCurrentPage + 1);
                }
            });
        }
    }

    // 添加排序字段
    function addSortField() {
        if (sortFields.length >= MAX_SORT_FIELDS) {
            alert('最多只能添加' + MAX_SORT_FIELDS + '个排序字段');
            return;
        }

        var container = document.getElementById('multi-sort-fields');
        if (!container) return;

        var fieldId = 'sort-field-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        var priority = sortFields.length + 1;

        var fieldConfig = {
            id: fieldId,
            field: SORT_FIELD_OPTIONS[0].value,
            order: 'asc'
        };
        sortFields.push(fieldConfig);

        var html = '<div class="sort-field-row" id="' + fieldId + '">';
        html += '<span class="sort-priority">第' + priority + '排序</span>';
        html += '<select class="form-control sort-field-select" data-id="' + fieldId + '">';
        for (var i = 0; i < SORT_FIELD_OPTIONS.length; i++) {
            var opt = SORT_FIELD_OPTIONS[i];
            html += '<option value="' + opt.value + '">' + escape_html(opt.label) + '</option>';
        }
        html += '</select>';
        html += '<div class="sort-order-group">';
        html += '<label class="sort-order-label"><input type="radio" name="order-' + fieldId + '" value="asc" checked> 升序</label>';
        html += '<label class="sort-order-label"><input type="radio" name="order-' + fieldId + '" value="desc"> 降序</label>';
        html += '</div>';
        html += '<button class="btn btn-danger btn-remove-sort" data-id="' + fieldId + '">删除</button>';
        html += '</div>';

        container.insertAdjacentHTML('beforeend', html);

        // 绑定字段选择变化事件
        var select = container.querySelector('#' + fieldId + ' .sort-field-select');
        if (select) {
            select.addEventListener('change', function() {
                updateSortFieldConfig(fieldId, 'field', this.value);
            });
        }

        // 绑定排序方向变化事件
        var radios = container.querySelectorAll('input[name="order-' + fieldId + '"]');
        for (var r = 0; r < radios.length; r++) {
            radios[r].addEventListener('change', function() {
                if (this.checked) {
                    updateSortFieldConfig(fieldId, 'order', this.value);
                }
            });
        }

        // 绑定删除按钮事件
        var removeBtn = container.querySelector('#' + fieldId + ' .btn-remove-sort');
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                removeSortField(fieldId);
            });
        }

        // 更新添加按钮状态
        updateAddButtonState();
    }

    // 更新排序字段配置
    function updateSortFieldConfig(fieldId, key, value) {
        for (var i = 0; i < sortFields.length; i++) {
            if (sortFields[i].id === fieldId) {
                sortFields[i][key] = value;
                break;
            }
        }
    }

    // 删除排序字段
    function removeSortField(fieldId) {
        var row = document.getElementById(fieldId);
        if (row) row.remove();

        // 从数组中移除
        for (var i = 0; i < sortFields.length; i++) {
            if (sortFields[i].id === fieldId) {
                sortFields.splice(i, 1);
                break;
            }
        }

        // 更新优先级显示
        updatePriorityLabels();
        // 更新添加按钮状态
        updateAddButtonState();
    }

    // 更新优先级标签
    function updatePriorityLabels() {
        var container = document.getElementById('multi-sort-fields');
        if (!container) return;

        var rows = container.querySelectorAll('.sort-field-row');
        for (var i = 0; i < rows.length; i++) {
            var priorityLabel = rows[i].querySelector('.sort-priority');
            if (priorityLabel) {
                priorityLabel.textContent = '第' + (i + 1) + '排序';
            }
        }
    }

    // 更新添加按钮状态
    function updateAddButtonState() {
        var btnAdd = document.getElementById('btn-add-sort-field');
        if (btnAdd) {
            btnAdd.disabled = sortFields.length >= MAX_SORT_FIELDS;
            if (sortFields.length >= MAX_SORT_FIELDS) {
                btnAdd.title = '最多只能添加' + MAX_SORT_FIELDS + '个排序字段';
            } else {
                btnAdd.title = '';
            }
        }
    }

    // 重置排序字段
    function resetSortFields() {
        var container = document.getElementById('multi-sort-fields');
        if (container) container.innerHTML = '';
        sortFields = [];
        addSortField();

        // 清空结果区域
        var resultWrapper = document.getElementById('sort-result');
        var sqlBox = document.getElementById('sort-sql');
        var emptyBox = document.getElementById('sort-empty');

        if (resultWrapper) { resultWrapper.classList.add('hidden'); }
        if (sqlBox) {
            sqlBox.innerHTML = '';
            sqlBox.classList.remove('sql-visible');
        }
        if (emptyBox) emptyBox.classList.remove('empty-visible');

        sortCurrentPage = 1;
        sortTotalPages = 1;
        updatePaginationInfo();
    }

    // 执行多字段排序查询
    function executeMultiSort(page) {
        if (sortFields.length === 0) {
            alert('请至少添加一个排序字段');
            return;
        }

        // 构建排序参数
        var sortParams = [];
        for (var i = 0; i < sortFields.length; i++) {
            sortParams.push({
                field: sortFields[i].field,
                order: sortFields[i].order
            });
        }

        show_loading();
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/query/sort', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                hide_loading();
                if (xhr.status === 200) {
                    try {
                        var resp = JSON.parse(xhr.responseText);
                        if (resp.ok !== false) {
                            renderMultiSortResult(resp);
                            sortCurrentPage = resp.page || 1;
                            sortTotalPages = resp.total_pages || 1;
                            updatePaginationInfo();
                        } else {
                            alert(resp.message || '查询失败');
                        }
                    } catch (e) {
                        alert('响应解析失败');
                    }
                } else {
                    alert('请求失败');
                }
            }
        };
        xhr.send(JSON.stringify({
            sort_fields: sortParams,
            page: page
        }));
    }

    // 渲染多字段排序结果
    function renderMultiSortResult(resp) {
        var sqlBox = document.getElementById('sort-sql');
        var resultWrapper = document.getElementById('sort-result');
        var emptyBox = document.getElementById('sort-empty');
        var table = document.getElementById('sort-table');

        if (sqlBox) {
            sqlBox.innerHTML = highlight_sql(resp.sql || '');
            sqlBox.classList.add('sql-visible');
        }

        var columns = resp.columns || ['student_no', 'student_name', 'gender', 'age', 'class_name', 'grade', 'major_name', 'dept_name'];
        var data = resp.data || [];

        if (data.length === 0) {
            if (resultWrapper) { resultWrapper.classList.add('hidden'); }
            if (emptyBox) emptyBox.classList.add('empty-visible');
            return;
        }

        if (emptyBox) emptyBox.classList.remove('empty-visible');
        if (resultWrapper) { resultWrapper.classList.remove('hidden'); resultWrapper.removeAttribute('style'); }

        // 渲染表头
        var thead = '<thead><tr>';
        for (var i = 0; i < columns.length; i++) {
            thead += '<th>' + escape_html(columns[i]) + '</th>';
        }
        thead += '</tr></thead>';

        // 渲染表体
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

        if (table) table.innerHTML = thead + tbody;
    }

    // 更新分页信息
    function updatePaginationInfo() {
        var pageInfo = document.getElementById('sort-page-info');
        var btnPrev = document.getElementById('sort-page-prev');
        var btnNext = document.getElementById('sort-page-next');

        if (pageInfo) {
            pageInfo.textContent = '第 ' + sortCurrentPage + ' 页 / 共 ' + sortTotalPages + ' 页';
        }

        if (btnPrev) {
            btnPrev.disabled = sortCurrentPage <= 1;
        }

        if (btnNext) {
            btnNext.disabled = sortCurrentPage >= sortTotalPages;
        }
    }

    // 选择排序面板时自动加载
    var sortTab = document.querySelector('[data-tab="sort"]');
    if (sortTab) {
        sortTab.addEventListener('click', function() {
            setTimeout(function() {
                initMultiSort();
            }, 100);
        });
    }

    // 如果当前就在排序面板，立即初始化
    if (document.getElementById('panel-sort') && document.getElementById('panel-sort').classList.contains('panel-active')) {
        initMultiSort();
    }
})();

/* ========== 自定义SQL输入 ========== */
(function() {
    var btn_toggle = document.getElementById('btn-sql-toggle');
    var sql_content = document.getElementById('custom-sql-content');
    var sql_editor = document.getElementById('sql-editor');
    var btn_format = document.getElementById('btn-sql-format');
    var btn_execute = document.getElementById('btn-sql-execute');
    var btn_export = document.getElementById('btn-sql-export');
    var sql_error = document.getElementById('sql-error-msg');
    
    if (!btn_toggle) return;

    // 切换显示隐藏
    btn_toggle.addEventListener('click', function() {
        var is_hidden = sql_content.classList.contains('hidden');
        if (is_hidden) {
            sql_content.classList.remove('hidden');
        } else {
            sql_content.classList.add('hidden');
        }
        btn_toggle.textContent = is_hidden ? '收起自定义SQL查询 ▴' : '切换到自定义SQL查询 ▾';
    });

    // 常用语句模板
    var sql_hint_btns = document.querySelectorAll('.sql-hint-btn');
    sql_hint_btns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            if (sql_editor) {
                sql_editor.value = this.getAttribute('data-sql');
            }
        });
    });

    // 格式化
    if (btn_format) {
        btn_format.addEventListener('click', function() {
            if (!sql_editor) return;
            try {
                var sql = sql_editor.value.trim();
                // 简单格式化：将关键词转大写
                var keywords = ['select', 'from', 'where', 'and', 'or', 'not', 'in', 'like', 'between', 
                    'is null', 'is not null', 'order by', 'group by', 'having', 'limit', 'asc', 'desc',
                    'insert into', 'values', 'update', 'set', 'delete from', 'create table', 'alter table',
                    'drop table', 'count', 'sum', 'avg', 'max', 'min', 'distinct', 'as', 'on', 'inner join',
                    'left join', 'right join'];
                var formatted = sql;
                keywords.forEach(function(kw) {
                    var regex = new RegExp('\\b' + kw + '\\b', 'gi');
                    formatted = formatted.replace(regex, kw.toUpperCase());
                });
                sql_editor.value = formatted;
                hide_sql_error();
            } catch(e) {
                show_sql_error('格式化出错');
            }
        });
    }

    // 执行
    if (btn_execute) {
        btn_execute.addEventListener('click', function() {
            execute_custom_sql(false);
        });
    }

    // 导出
    if (btn_export) {
        btn_export.addEventListener('click', function() {
            execute_custom_sql(true);
        });
    }

    function show_sql_error(msg) {
        if (sql_error) {
            sql_error.textContent = msg;
            sql_error.classList.remove('hidden');
            sql_error.removeAttribute('style');
        }
    }

    function hide_sql_error() {
        if (sql_error) {
            sql_error.classList.add('hidden');
        }
    }

    function execute_custom_sql(is_export) {
        if (!sql_editor) return;
        var sql = sql_editor.value.trim();
        if (!sql) {
            show_sql_error('请输入SQL语句');
            return;
        }
        
        hide_sql_error();
        show_loading();
        
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/query/custom-sql', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        
        if (is_export) {
            xhr.responseType = 'blob';
        }
        
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                hide_loading();
                if (is_export && xhr.status === 200) {
                    var blob = new Blob([xhr.response], {type: 'text/csv'});
                    var link = document.createElement('a');
                    link.href = URL.createObjectURL(blob);
                    link.download = 'custom_query_result.csv';
                    link.click();
                    return;
                }
                
                if (xhr.status === 200) {
                    try {
                        var res = JSON.parse(xhr.responseText);
                        if (res.success) {
                            render_custom_sql_result(res);
                        } else {
                            show_sql_error(res.message || '执行失败');
                        }
                    } catch(err) {
                        show_sql_error('响应解析失败');
                    }
                } else {
                    show_sql_error('请求失败，状态码：' + xhr.status);
                }
            }
        };
        
        xhr.send(JSON.stringify({sql: sql, export: is_export}));
    }

    function render_custom_sql_result(res) {
        var resultDiv = document.getElementById('condition-result');
        var sqlDisplay = document.getElementById('condition-sql');
        
        if (sqlDisplay) {
            sqlDisplay.innerHTML = '<div class="sql-label">执行SQL：</div><div class="sql-text">' + highlight_sql(escape_html(res.sql)) + '</div>';
            sqlDisplay.classList.remove('hidden');
            sqlDisplay.removeAttribute('style');
        }
        
        if (res.data && res.data.length > 0) {
            var thead = document.getElementById('condition-thead');
            var tbody = document.getElementById('condition-tbody');
            if (thead) thead.innerHTML = '';
            if (tbody) tbody.innerHTML = '';
            
            var tr = document.createElement('tr');
            res.columns.forEach(function(col) {
                var th = document.createElement('th');
                th.textContent = col;
                tr.appendChild(th);
            });
            if (thead) thead.appendChild(tr);
            
            res.data.forEach(function(row) {
                var tr2 = document.createElement('tr');
                res.columns.forEach(function(col) {
                    var td = document.createElement('td');
                    td.textContent = row[col] !== null ? row[col] : '';
                    tr2.appendChild(td);
                });
                if (tbody) tbody.appendChild(tr2);
            });
            
            if (resultDiv) {
                resultDiv.classList.remove('hidden');
            }
            var emptyEl = document.getElementById('condition-empty');
            if (emptyEl) emptyEl.classList.add('hidden');
        } else {
            if (resultDiv) {
                resultDiv.classList.remove('hidden');
            }
            var tableEl = document.getElementById('condition-table');
            if (tableEl) tableEl.classList.add('hidden');
            var emptyEl = document.getElementById('condition-empty');
            if (emptyEl) emptyEl.classList.remove('hidden');
        }
    }
})();

/* ========== 快查指令 - SQL执行器 ========== */
(function() {
    var editor = document.getElementById('quick-sql-editor');
    var btn_run = document.getElementById('btn-quick-sql-run');
    var btn_clear = document.getElementById('btn-quick-sql-clear');
    var btn_export = document.getElementById('btn-quick-sql-export');
    var error_div = document.getElementById('quick-sql-error');
    var display_div = document.getElementById('quick-sql-display');
    var result_div = document.getElementById('quick-sql-result');
    var table_head = document.getElementById('quick-sql-thead');
    var table_body = document.getElementById('quick-sql-tbody');
    var empty_div = document.getElementById('quick-sql-empty');

    if (!editor) return;

    function show_err(msg) {
        if (error_div) {
            error_div.textContent = msg;
            error_div.classList.remove('hidden');
            error_div.removeAttribute('style');
        }
    }

    function hide_err() {
        if (error_div) error_div.classList.add('hidden');
    }

    function run_sql(is_export) {
        var sql = editor.value.trim();
        if (!sql) {
            show_err('请输入SQL语句');
            return;
        }
        hide_err();
        show_loading();

        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/query/custom-sql', true);
        xhr.setRequestHeader('Content-Type', 'application/json');

        if (is_export) {
            xhr.responseType = 'blob';
        }

        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                hide_loading();
                if (is_export && xhr.status === 200) {
                    var blob = new Blob([xhr.response], {type: 'text/csv'});
                    var link = document.createElement('a');
                    link.href = URL.createObjectURL(blob);
                    link.download = 'quick_sql_result.csv';
                    link.click();
                    return;
                }
                if (xhr.status === 200) {
                    try {
                        var res = JSON.parse(xhr.responseText);
                        if (res.success) {
                            if (display_div) {
                                display_div.innerHTML = '<div class="sql-label">执行SQL：</div><div class="sql-text">' + highlight_sql(escape_html(res.sql)) + '</div>';
                                display_div.classList.remove('hidden');
                                display_div.removeAttribute('style');
                            }
                            if (res.data && res.data.length > 0 && table_head && table_body) {
                                table_head.innerHTML = '';
                                table_body.innerHTML = '';
                                var tr = document.createElement('tr');
                                res.columns.forEach(function(col) {
                                    var th = document.createElement('th');
                                    th.textContent = col;
                                    tr.appendChild(th);
                                });
                                table_head.appendChild(tr);
                                res.data.forEach(function(row) {
                                    var tr2 = document.createElement('tr');
                                    res.columns.forEach(function(col) {
                                        var td = document.createElement('td');
                                        td.textContent = row[col] !== null ? row[col] : '';
                                        tr2.appendChild(td);
                                    });
                                    table_body.appendChild(tr2);
                                });
                                if (result_div) { result_div.classList.remove('hidden'); result_div.removeAttribute('style'); }
                                if (empty_div) empty_div.classList.add('hidden');
                            } else {
                                if (result_div) { result_div.classList.remove('hidden'); result_div.removeAttribute('style'); }
                                if (empty_div) empty_div.classList.remove('hidden');
                            }
                        } else {
                            show_err(res.message || '执行失败');
                        }
                    } catch(err) {
                        show_err('响应解析失败');
                    }
                } else {
                    show_err('请求失败，状态码：' + xhr.status);
                }
            }
        };
        xhr.send(JSON.stringify({sql: sql, export: is_export}));
    }

    if (btn_run) btn_run.addEventListener('click', function() { run_sql(false); });
    if (btn_export) btn_export.addEventListener('click', function() { run_sql(true); });
    if (btn_clear) btn_clear.addEventListener('click', function() { editor.value = ''; hide_err(); if(display_div) display_div.classList.add('hidden'); if(result_div) result_div.classList.add('hidden'); });

    // 复制按钮
    document.querySelectorAll('.btn-sql-copy').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var pre = this.parentElement.querySelector('pre.ref-sql');
            if (pre) {
                var text = pre.textContent.trim();
                // 复制到编辑器
                if (editor) {
                    editor.value = text;
                }
                this.textContent = '已复制!';
                var self = this;
                setTimeout(function() { self.textContent = '复制'; }, 1500);
            }
        });
    });

    // ref-card 点击展开
    document.querySelectorAll('.ref-card-header').forEach(function(header) {
        header.addEventListener('click', function() {
            var card = this.parentElement;
            card.classList.toggle('open');
        });
    });

    // keyword 网格项点击
    document.querySelectorAll('.kw-item').forEach(function(item) {
        item.addEventListener('click', function() {
            var kw = this.getAttribute('data-keyword');
            if (kw && editor) {
                editor.value = editor.value + ' ' + kw + ' ';
                editor.focus();
            }
        });
    });
})();

/* ========== Tab 参数处理 ========== */
(function() {
    var params = new URLSearchParams(window.location.search);
    var tab = params.get('tab');
    if (tab) {
        var tab_btn = document.querySelector('.tab-item[data-tab="' + tab + '"]');
        if (tab_btn) {
            tab_btn.click();
        }
    }
})();

/* ========== 侧边栏状态恢复 ========== */
(function() {
    var sidebar = document.getElementById('sidebar');
    var mainWrapper = document.getElementById('main-wrapper');
    if (sidebar && mainWrapper) {
        var isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (isCollapsed) {
            sidebar.classList.add('collapsed');
            mainWrapper.classList.add('expanded');
        }
    }
})();
