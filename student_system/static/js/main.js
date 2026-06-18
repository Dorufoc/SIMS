/* ========== CSRF Token 管理 ========== */
var _csrf_token = '';

function fetch_csrf_token() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/csrf-token', true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            try {
                var resp = JSON.parse(xhr.responseText);
                if (resp.code === 0 && resp.token) {
                    _csrf_token = resp.token;
                }
            } catch(e) {}
        }
    };
    xhr.send();
}

// 页面加载时获取 token
fetch_csrf_token();

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

/* ========== 移动端侧边栏切换 ========== */

var MOBILE_BREAKPOINT = 768;

function toggleMobileSidebar() {
    var sidebar = document.getElementById('sidebar');
    var overlay = document.getElementById('sidebar-overlay');
    if (!sidebar) return;
    sidebar.classList.toggle('mobile-show');
    if (overlay) overlay.classList.toggle('active');
}

// 初始化移动端侧边栏：创建遮罩层、监听窗口尺寸变化、点击遮罩关闭
(function() {
    var sidebar = document.getElementById('sidebar');
    if (!sidebar) return;

    var overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    overlay.id = 'sidebar-overlay';
    overlay.addEventListener('click', function() {
        sidebar.classList.remove('mobile-show');
        overlay.classList.remove('active');
    });
    document.body.appendChild(overlay);

    window.addEventListener('resize', function() {
        if (window.innerWidth > MOBILE_BREAKPOINT) {
            sidebar.classList.remove('mobile-show');
            overlay.classList.remove('active');
        }
    });
})();

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
  xhr.setRequestHeader("X-CSRF-Token", _csrf_token);

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

/* ========== 侧边栏滚动位置保存与恢复 ========== */
(function() {
    var sidebar = document.getElementById('sidebar');
    if (!sidebar) return;

    // 页面加载时恢复侧边栏滚动位置
    var savedScrollTop = sessionStorage.getItem('sidebarScrollTop');
    if (savedScrollTop !== null) {
        sidebar.scrollTop = parseInt(savedScrollTop, 10);
    }

    // 点击侧边栏链接时保存滚动位置
    sidebar.addEventListener('click', function(e) {
        var link = e.target.closest('a');
        if (link && link.getAttribute('href')) {
            sessionStorage.setItem('sidebarScrollTop', sidebar.scrollTop);
        }
    });
})();

/* ========== 统一筛选模块（增强版） ========== */

/**
 * 根据字段类型获取可用的运算符列表
 * @param {string} type - 字段类型: text, number, select
 * @returns {Array<{value:string, label:string}>} 运算符列表
 */
function getOperatorsForType(type) {
    if (type === 'number') {
        return [
            {value: 'eq', label: '等于'},
            {value: 'neq', label: '不等于'},
            {value: 'gt', label: '大于'},
            {value: 'gte', label: '大于等于'},
            {value: 'lt', label: '小于'},
            {value: 'lte', label: '小于等于'},
            {value: 'between', label: '在...之间'}
        ];
    } else if (type === 'select') {
        return [
            {value: 'eq', label: '等于'},
            {value: 'neq', label: '不等于'},
            {value: 'contains', label: '包含'},
            {value: 'startswith', label: '以...开头'},
            {value: 'endswith', label: '以...结尾'}
        ];
    } else {
        // text 类型
        return [
            {value: 'contains', label: '包含'},
            {value: 'eq', label: '等于'},
            {value: 'neq', label: '不等于'},
            {value: 'startswith', label: '以...开头'},
            {value: 'endswith', label: '以...结尾'}
        ];
    }
}

/**
 * 收集筛选模块中的所有筛选条件
 * @param {string} containerId - 筛选模块容器的ID
 * @returns {Array<{field:string, op:string, value:string}>} 筛选条件数组
 */
function collectFilterValues(containerId) {
    var container = document.getElementById(containerId);
    if (!container) return [];

    var rows = container.querySelectorAll('.filter-row');
    var filters = [];
    for (var i = 0; i < rows.length; i++) {
        var fieldSelect = rows[i].querySelector('.filter-field-select');
        var operatorSelect = rows[i].querySelector('.filter-operator-select');
        var valueInputs = rows[i].querySelectorAll('.filter-value-input');

        if (!fieldSelect || !operatorSelect) continue;
        var field = fieldSelect.value;
        var op = operatorSelect.value;
        if (!field) continue;

        if (op === 'between') {
            // between: 取两个输入框的值，用逗号拼接
            var val1 = valueInputs.length > 0 ? valueInputs[0].value.trim() : '';
            var val2 = valueInputs.length > 1 ? valueInputs[1].value.trim() : '';
            if (val1 && val2) {
                filters.push({field: field, op: op, value: val1 + ',' + val2});
            }
        } else {
            var val = valueInputs.length > 0 ? valueInputs[0].value.trim() : '';
            if (val) {
                filters.push({field: field, op: op, value: val});
            }
        }
    }
    return filters;
}

/**
 * 将筛选条件数组编码为 URL 查询字符串
 * @param {Array<{field:string, op:string, value:string}>} filters
 * @returns {string} 如: filters=%5B%7B%22field%22%3A%22...%22%7D%5D
 */
function encodeFilters(filters) {
    if (!filters || filters.length === 0) return '';
    return 'filters=' + encodeURIComponent(JSON.stringify(filters));
}

