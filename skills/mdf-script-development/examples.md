# 脚本示例

本文档是 `mdf-script-development` skill 的支持文件，提供从简单到复杂的完整脚本示例。

## 示例 1：简单按钮控制

最简单的脚本：初始化时隐藏一个按钮。

```javascript
// 初始化隐藏按钮
viewModel.on('customInit', function () {
    viewModel.get('button31if') && viewModel.get('button31if').setVisible(false);
});
```

---

## 示例 2：字段联动

字段值变化后联动更新其他字段。

```javascript
// 组织变化后联动更新下属单位
viewModel.on('customInit', function () {
    viewModel.get('pk_org').on('afterValueChange', function (data) {
        var orgId = data.value;
        if (!orgId) {
            viewModel.get('pk_unit').setValue('');
            viewModel.get('pk_unit_name').setValue('');
            return;
        }

        // 同步查询并填充
        var result = cb.rest.invokeFunction(
            'querySubUnits',
            { pk_org: orgId },
            null, null,
            { async: false }
        );

        if (result && result.length > 0) {
            viewModel.get('pk_unit').setValue(result[0].id);
            viewModel.get('pk_unit_name').setValue(result[0].name);
        }
    });
});
```

---

## 示例 3：表格单元格联动 + 校验

单元格值变化后联动更新并校验。

```javascript
viewModel.on('customInit', function () {
    viewModel.enableFeature('asyncSave');
});

viewModel.on('afterLoadData', function () {
    var grid = viewModel.getGridModel('bodyvos');
    if (!grid) return;

    // 设置某些列只读
    grid.setColumnState('equip_code', 'disabled', true);
});

viewModel.getGridModel('bodyvos').on('afterCellValueChange', function (data) {
    var grid = viewModel.getGridModel('bodyvos');
    var rowIndex = data.rowIndex;

    // 盘到标识联动
    if (data.cellName === 'inventory_flag') {
        var isFound = data.value;
        grid.setCellValue(rowIndex, 'inventory_verfiresult', isFound ? '1' : '');
        grid.setCellValue(rowIndex, 'inventory_result', isFound ? '1' : '2');
    }
});

viewModel.on('beforeValidate', function () {
    var grid = viewModel.getGridModel('bodyvos');
    if (!grid) return true;
    var rows = grid.getRows();

    for (var i = 0; i < rows.length; i++) {
        if (!rows[i].equip_code) {
            cb.utils.alert('第 ' + (i + 1) + ' 行缺少装备编码', 'error');
            return false;
        }
    }
    return true;
});

viewModel.on('batchModifySetFields', function (data) {
    data.setFields = data.setFields.filter(function (field) {
        return field.key === 'inventory_flag'
            || field.key === 'inventory_verfiresult';
    });
});
```

---

## 示例 4：参照过滤 + API 调用

完整的参照过滤、按钮点击、API 调用、刷新流程。

```javascript
viewModel.on('customInit', function () {
    // 参照过滤：资产只能选择当前组织的
    viewModel.get('pk_asset').on('beforeBrowse', function (arg) {
        var orgId = viewModel.get('pk_org').getValue();
        if (!orgId) return;

        arg.context.setFilter({
            isExtend: true,
            simpleVOs: [
                { field: 'pk_org', op: 'eq', value1: orgId },
                { field: 'status', op: 'eq', value1: 'ACTIVE' }
            ]
        });
    });
});

// 自定义按钮：同步资产
viewModel.get('btnSync') && viewModel.get('btnSync').on('click', function () {
    var pk_org = viewModel.get('pk_org').getValue();
    if (!pk_org) {
        cb.utils.alert('请先选择组织', 'error');
        return;
    }

    cb.utils.confirm('确定要同步资产数据吗？', function () {
        cb.utils.loadingControl.start({ diworkCode: 'sync-assets' });

        var domainKey = viewModel.getDomainKey();
        var proxy = cb.rest.DynamicProxy.create({
            syncAssets: {
                url: '/api/asset/sync?domainKey=' + domainKey,
                method: 'POST'
            }
        });

        proxy.syncAssets({ pk_org: pk_org }, function (err, result) {
            cb.utils.loadingControl.end({ diworkCode: 'sync-assets' });
            if (err) {
                cb.utils.alert('同步失败: ' + err.message, 'error');
                return;
            }
            var count = result.count || 0;
            cb.utils.alert('成功同步 ' + count + ' 条资产数据', 'success');
            viewModel.execute('refresh');
        });
    });
});
```

