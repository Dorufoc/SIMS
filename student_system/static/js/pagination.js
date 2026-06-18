/**
 * 通用分页组件
 * 统一项目中所有表格控件的分页逻辑、样式和交互
 *
 * 使用方式：
 *   1. 在HTML中放置 <div class="pagination" id="pagination"></div>
 *   2. 创建分页实例：
 *      var pager = new Pagination({
 *          container: 'pagination',
 *          totalPages: 10,
 *          currentPage: 1,
 *          range: 2,
 *          onChange: function(page) { loadData(page); }
 *      });
 *   3. 数据加载完成后更新：
 *      pager.update({ currentPage: page, totalPages: totalPages, total: total });
 */
(function () {
    'use strict';

    var Pagination = function (options) {
        options = options || {};
        this.container = typeof options.container === 'string'
            ? document.getElementById(options.container)
            : options.container;
        if (!this.container) {
            throw new Error('Pagination: container element not found');
        }

        this.totalPages = options.totalPages || 1;
        this.currentPage = options.currentPage || 1;
        this.range = options.range || 2;           // 当前页前后显示的页码数
        this.pageSize = options.pageSize || 10;
        this.total = options.total || 0;
        this.onChange = typeof options.onChange === 'function' ? options.onChange : function () {};
        this._transitionTimer = null;

        this.render();
    };

    /**
     * 更新分页状态（数据加载完成后调用）
     */
    Pagination.prototype.update = function (options) {
        if (options.totalPages !== undefined) this.totalPages = Math.max(1, options.totalPages);
        if (options.currentPage !== undefined) this.currentPage = Math.max(1, Math.min(options.currentPage, this.totalPages));
        if (options.total !== undefined) this.total = options.total;
        if (options.pageSize !== undefined) this.pageSize = options.pageSize;
        if (options.range !== undefined) this.range = options.range;
        this.render();
    };

    /**
     * 跳转到指定页
     */
    Pagination.prototype.goTo = function (page) {
        page = parseInt(page, 10);
        if (isNaN(page) || page < 1 || page > this.totalPages || page === this.currentPage) return;
        this.currentPage = page;
        this._animateTransition();
        this.render();
        this.onChange(page);
    };

    /**
     * 上一页
     */
    Pagination.prototype.prev = function () {
        if (this.currentPage > 1) this.goTo(this.currentPage - 1);
    };

    /**
     * 下一页
     */
    Pagination.prototype.next = function () {
        if (this.currentPage < this.totalPages) this.goTo(this.currentPage + 1);
    };

    /**
     * 平滑过渡动画
     */
    Pagination.prototype._animateTransition = function () {
        var container = this.container;
        container.classList.add('paging-transition');
        if (this._transitionTimer) clearTimeout(this._transitionTimer);
        this._transitionTimer = setTimeout(function () {
            container.classList.remove('paging-transition');
        }, 300);
    };

    /**
     * 生成页码数组（含省略号标记）
     * 返回: [1, '...', 3, 4, 5, '...', 10]
     */
    Pagination.prototype._generatePages = function () {
        var total = this.totalPages;
        var current = this.currentPage;
        var range = this.range;
        var pages = [];

        if (total <= 1) return pages;

        // 总页数较少时直接显示全部
        if (total <= range * 2 + 3) {
            for (var i = 1; i <= total; i++) pages.push(i);
            return pages;
        }

        // 始终显示首页
        pages.push(1);

        var rangeStart = Math.max(2, current - range);
        var rangeEnd = Math.min(total - 1, current + range);

        // 首页和中间区域之间的省略号
        if (rangeStart > 2) pages.push('...');

        // 中间页码
        for (var j = rangeStart; j <= rangeEnd; j++) pages.push(j);

        // 中间区域和末页之间的省略号
        if (rangeEnd < total - 1) pages.push('...');

        // 始终显示末页
        pages.push(total);

        return pages;
    };

    /**
     * 渲染分页组件
     */
    Pagination.prototype.render = function () {
        var container = this.container;
        var total = this.totalPages;
        var current = this.currentPage;

        container.innerHTML = '';
        if (total <= 1 && this.total <= 0) return;

        var fragment = document.createDocumentFragment();

        // ===== 上一页 =====
        fragment.appendChild(this._createBtn('\u00AB', function () { this.goTo(1); }, current <= 1, 'page-first'));
        fragment.appendChild(this._createBtn('\u2039', function () { this.prev(); }, current <= 1, 'page-prev'));

        // ===== 页码 =====
        var pages = this._generatePages();
        for (var i = 0; i < pages.length; i++) {
            var p = pages[i];
            if (p === '...') {
                var ellipsis = document.createElement('span');
                ellipsis.className = 'page-ellipsis';
                ellipsis.textContent = '\u2026';
                fragment.appendChild(ellipsis);
            } else {
                fragment.appendChild(this._createBtn(p, function (page) { this.goTo(page); }, false, p === current ? 'page-btn active' : 'page-btn', p));
            }
        }

        // ===== 下一页 =====
        fragment.appendChild(this._createBtn('\u203A', function () { this.next(); }, current >= total, 'page-next'));
        fragment.appendChild(this._createBtn('\u00BB', function () { this.goTo(total); }, current >= total, 'page-last'));

        // ===== 跳转输入 =====
        var jumpWrap = document.createElement('span');
        jumpWrap.className = 'page-jump';

        var jumpLabel = document.createElement('span');
        jumpLabel.className = 'page-jump-label';
        jumpLabel.textContent = '\u8DF3\u8F6C\u5230';
        jumpWrap.appendChild(jumpLabel);

        var jumpInput = document.createElement('input');
        jumpInput.type = 'number';
        jumpInput.className = 'page-jump-input';
        jumpInput.min = 1;
        jumpInput.max = total;
        jumpInput.placeholder = '';
        jumpInput.value = '';
        // 数值验证
        jumpInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') triggerJump();
        });
        jumpInput.addEventListener('blur', function () {
            validateJumpInput(this);
        });
        jumpWrap.appendChild(jumpInput);

        var jumpUnit = document.createElement('span');
        jumpUnit.className = 'page-jump-unit';
        jumpUnit.textContent = '\u9875';
        jumpWrap.appendChild(jumpUnit);

        var jumpBtn = document.createElement('button');
        jumpBtn.className = 'page-jump-btn';
        jumpBtn.textContent = 'GO';
        jumpBtn.addEventListener('click', triggerJump);
        jumpWrap.appendChild(jumpBtn);

        fragment.appendChild(jumpWrap);

        // 跳转逻辑
        var self = this;
        function validateJumpInput(input) {
            var val = parseInt(input.value, 10);
            if (isNaN(val) || val < 1) input.value = 1;
            else if (val > total) input.value = total;
        }
        function triggerJump() {
            var val = parseInt(jumpInput.value, 10);
            if (isNaN(val) || val < 1 || val > total) {
                validateJumpInput(jumpInput);
                val = parseInt(jumpInput.value, 10);
            }
            if (!isNaN(val) && val >= 1 && val <= total && val !== current) {
                self.goTo(val);
            }
            jumpInput.value = '';
        }

        container.appendChild(fragment);
    };

    /**
     * 创建分页按钮
     */
    Pagination.prototype._createBtn = function (text, clickHandler, disabled, className, page) {
        var btn = document.createElement('button');
        btn.className = className || 'page-btn';
        btn.textContent = text;
        if (disabled) btn.disabled = true;

        var self = this;
        btn.addEventListener('click', function () {
            if (btn.disabled) return;
            if (page !== undefined) {
                clickHandler.call(self, page);
            } else {
                clickHandler.call(self);
            }
        });

        return btn;
    };

    // 暴露到全局
    window.Pagination = Pagination;
})();