/**
 * 初始化统一筛选模块
 * @param {object} config - 配置对象
 * @param {string} config.containerId - 筛选模块容器的ID
 * @param {Array<{name:string, label:string, type:string, options?:string[]}>} config.fields - 筛选字段配置
 * @param {function} config.onApply - 点击查询时的回调，接收 filters 数组
 * @param {function} config.onReset - 点击重置时的回调
 */
function initFilterModule(config) {
    var container = document.getElementById(config.containerId);
    if (!container) return;

    var rowsContainer = container.querySelector('.filter-rows-container');
    var addBtn = container.querySelector('.btn-add-filter');
    var applyBtn = container.querySelector('.btn-apply-filters');
    var resetBtn = container.querySelector('.btn-reset-filters');

    // 将字段配置存储到容器上，支持动态更新选项
    container._fieldConfigs = {};
    for (var i = 0; i < config.fields.length; i++) {
        container._fieldConfigs[config.fields[i].name] = config.fields[i];
    }

    // 构建字段选项 HTML（不包含可选的占位项，自动默认选中第一个字段）
    function buildFieldOptions(selectedName) {
        var html = '';
        for (var i = 0; i < config.fields.length; i++) {
            var f = config.fields[i];
            var sel = (f.name === selectedName) ? ' selected' : '';
            html += '<option value="' + f.name + '"' + sel + '>' + f.label + '</option>';
        }
        return html;
    }

    // 构建运算符选项 HTML
    function buildOperatorOptions(type, selectedOp) {
        var ops = getOperatorsForType(type);
        var html = '';
        for (var i = 0; i < ops.length; i++) {
            var sel = (ops[i].value === selectedOp) ? ' selected' : '';
            html += '<option value="' + ops[i].value + '"' + sel + '>' + ops[i].label + '</option>';
        }
        return html;
    }

    // 获取字段配置
    function getFieldConfig(name) {
        for (var i = 0; i < config.fields.length; i++) {
            if (config.fields[i].name === name) return config.fields[i];
        }
        return null;
    }

    // 根据字段类型和运算符构建值输入控件
    function buildValueControl(fieldConfig, operator, currentValues) {
        if (!fieldConfig) return '';
        var type = fieldConfig.type;

        if (operator === 'between') {
            // 范围：显示两个输入框
            var v1 = currentValues && currentValues.length > 0 ? currentValues[0] : '';
            var v2 = currentValues && currentValues.length > 1 ? currentValues[1] : '';
            return '<div class="filter-between-group">' +
                '<input type="' + (type === 'number' ? 'number' : 'text') + '" class="filter-value-input filter-value-from" placeholder="起始值" value="' + v1 + '">' +
                '<span class="filter-between-sep">至</span>' +
                '<input type="' + (type === 'number' ? 'number' : 'text') + '" class="filter-value-input filter-value-to" placeholder="结束值" value="' + v2 + '">' +
                '</div>';
        }

        if (type === 'select' && fieldConfig.options) {
            // 精确匹配（eq/neq）使用下拉选择，模糊匹配使用文本输入框
            if (operator === 'eq' || operator === 'neq') {
                var selectHtml = '<select class="filter-value-input" style="flex:1;min-width:120px;padding:8px 12px;border:1px solid #cbd5e0;border-radius:4px;font-size:14px;">';
                selectHtml += '<option value="">请选择</option>';
                var curVal = currentValues && currentValues.length > 0 ? currentValues[0] : '';
                for (var i = 0; i < fieldConfig.options.length; i++) {
                    var opt = fieldConfig.options[i];
                    var optValue = (typeof opt === 'object' && opt.value !== undefined) ? opt.value : opt;
                    var optLabel = (typeof opt === 'object' && opt.label !== undefined) ? opt.label : opt;
                    var sel = (optValue === curVal) ? ' selected' : '';
                    selectHtml += '<option value="' + optValue + '"' + sel + '>' + optLabel + '</option>';
                }
                selectHtml += '</select>';
                return selectHtml;
            }
        }

        // text / number 默认输入框
        var curVal = currentValues && currentValues.length > 0 ? currentValues[0] : '';
        return '<input type="' + (type === 'number' ? 'number' : 'text') + '" class="filter-value-input" placeholder="请输入筛选值" value="' + curVal.replace(/"/g, '&quot;') + '" style="flex:1;min-width:150px;padding:8px 12px;border:1px solid #cbd5e0;border-radius:4px;font-size:14px;">';
    }

    // 更新单行的运算符和值输入
    function updateRowControls(row, fieldName, operator, values) {
        var operatorSelect = row.querySelector('.filter-operator-select');
        var valueCell = row.querySelector('.filter-value-cell');
        var fieldConfig = getFieldConfig(fieldName);
        if (!fieldConfig) return;

        // 更新运算符选项
        var operators = getOperatorsForType(fieldConfig.type);
        var opHtml = '';
        for (var i = 0; i < operators.length; i++) {
            var sel = (operators[i].value === operator) ? ' selected' : '';
            opHtml += '<option value="' + operators[i].value + '"' + sel + '>' + operators[i].label + '</option>';
        }
        operatorSelect.innerHTML = opHtml;

        // 更新值控件
        valueCell.innerHTML = buildValueControl(fieldConfig, operator, values || []);
    }

    // 添加一行筛选条件
    function addFilterRow(fieldName, operator, value) {
        var hint = rowsContainer.querySelector('.filter-empty-hint');
        if (hint) hint.style.display = 'none';

        var firstField = config.fields.length > 0 ? config.fields[0] : null;
        var fc = fieldName ? getFieldConfig(fieldName) : firstField;
        if (!fc) return;
        var selectedName = fc.name;
        var selectedOp = operator || (getOperatorsForType(fc.type)[0] ? getOperatorsForType(fc.type)[0].value : 'contains');

        var row = document.createElement('div');
        row.className = 'filter-row';

        row.innerHTML =
            '<select class="filter-field-select" style="min-width:120px;padding:8px 12px;border:1px solid #cbd5e0;border-radius:4px;font-size:14px;background:#fff;">' +
                buildFieldOptions(selectedName) +
            '</select>' +
            '<select class="filter-operator-select" style="min-width:110px;padding:8px 12px;border:1px solid #cbd5e0;border-radius:4px;font-size:14px;background:#fff;">' +
                buildOperatorOptions(fc.type, selectedOp) +
            '</select>' +
            '<div class="filter-value-cell" style="flex:1;display:flex;align-items:center;gap:6px;min-width:150px;">' +
                buildValueControl(fc, selectedOp, value ? [value] : []) +
            '</div>' +
            '<button class="filter-row-remove" style="padding:6px 12px;border:1px solid #feb2b2;background:#fff5f5;color:#c53030;cursor:pointer;border-radius:4px;font-size:13px;white-space:nowrap;">删除</button>';

        rowsContainer.appendChild(row);

        // 字段切换事件
        var fieldSelect = row.querySelector('.filter-field-select');
        fieldSelect.addEventListener('change', function() {
            var currentRow = this.closest('.filter-row');
            var currentOp = currentRow.querySelector('.filter-operator-select');
            var newFieldName = this.value;
            var newFc = getFieldConfig(newFieldName);
            if (!newFc) return;
            var defaultOp = getOperatorsForType(newFc.type)[0] ? getOperatorsForType(newFc.type)[0].value : 'contains';
            updateRowControls(currentRow, newFieldName, defaultOp, []);
        });

        // 运算符切换事件
        var operatorSelect = row.querySelector('.filter-operator-select');
        operatorSelect.addEventListener('change', function() {
            var currentRow = this.closest('.filter-row');
            var fieldSelect = currentRow.querySelector('.filter-field-select');
            var newOp = this.value;
            var fc = getFieldConfig(fieldSelect.value);
            if (fc) {
                updateRowControls(currentRow, fieldSelect.value, newOp, []);
            }
        });

        // 删除事件
        var removeBtn = row.querySelector('.filter-row-remove');
        removeBtn.addEventListener('click', function() {
            rowsContainer.removeChild(row);
            var remaining = rowsContainer.querySelectorAll('.filter-row');
            if (remaining.length === 0) {
                var emptyHint = rowsContainer.querySelector('.filter-empty-hint');
                if (emptyHint) emptyHint.style.display = '';
            }
        });
    }

    // 添加筛选条件按钮
    if (addBtn) {
        addBtn.addEventListener('click', function() { addFilterRow(); });
    }

    // 查询按钮
    if (applyBtn) {
        applyBtn.addEventListener('click', function() {
            if (typeof config.onApply === 'function') {
                config.onApply(collectFilterValues(config.containerId));
            }
        });
    }

    // 重置按钮
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            var rows = rowsContainer.querySelectorAll('.filter-row');
            for (var i = 0; i < rows.length; i++) {
                rows[i].remove();
            }
            var hint = rowsContainer.querySelector('.filter-empty-hint');
            if (hint) hint.style.display = '';
            if (typeof config.onReset === 'function') {
                config.onReset([]);
            }
        });
    }
}