---

## 示例 5：完整盘点单（中等复杂度）

包含特性启用、分页、表格操作、before/after 对比、批改等完整功能。

```javascript
viewModel.on('customInit', function () {
    viewModel.enableFeature('lazyLoadByPage');
    viewModel.enableFeature('asyncSave');
    viewModel.enableFeature('filteringCrossPage');
});

viewModel.on('afterLoadData', function () {
    var grid = viewModel.getGridModel('bodyvos');
    if (!grid) return;

    // 设置分页
    grid.setPageSize(1000);
    grid.setPageInfo({
        isPagination: true,
        pageSize: 1000,
        pageCount: 1,
        pageNo: 1,
        itemCount: 0
    });

    // 获取所有 after 字段并设置为可编辑
    var columns = grid.getColumns();
    var afterKeys = columns.filter(function (col) {
        return col.key && col.key.endsWith('_after');
    }).map(function (col) { return col.key; });

    afterKeys.forEach(function (key) {
        grid.setColumnState(key, 'bCanModify', true);
    });
});

// 单元格值变化联动
viewModel.getGridModel('bodyvos').on('afterCellValueChange', function (data) {
    var grid = viewModel.getGridModel('bodyvos');
    var rowIndex = data.rowIndex;

    if (data.cellName === 'inventory_flag') {
        var isFound = normalizeIfBoolean(data.value);

        if (isFound === true) {
            grid.setCellValue(rowIndex, 'inventory_verfiresult', '1');
            grid.setCellValue(rowIndex, 'inventory_result', '1');
        } else {
            grid.setCellValue(rowIndex, 'inventory_verfiresult', '');
            grid.setCellValue(rowIndex, 'inventory_result', '2');
        }
        return;
    }

    // after 字段变化时对比 before
    if (data.cellName.endsWith('_after')) {
        var row = grid.getRow(rowIndex);
        var beforeKey = data.cellName.replace('_after', '_before');
        var beforeVal = row[beforeKey];
        var afterVal = data.value;

        // 计算差异
        var diffs = [];
        var allBeforeKeys = Object.keys(row).filter(function (k) {
            return k.endsWith('_before');
        });
        allBeforeKeys.forEach(function (bk) {
            var ak = bk.replace('_before', '_after');
            if (row[bk] !== row[ak]) {
                diffs.push(bk.replace('_before', ''));
            }
        });
        grid.setCellValue(rowIndex, 'DiffDetails', diffs.join(', '));

        // 计算盘点结果
        var allMatch = true;
        allBeforeKeys.forEach(function (bk) {
            var ak = bk.replace('_before', '_after');
            if (row[bk] !== row[ak]) { allMatch = false; }
        });

        if (allMatch) {
            grid.setCellValue(rowIndex, 'inventory_verfiresult', '1');
            grid.setCellValue(rowIndex, 'inventory_result', '1');
        } else {
            grid.setCellValue(rowIndex, 'inventory_verfiresult', '3');
            grid.setCellValue(rowIndex, 'inventory_result', '3');
        }
    }
});

// 批改字段过滤
viewModel.on('batchModifySetFields', function (data) {
    var allowed = [
        'pk_asset__name', 'equip_code', 'inventory_flag',
        'inventory_verfiresult', 'inventory_result'
    ];
    data.setFields = data.setFields.filter(function (f) {
        return allowed.indexOf(f.key) !== -1;
    });
});

// 保存前校验
viewModel.on('beforeValidate', function () {
    var grid = viewModel.getGridModel('bodyvos');
    if (!grid) return true;
    var rows = grid.getRows();

    for (var i = 0; i < rows.length; i++) {
        if (!rows[i].equip_code) {
            cb.utils.alert('第 ' + (i + 1) + ' 行缺少装备编码', 'error');
            return false;
        }
    }
    return true;
});

// 工具函数
function normalizeIfBoolean(value) {
    if (typeof value === 'boolean') return value;
    if (value === 'true' || value === '1') return true;
    if (value === 'false' || value === '0' || value === '') return false;
    return value;
}
```

---

## 示例 6：完整新线资产接收单（主单）

复杂脚本，包含特性启用、分页、beforePush 校验、反馈 API、自定义 CSS 等。

```javascript
viewModel.on('customInit', function () {
    // 启用特性
    viewModel.enableFeature('lazyLoadByPage');
    viewModel.enableFeature('asyncSave');
    viewModel.enableFeature('filteringCrossPage');

    // 注册环境（推单行为控制）
    var domainKey = viewModel.getDomainKey();
    cb.extend.registerEnv(domainKey, {
        pullVoucherCarryDetail: true,
        createCodeCarryDetail: true
    });

    // 自定义 CSS（必填字段表头标红）
    var cusStyle =
        '.meta-table .public_fixedDataTableCell_wrap3 .fixedDataTableRowLayout_rowWrapper > div:nth-child(13) > div > span,' +
        '.meta-table .public_fixedDataTableLayout_fixedDataTableDivider > div:nth-child(13) > span {' +
        '    color: rgb(223, 17, 34) !important;' +
        '}';
    var style = document.createElement('style');
    style.sheet && style.sheet.insertRule(cusStyle, 0);
    document.head.appendChild(style);

    // 初始化分页
    var grid = viewModel.getGridModel('bodyvos');
    if (grid) {
        grid.setPageSize(1000);
    }
});

viewModel.on('afterLoadData', function () {
    // 根据事务类型控制按钮
    var transType = viewModel.get('transType').getValue();
    if (transType === '4A35-01-02') {
        viewModel.get('button31if') && viewModel.get('button31if').setVisible(false);
    }
});

// 单元格值变化联动
viewModel.getGridModel('bodyvos').on('afterCellValueChange', function (data) {
    var grid = viewModel.getGridModel('bodyvos');
    if (!grid) return;

    if (data.cellName === 'is_confirmed') {
        var rowIndex = data.rowIndex;
        var confirmed = data.value;

        grid.setCellValue(rowIndex, 'confirm_time', getDate());
        grid.setCellState(rowIndex, 'confirm_remark', 'disabled', !confirmed);
    }
});

// beforePush 校验
viewModel.on('beforePush', function () {
    var grid = viewModel.getGridModel('bodyvos');
    if (!grid) return true;
    var rows = grid.getRows();

    for (var i = 0; i < rows.length; i++) {
        if (!rows[i].pk_maintenance_unit || !rows[i].pk_maintenance_unit_name) {
            cb.utils.alert('第 ' + (i + 1) + ' 行缺少维保单位', 'error');
            return false;
        }
        if (!rows[i].pk_profession || !rows[i].pk_profession_name) {
            cb.utils.alert('第 ' + (i + 1) + ' 行缺少专业', 'error');
            return false;
        }
    }
    return true;
});

// 反馈按钮
viewModel.get('btnFeedback') && viewModel.get('btnFeedback').on('click', function () {
    var grid = viewModel.getGridModel('bodyvos');
    if (!grid) return;

    cb.utils.confirm('确定要反馈到京投系统？', function () {
        cb.utils.loadingControl.start({ diworkCode: 'feedback-jt' });

        var domainKey = viewModel.getDomainKey();
        var proxy = cb.rest.DynamicProxy.create({
            mainToJtFeedbackReturn: {
                url: '/api/asset/mainToJtFeedbackReturn?domainKey=' + domainKey,
                method: 'POST'
            }
        });

        proxy.mainToJtFeedbackReturn({}, function (err, result) {
            cb.utils.loadingControl.end({ diworkCode: 'feedback-jt' });
            if (err) {
                cb.utils.alert('反馈失败: ' + err.message, 'error');
                return;
            }
            cb.utils.alert('反馈到京投系统成功', 'success');
            viewModel.execute('refresh');
        });
    });
});

// 批改字段过滤
viewModel.on('batchModifySetFields', function (data) {
    data.setFields = data.setFields.filter(function (field) {
        return field.key === 'pk_maintenance_unit__name'
            || field.key === 'pk_profession__name'
            || field.key === 'is_confirmed';
    });
});

// 获取北京时间日期
function getDate() {
    var date = new Date();
    var utc8Date = new Date(date.getTime() + 8 * 60 * 60 * 1000);
    return utc8Date.toISOString().split('T')[0];
}
```