/* ========== 通用批量导入模块 ========== */

/**
 * 初始化批量导入组件
 * @param {object} config
 * @param {string} config.entityType    - 实体类型，如 'student', 'teacher', 'course'
 * @param {string[]} config.previewColumns - 预览表表头列名（从 CSV 表头映射到显示名称）
 * @param {number} [config.requiredFieldIndex] - 必填字段的列索引
 * @param {string} [config.requiredFieldName]  - 必填字段名称（用于错误提示）
 * @param {function} [config.onImportSuccess]  - 导入成功后的回调（如重新加载表格）
 * @param {string} [config.containerId]        - 组件容器 ID，默认 'batch_import_area'
 */
function initBatchImport(config) {
    if (!config || !config.entityType) {
        console.error('initBatchImport: entityType is required');
        return;
    }

    var containerId = config.containerId || 'batchImportModal';
    var container = document.getElementById(containerId);
    if (!container) return;

    var entityType = config.entityType;
    var previewColumns = config.previewColumns || [];
    var requiredFieldIndex = config.requiredFieldIndex;
    var requiredFieldName = config.requiredFieldName || '';
    var onImportSuccess = config.onImportSuccess || function() { window.location.reload(); };

    // ── 元素引用 ──
    var templateLink = container.querySelector('#batch_import_template_link');
    var exportLink = container.querySelector('#batch_export_link');
    var fileInput = container.querySelector('#batch_import_file_input');
    var previewBtn = container.querySelector('#batch_import_preview_btn');
    var previewArea = container.querySelector('#batch_import_preview_area');
    var previewThead = container.querySelector('#batch_import_preview_thead');
    var previewTbody = container.querySelector('#batch_import_preview_tbody');
    var previewErrors = container.querySelector('#batch_import_preview_errors');
    var confirmBtn = container.querySelector('#batch_import_confirm_btn');
    var cancelBtn = container.querySelector('#batch_import_cancel_btn');
    var closeBtn = container.querySelector('#batchImportModalClose');

    var pendingData = null;

    // 设置模板下载和导出链接
    if (templateLink) {
        templateLink.href = '/api/import/' + entityType + '/template';
    }
    if (exportLink) {
        exportLink.href = '/api/import/' + entityType + '/export';
    }

    // ── 预览按钮 ──
    if (previewBtn) {
        previewBtn.addEventListener('click', function() {
            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                alert('请先选择 CSV 文件');
                return;
            }
            var file = fileInput.files[0];
            var reader = new FileReader();
            reader.onload = function(e) {
                var text = e.target.result;
                var parsed = parse_csv_content(text);
                var validated = validate_batch_csv_data(parsed.rows, requiredFieldIndex, requiredFieldName);
                render_batch_preview(validated, previewColumns);
                pendingData = validated.valid_data;
                hide_loading();
            };
            reader.onerror = function() {
                alert('文件读取失败');
                hide_loading();
            };
            show_loading();
            reader.readAsText(file);
        });
    }

    // ── 渲染预览 ──
    function render_batch_preview(res, columns) {
        if (!previewTbody || !previewThead) return;
        previewTbody.innerHTML = '';
        previewThead.innerHTML = '';

        // 渲染表头
        var headerRow = document.createElement('tr');
        for (var i = 0; i < columns.length; i++) {
            var th = document.createElement('th');
            th.textContent = columns[i];
            headerRow.appendChild(th);
        }
        previewThead.appendChild(headerRow);

        // 渲染错误
        if (previewErrors) {
            if (res.errors && res.errors.length > 0) {
                previewErrors.textContent = res.errors.join('；');
                previewErrors.style.display = 'block';
            } else {
                previewErrors.style.display = 'none';
            }
        }

        // 渲染数据行
        if (res.valid_data && res.valid_data.length > 0) {
            for (var r = 0; r < res.valid_data.length; r++) {
                var row = res.valid_data[r];
                var tr = document.createElement('tr');
                for (var c = 0; c < columns.length; c++) {
                    var td = document.createElement('td');
                    td.textContent = (row[c] !== null && row[c] !== undefined) ? String(row[c]) : '';
                    tr.appendChild(td);
                }
                previewTbody.appendChild(tr);
            }
            if (confirmBtn) confirmBtn.style.display = '';
        } else {
            var tr = document.createElement('tr');
            var td = document.createElement('td');
            td.colSpan = columns.length || 1;
            td.textContent = '无有效数据';
            td.className = 'empty-row';
            tr.appendChild(td);
            previewTbody.appendChild(tr);
            if (confirmBtn) confirmBtn.style.display = 'none';
        }

        if (previewArea) previewArea.style.display = 'block';
    }

    // ── 确认导入 ──
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            if (!pendingData || pendingData.length === 0) {
                alert('没有有效数据可导入');
                return;
            }

            show_loading();
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/import/' + entityType + '/import', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.setRequestHeader('X-CSRF-Token', _csrf_token);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    hide_loading();
                    if (xhr.status === 200) {
                        try {
                            var res = JSON.parse(xhr.responseText);
                            if (res.code === 0) {
                                alert('导入成功，共导入 ' + (res.count || 0) + ' 条数据');
                                cancel_batch_preview();
                                if (typeof onImportSuccess === 'function') {
                                    onImportSuccess();
                                }
                            } else {
                                alert('导入失败：' + (res.msg || '未知错误'));
                            }
                        } catch (err) {
                            alert('导入响应解析失败');
                        }
                    } else {
                        alert('导入请求失败，状态码：' + xhr.status);
                    }
                }
            };
            xhr.send(JSON.stringify({data: pendingData}));
        });
    }

    // ── 取消 ──
    function cancel_batch_preview() {
        if (previewArea) previewArea.style.display = 'none';
        if (previewTbody) previewTbody.innerHTML = '';
        if (previewThead) previewThead.innerHTML = '';
        if (previewErrors) { previewErrors.style.display = 'none'; previewErrors.textContent = ''; }
        pendingData = null;
        if (fileInput) fileInput.value = '';
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', cancel_batch_preview);
    }

    // ── 弹窗关闭 ──
    function closeImportModal() {
        container.classList.remove('active');
        cancel_batch_preview();
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', closeImportModal);
    }
    container.addEventListener('click', function(e) {
        if (e.target === container) {
            closeImportModal();
        }
    });
}

/**
 * 打开批量导入/导出弹窗（由页面按钮调用）
 */
function openBatchImportModal() {
    var modal = document.getElementById('batchImportModal');
    if (modal) {
        modal.classList.add('active');
    }
}

/**
 * 验证批量导入的 CSV 数据行
 * @param {string[][]} rows - 数据行数组
 * @param {number} requiredFieldIndex - 必填字段的列索引（可选）
 * @param {string} requiredFieldName - 必填字段名称（可选）
 * @returns {{valid_data: string[][], errors: string[]}}
 */
function validate_batch_csv_data(rows, requiredFieldIndex, requiredFieldName) {
    var valid_data = [];
    var errors = [];
    var seen = {};

    for (var i = 0; i < rows.length; i++) {
        var row = rows[i];
        var row_num = i + 2; // header is row 1
        var row_errors = [];

        // 必填字段校验
        if (requiredFieldIndex !== undefined && requiredFieldIndex !== null) {
            var fieldVal = row[requiredFieldIndex];
            if (!fieldVal || String(fieldVal).trim() === '') {
                var fname = requiredFieldName || ('第' + (requiredFieldIndex + 1) + '列');
                row_errors.push('第' + row_num + '行：' + fname + '不能为空');
            } else if (seen[String(fieldVal).trim()]) {
                row_errors.push('第' + row_num + '行：' + fname + ' "' + String(fieldVal).trim() + '" 在文件中重复');
            }
        }

        if (row_errors.length === 0) {
            if (requiredFieldIndex !== undefined && requiredFieldIndex !== null && row[requiredFieldIndex]) {
                seen[String(row[requiredFieldIndex]).trim()] = true;
            }
            valid_data.push(row);
        } else {
            errors = errors.concat(row_errors);
        }
    }

    return {valid_data: valid_data, errors: errors};
}