---

## 示例 7：列表页任务分配

列表页脚本，添加自定义按钮并处理批量操作。

```javascript
viewModel.on('customInit', function () {
    // 列表页初始化
});

// 批量分配按钮
viewModel.get('btnAssign') && viewModel.get('btnAssign').on('click', function () {
    var grid = viewModel.getGridModel();
    var indexes = grid.getSelectedRowIndexes();

    if (!indexes || indexes.length === 0) {
        cb.utils.alert('请先选择要分配的任务', 'warning');
        return;
    }

    cb.utils.confirm('确定将选中的 ' + indexes.length + ' 个任务分配给当前用户？', function () {
        var domainKey = viewModel.getDomainKey();
        var proxy = cb.rest.DynamicProxy.create({
            assignTask: {
                url: '/api/task/assign?domainKey=' + domainKey,
                method: 'POST'
            }
        });

        proxy.assignTask({ ids: indexes }, function (err, result) {
            if (err) {
                cb.utils.alert(err.message, 'error');
                return;
            }
            cb.utils.alert('分配成功', 'success');
            viewModel.execute('refresh');
        });
    });
});

// 批量发布按钮
viewModel.get('btnPublish') && viewModel.get('btnPublish').on('click', function () {
    var grid = viewModel.getGridModel();
    var indexes = grid.getSelectedRowIndexes();

    if (!indexes || indexes.length === 0) {
        cb.utils.alert('请先选择要发布的盘点计划', 'warning');
        return;
    }

    cb.utils.confirm('确定发布选中的盘点计划？', function () {
        var domainKey = viewModel.getDomainKey();
        var proxy = cb.rest.DynamicProxy.create({
            publishPlan: {
                url: '/api/plan/publish?domainKey=' + domainKey,
                method: 'POST'
            }
        });

        proxy.publishPlan({ ids: indexes }, function (err, result) {
            if (err) {
                cb.utils.alert(err.message, 'error');
                return;
            }
            cb.utils.alert('发布成功', 'success');
            viewModel.execute('refresh');
        });
    });
});
```

---

## 示例 8：清册单（多 Tab + 多孙表）

复杂清册单脚本，包含多 tab 数据联动、实物编码查询、保存前校验。