/* ========== 可排序列头 ========== */

/**
 * 初始化可排序列头
 * @param {object} config
 * @param {string} config.tableId     - 表格容器 ID（用于定位 th）
 * @param {function} config.onSort    - 排序回调，接收 { sort_by, sort_order }
 * @param {object} config.initialSort - 初始排序 { sort_by, sort_order }，可选
 */
function initSortableTable(config) {
    if (!config || !config.tableId || !config.onSort) return;

    var table = document.getElementById(config.tableId);
    if (!table) return;

    var state = {
        sort_by: (config.initialSort && config.initialSort.sort_by) || '',
        sort_order: (config.initialSort && config.initialSort.sort_order) || 'asc'
    };

    var headers = table.querySelectorAll('th[data-sort]');

    // 恢复初始排序指示
    if (state.sort_by) {
        headers.forEach(function(th) {
            if (th.getAttribute('data-sort') === state.sort_by) {
                th.classList.add('sortable', state.sort_order === 'asc' ? 'sort-asc' : 'sort-desc');
            } else {
                th.classList.add('sortable');
            }
        });
    } else {
        headers.forEach(function(th) { th.classList.add('sortable'); });
    }

    headers.forEach(function(th) {
        th.addEventListener('click', function() {
            var field = th.getAttribute('data-sort');
            if (!field) return;

            // 切换排序方向
            if (state.sort_by === field) {
                state.sort_order = state.sort_order === 'asc' ? 'desc' : 'asc';
            } else {
                state.sort_by = field;
                state.sort_order = 'asc';
            }

            // 更新样式
            headers.forEach(function(h) {
                h.classList.remove('sort-asc', 'sort-desc');
            });
            th.classList.add(state.sort_order === 'asc' ? 'sort-asc' : 'sort-desc');

            // 触发回调
            config.onSort({
                sort_by: state.sort_by,
                sort_order: state.sort_order
            });
        });
    });

    // 返回状态，可用于外部读取
    return state;
}

/* ========== 全局错误处理 ========== */
window.addEventListener('error', function(e) {
    console.error('Global error:', e.message, 'at', e.filename, 'line', e.lineno);
    // 忽略网络资源加载失败的噪音（如 CDN 引用）
    if (e.target !== window) return;
    // 开发环境可在这里添加错误上报
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    // 防止未处理的 Promise 导致静默失败
    if (e.reason && e.reason.message) {
        console.error('Rejection reason:', e.reason.message);
    }
});

/* ========== 模拟数据填充 ========== */

function openMockDataModal() {
    var modal = document.getElementById('mock-data-modal');
    if (modal) modal.classList.add('active');
    // 重置状态
    var selectAll = document.getElementById('mock-select-all');
    if (selectAll) selectAll.checked = false;
    var cbs = document.querySelectorAll('.mock-table-cb');
    for (var i = 0; i < cbs.length; i++) cbs[i].checked = false;
    var msg = document.getElementById('mock-data-msg');
    var success = document.getElementById('mock-data-success');
    if (msg) msg.style.display = 'none';
    if (success) success.style.display = 'none';
    var btn = document.getElementById('mock-data-submit-btn');
    if (btn) btn.disabled = false;
}

function closeMockDataModal() {
    var modal = document.getElementById('mock-data-modal');
    if (modal) modal.classList.remove('active');
}

// 点击遮罩层关闭
document.addEventListener('DOMContentLoaded', function() {
    var mockModal = document.getElementById('mock-data-modal');
    if (mockModal) {
        mockModal.addEventListener('click', function(e) {
            if (e.target === mockModal) closeMockDataModal();
        });
    }
});

function toggleMockSelectAll() {
    var selectAll = document.getElementById('mock-select-all');
    if (!selectAll) return;
    var checked = selectAll.checked;
    var cbs = document.querySelectorAll('.mock-table-cb');
    for (var i = 0; i < cbs.length; i++) {
        cbs[i].checked = checked;
    }
}

// 单个复选框变化时更新全选状态
document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('change', function(e) {
        if (!e.target.classList.contains('mock-table-cb')) return;
        var cbs = document.querySelectorAll('.mock-table-cb');
        var allChecked = true;
        for (var i = 0; i < cbs.length; i++) {
            if (!cbs[i].checked) { allChecked = false; break; }
        }
        var selectAll = document.getElementById('mock-select-all');
        if (selectAll) selectAll.checked = allChecked;
    });
});

function submitMockData() {
    var cbs = document.querySelectorAll('.mock-table-cb');
    var tables = [];
    for (var i = 0; i < cbs.length; i++) {
        if (cbs[i].checked) tables.push(cbs[i].value);
    }
    if (tables.length === 0) {
        var msg = document.getElementById('mock-data-msg');
        if (msg) { msg.textContent = '请至少选择一个数据表'; msg.style.display = 'block'; }
        return;
    }

    var btn = document.getElementById('mock-data-submit-btn');
    var msg = document.getElementById('mock-data-msg');
    var success = document.getElementById('mock-data-success');
    if (msg) msg.style.display = 'none';
    if (success) success.style.display = 'none';
    if (btn) { btn.disabled = true; btn.textContent = '生成中...'; }

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/mock-data/generate', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('X-CSRF-Token', _csrf_token);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (btn) { btn.disabled = false; btn.textContent = '确认生成'; }
            var resp;
            try { resp = JSON.parse(xhr.responseText); } catch(e) { resp = {}; }
            if (resp.code === 0) {
                if (success) {
                    success.textContent = resp.msg + ' (' + (resp.data && resp.data.detail || '') + ')';
                    success.style.display = 'block';
                }
                // 刷新仪表盘统计
                setTimeout(function() {
                    if (typeof loadDashboardStats === 'function') {
                        loadDashboardStats();
                    }
                }, 500);
            } else {
                if (msg) { msg.textContent = resp.msg || '生成失败'; msg.style.display = 'block'; }
            }
        }
    };
    xhr.send(JSON.stringify({ tables: tables }));
}