```javascript
viewModel.on('customInit', function () {
    // 启用特性
    viewModel.enableFeature('asyncSave');

    // 初始化时清空数据
    viewModel.clear();

    // Excel 模板下载按钮
    viewModel.get('btnDownloadTemplate') && viewModel.get('btnDownloadTemplate').on('click', function () {
        downloadTemplate('asset_template', '资产清册模板.xlsx');
    });
});

// 项目选择联动
viewModel.get('pk_project').on('afterValueChange', function (data) {
    var projectId = data.value;
    if (!projectId) return;

    var domainKey = viewModel.getDomainKey();
    var proxy = cb.rest.DynamicProxy.create({
        queryProjectDetail: {
            url: '/api/project/detail?domainKey=' + domainKey + '&pk_project=' + projectId,
            method: 'GET'
        }
    });

    proxy.queryProjectDetail({}, function (err, result) {
        if (err) { cb.utils.alert(err.message, 'error'); return; }
        if (result) {
            // 填充表头
            viewModel.get('pk_org').setValue(result.pk_org);
            viewModel.get('project_name').setValue(result.name);

            // 填充三个孙表
            fillSubTable('addList', result.addItems || []);
            fillSubTable('updateList', result.updateItems || []);
            fillSubTable('demoliteList', result.demoliteItems || []);
        }
    });
});

// 实物编码选择联动 - 新增资产 tab
viewModel.getGridModel('addList').on('afterCellValueChange', function (data) {
    if (data.cellName === 'equip_code') {
        var grid = viewModel.getGridModel('addList');
        var rowIndex = data.rowIndex;
        var equipCode = data.value;

        queryAssetCardByEquipCode(equipCode, function (card) {
            if (card) {
                grid.updateRow(rowIndex, {
                    pk_asset: card.pk_asset,
                    pk_asset_name: card.name,
                    equip_model: card.model,
                    use_date: card.use_date,
                    original_value: card.original_value
                });
            }
        });
    }
});

// 保存前校验 - 父资产关系
viewModel.on('beforeValidate', function () {
    var errorMsgs = [];
    var addRows = viewModel.getGridModel('addList') ? viewModel.getGridModel('addList').getRows() : [];
    var updateRows = viewModel.getGridModel('updateList') ? viewModel.getGridModel('updateList').getRows() : [];

    var checkRows = function (rows, tabName) {
        for (var i = 0; i < rows.length; i++) {
            var row = rows[i];
            if (!row.pk_asset) {
                errorMsgs.push(tabName + ' 第 ' + (i + 1) + ' 行缺少资产');
            }
            if (row.important_composition_list) {
                var parts = row.important_composition_list;
                for (var j = 0; j < parts.length; j++) {
                    if (!parts[j].pk_asset) {
                        errorMsgs.push(tabName + ' 第 ' + (i + 1) + ' 行重要组成缺少资产');
                    }
                }
            }
        }
    };

    checkRows(addRows, '新增资产');
    checkRows(updateRows, '更新改造');

    if (errorMsgs.length > 0) {
        cb.utils.alert(errorMsgs.join('\n'), 'error');
        return false;
    }
    return true;
});

// 批改字段过滤
viewModel.on('batchModifySetFields', function (data) {
    data.setFields = data.setFields.filter(function (field) {
        return field.key === 'pk_asset__name'
            || field.key === 'equip_code'
            || field.key === 'userDefines__T0002';
    });
});

// 辅助函数
function fillSubTable(gridName, items) {
    var grid = viewModel.getGridModel(gridName);
    if (!grid) return;
    grid.clear();
    items.forEach(function (item) {
        grid.appendRow(item);
    });
}

function queryAssetCardByEquipCode(equipCode, callback) {
    var domainKey = viewModel.getDomainKey();
    var proxy = cb.rest.DynamicProxy.create({
        queryCard: {
            url: '/api/asset/cardByEquip?domainKey=' + domainKey,
            method: 'GET'
        }
    });
    proxy.queryCard({ equip_code: equipCode }, function (err, result) {
        if (err || !result) { callback(null); return; }
        callback(result);
    });
}

function downloadTemplate(templateId, fileName) {
    var url = '/api/template/download/' + templateId;
    fetch(url)
        .then(function (res) { return res.blob(); })
        .then(function (blob) {
            var link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = fileName;
            link.click();
            URL.revokeObjectURL(link.href);
        })
        .catch(function (err) {
            cb.utils.alert('下载失败: ' + err.message, 'error');
        });
}