/* ========== 综合查询 ========== */
(function() {
    // 仅在综合查询页面执行
    if (!document.getElementById('panel-comprehensive') && !document.getElementById('comp-main-table')) return;

    var compState = {
        mainTable: '',
        availableRelations: [],
        selectedJoins: [],
        allFields: [],
        currentPage: 1,
        totalPages: 0,
        currentFilters: [],
        compPager: null,
    };

    // 元素引用
    var mainTableSelect = document.getElementById('comp-main-table');
    var relationsSection = document.getElementById('comp-relations-section');
    var relationsList = document.getElementById('comp-relations-list');
    var relationsEmpty = document.getElementById('comp-relations-empty');
    var fieldsPreview = document.getElementById('comp-fields-preview');
    var fieldsTags = document.getElementById('comp-fields-tags');
    var filterSection = document.getElementById('comp-filter-section');
    var actionsDiv = document.getElementById('comp-actions');
    var btnQuery = document.getElementById('comp-btn-query');
    var btnResetAll = document.getElementById('comp-btn-reset-all');
    var btnAddFilter = document.getElementById('comp-btn-add-filter');
    var btnResetFilters = document.getElementById('comp-btn-reset-filters');
    var filterRows = document.getElementById('comp-filter-rows');
    var resultDiv = document.getElementById('comp-result');
    var emptyDiv = document.getElementById('comp-empty');
    var tableEl = document.getElementById('comp-table');
    var resultStats = document.getElementById('comp-result-stats');
    var paginationDiv = document.getElementById('comp-pagination');
    var loadingDiv = document.getElementById('comp-loading');

    // 1. 加载主表列表
    function loadMainTables() {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/api/query/comprehensive/tables', true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                try {
                    var resp = JSON.parse(xhr.responseText);
                    if (resp.ok && resp.data) {
                        renderMainTableOptions(resp.data);
                    }
                } catch (e) {}
            }
        };
        xhr.send();
    }

    function renderMainTableOptions(tables) {
        var html = '<option value="">-- 请选择主表 --</option>';
        for (var i = 0; i < tables.length; i++) {
            html += '<option value="' + tables[i].name + '">' +
                escape_html(tables[i].label) + ' (' + tables[i].column_count + ' 个字段)</option>';
        }
        mainTableSelect.innerHTML = html;
    }

    // 2. 主表切换
    mainTableSelect.addEventListener('change', function() {
        var tableName = this.value;
        resetAll(true);

        if (!tableName) {
            compState.mainTable = '';
            hideSections();
            return;
        }

        compState.mainTable = tableName;
        loadTableRelations(tableName);
        loadTableFields(tableName);
        filterSection.style.display = '';
        actionsDiv.style.display = '';
    });

    function loadTableRelations(tableName) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/api/query/comprehensive/table/' + tableName + '/relations', true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                try {
                    var resp = JSON.parse(xhr.responseText);
                    if (resp.ok) {
                        compState.availableRelations = resp.data || [];
                        renderRelations(compState.availableRelations);
                    }
                } catch (e) {}
            }
        };
        xhr.send();
    }

    function renderRelations(relations) {
        relationsSection.style.display = '';

        if (relations.length === 0) {
            relationsList.innerHTML = '';
            relationsEmpty.style.display = '';
            compState.selectedJoins = [];
            return;
        }

        relationsEmpty.style.display = 'none';
        var html = '';
        for (var i = 0; i < relations.length; i++) {
            var rel = relations[i];
            html += '<label class="comp-relation-item">';
            html += '<input type="checkbox" class="comp-relation-cb" ' +
                'data-join=\'' + JSON.stringify(rel) + '\'> ';
            html += '<span class="comp-relation-text">' +
                escape_html(rel.from_label) + '.' + escape_html(rel.from_column) +
                ' \u2192 ' +
                escape_html(rel.to_label) + '.' + escape_html(rel.to_column) +
                '</span>';
            html += '</label>';
        }
        relationsList.innerHTML = html;

        var cbs = relationsList.querySelectorAll('.comp-relation-cb');
        for (var j = 0; j < cbs.length; j++) {
            cbs[j].addEventListener('change', function() {
                updateSelectedJoins();
                refreshFilterFields();
            });
        }
    }

    function updateSelectedJoins() {
        var cbs = relationsList.querySelectorAll('.comp-relation-cb:checked');
        compState.selectedJoins = [];
        for (var i = 0; i < cbs.length; i++) {
            try {
                var joinData = JSON.parse(cbs[i].getAttribute('data-join'));
                compState.selectedJoins.push(joinData);
            } catch (e) {}
        }
    }

    function loadTableFields(tableName) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/api/query/comprehensive/table/' + tableName + '/fields', true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                try {
                    var resp = JSON.parse(xhr.responseText);
                    if (resp.ok && resp.data) {
                        renderFieldsPreview(resp.data, tableName);
                        refreshFilterFields();
                    }
                } catch (e) {}
            }
        };
        xhr.send();
    }

    function renderFieldsPreview(fields, tableName) {
        fieldsPreview.style.display = '';
        var html = '<h4>主表字段 (' + fields.length + ' 个)</h4><div class="comp-fields-tags">';
        for (var i = 0; i < fields.length; i++) {
            var f = fields[i];
            html += '<span class="comp-field-tag" title="' + f.type + '">' +
                escape_html(f.label) + (f.is_pk ? ' \uD83D\uDD11' : '') + '</span>';
        }
        html += '</div>';
        fieldsTags.innerHTML = html;
    }

    function refreshFilterFields() {
        var tablesToLoad = [compState.mainTable];
        for (var i = 0; i < compState.selectedJoins.length; i++) {
            var toTable = compState.selectedJoins[i].to_table;
            if (tablesToLoad.indexOf(toTable) === -1) {
                tablesToLoad.push(toTable);
            }
        }

        var loaded = 0;
        compState.allFields = [];

        for (var j = 0; j < tablesToLoad.length; j++) {
            (function(tbl) {
                var xhr = new XMLHttpRequest();
                xhr.open('GET', '/api/query/comprehensive/table/' + tbl + '/fields', true);
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4 && xhr.status === 200) {
                        try {
                            var resp = JSON.parse(xhr.responseText);
                            if (resp.ok && resp.data) {
                                for (var k = 0; k < resp.data.length; k++) {
                                    var f = resp.data[k];
                                    compState.allFields.push({
                                        table: tbl,
                                        name: f.name,
                                        label: f.label,
                                        type: f.type,
                                    });
                                }
                            }
                        } catch (e) {}
                        loaded++;
                        if (loaded >= tablesToLoad.length) {
                            renderFilterRows();
                        }
                    }
                };
                xhr.send();
            })(tablesToLoad[j]);
        }
    }

    // 3. 筛选条件
    var COMP_FILTER_ROW_COUNT = 0;

    function addCompFilterRow() {
        COMP_FILTER_ROW_COUNT++;
        var rowId = 'comp-filter-row-' + COMP_FILTER_ROW_COUNT;

        var fieldOptions = '<option value="">选择字段</option>';
        for (var i = 0; i < compState.allFields.length; i++) {
            var f = compState.allFields[i];
            fieldOptions += '<option value="' + f.table + '|' + f.name + '">' +
                escape_html(f.label) + '</option>';
        }

        var operatorOptions = '<option value="=">等于</option>' +
            '<option value="!=">不等于</option>' +
            '<option value="LIKE">包含</option>' +
            '<option value=">">大于</option>' +
            '<option value="<">小于</option>' +
            '<option value=">=">大于等于</option>' +
            '<option value="<=">小于等于</option>' +
            '<option value="IN">多值</option>';

        var row = document.createElement('div');
        row.className = 'filter-row';
        row.id = rowId;
        row.innerHTML =
            '<select class="comp-filter-field" style="min-width:130px;padding:8px;border:1px solid #cbd5e0;border-radius:4px;">' +
                fieldOptions +
            '</select>' +
            '<select class="comp-filter-operator" style="min-width:100px;padding:8px;border:1px solid #cbd5e0;border-radius:4px;">' +
                operatorOptions +
            '</select>' +
            '<input type="text" class="comp-filter-value" placeholder="筛选值" style="flex:1;min-width:150px;padding:8px;border:1px solid #cbd5e0;border-radius:4px;">' +
            '<button class="comp-filter-remove">删除</button>';

        filterRows.appendChild(row);

        var hint = document.getElementById('comp-filter-empty-hint');
        if (hint) hint.style.display = 'none';

        row.querySelector('.comp-filter-remove').addEventListener('click', function() {
            filterRows.removeChild(row);
            var remaining = filterRows.querySelectorAll('.filter-row');
            if (remaining.length === 0) {
                var h = document.getElementById('comp-filter-empty-hint');
                if (h) h.style.display = '';
            }
        });
    }

    function collectCompFilters() {
        var rows = filterRows.querySelectorAll('.filter-row');
        var filters = [];
        for (var i = 0; i < rows.length; i++) {
            var fieldSelect = rows[i].querySelector('.comp-filter-field');
            var opSelect = rows[i].querySelector('.comp-filter-operator');
            var valInput = rows[i].querySelector('.comp-filter-value');

            if (!fieldSelect || !opSelect || !valInput) continue;
            var fieldVal = fieldSelect.value;
            if (!fieldVal) continue;
            var parts = fieldVal.split('|');
            var table = parts[0];
            var field = parts[1];
            var operator = opSelect.value;
            var value = valInput.value.trim();
            if (!value && operator !== 'IS NULL' && operator !== 'IS NOT NULL') continue;

            filters.push({
                table: table,
                field: field,
                operator: operator,
                value: value,
            });
        }
        return filters;
    }

    function renderFilterRows() {
        var existingRows = filterRows.querySelectorAll('.filter-row');
        for (var i = 0; i < existingRows.length; i++) {
            existingRows[i].remove();
        }
        COMP_FILTER_ROW_COUNT = 0;
        var hint = document.getElementById('comp-filter-empty-hint');
        if (hint) hint.style.display = '';
    }

    if (btnAddFilter) {
        btnAddFilter.addEventListener('click', function() {
            if (compState.allFields.length === 0) {
                alert('请先选择主表');
                return;
            }
            addCompFilterRow();
        });
    }

    if (btnResetFilters) {
        btnResetFilters.addEventListener('click', function() {
            renderFilterRows();
        });
    }

    // 4. 执行查询
    if (btnQuery) {
        btnQuery.addEventListener('click', function() {
            compState.currentPage = 1;
            executeQuery(1);
        });
    }

    function executeQuery(page) {
        var filters = collectCompFilters();
        compState.currentFilters = filters;
        compState.currentPage = page;

        var payload = {
            main_table: compState.mainTable,
            joins: compState.selectedJoins,
            filters: filters,
            page: page,
        };

        loadingDiv.style.display = 'flex';
        resultDiv.style.display = 'none';
        emptyDiv.style.display = 'none';
        resultStats.style.display = 'none';

        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/query/comprehensive/execute', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('X-CSRF-Token', _csrf_token);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                loadingDiv.style.display = 'none';
                if (xhr.status === 200) {
                    try {
                        var resp = JSON.parse(xhr.responseText);
                        renderResults(resp);
                    } catch (e) {
                        alert('响应解析失败');
                    }
                } else {
                    alert('查询请求失败');
                }
            }
        };
        xhr.send(JSON.stringify(payload));
    }

    function renderResults(resp) {
        if (!resp.ok) {
            alert(resp.error || '查询失败');
            return;
        }

        var columns = resp.columns || [];
        var data = resp.data || [];
        var total = resp.total || 0;

        resultStats.style.display = '';
        document.getElementById('comp-total-count').textContent = total;

        if (data.length === 0) {
            resultDiv.style.display = '';
            tableEl.innerHTML = '<thead></thead><tbody></tbody>';
            emptyDiv.style.display = 'block';
            paginationDiv.style.display = 'none';
            return;
        }

        emptyDiv.style.display = 'none';
        resultDiv.style.display = '';

        var thead = '<thead><tr>';
        for (var i = 0; i < columns.length; i++) {
            thead += '<th title="' + escape_html(columns[i].key) + '">' +
                escape_html(columns[i].label) + '</th>';
        }
        thead += '</tr></thead>';

        var tbody = '<tbody>';
        for (var r = 0; r < data.length; r++) {
            tbody += '<tr>';
            for (var c = 0; c < columns.length; c++) {
                var val = data[r][columns[c].key];
                tbody += '<td>' + escape_html(val !== null && val !== undefined ? String(val) : '') + '</td>';
            }
            tbody += '</tr>';
        }
        tbody += '</tbody>';

        tableEl.innerHTML = thead + tbody;

        updateCompPagination(resp.page || 1, resp.total_pages || 1, total);
    }

    function updateCompPagination(page, totalPages, total) {
        if (totalPages <= 1 && total <= 20) {
            paginationDiv.style.display = 'none';
            return;
        }
        paginationDiv.style.display = '';

        if (!compState.compPager) {
            compState.compPager = new Pagination({
                container: paginationDiv,
                totalPages: totalPages,
                currentPage: page,
                total: total,
                onChange: function(p) {
                    executeQuery(p);
                },
            });
        } else {
            compState.compPager.update({
                currentPage: page,
                totalPages: totalPages,
                total: total,
            });
        }
    }

    // 5. 重置
    function resetAll(keepMainTable) {
        resultDiv.style.display = 'none';
        emptyDiv.style.display = 'none';
        resultStats.style.display = 'none';
        paginationDiv.style.display = 'none';
        if (tableEl) tableEl.innerHTML = '';

        if (!keepMainTable) {
            compState.mainTable = '';
            mainTableSelect.value = '';
        }

        compState.availableRelations = [];
        compState.selectedJoins = [];
        compState.allFields = [];
        hideSections();

        renderFilterRows();
        compState.currentPage = 1;
        compState.compPager = null;
    }

    function hideSections() {
        relationsSection.style.display = 'none';
        relationsList.innerHTML = '';
        relationsEmpty.style.display = 'none';
        fieldsPreview.style.display = 'none';
        fieldsTags.innerHTML = '';
    }

    if (btnResetAll) {
        btnResetAll.addEventListener('click', function() {
            resetAll(false);
        });
    }

    // 初始化
    loadMainTables();
})();


