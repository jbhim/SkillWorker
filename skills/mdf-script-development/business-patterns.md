# 业务场景模式

本文档是 `mdf-script-development` skill 的支持文件，描述常见业务场景的开发模式。

## 盘点业务流

### 业务流程

```
盘点计划 → 生单 → 盘点单(父单) → 自动分单 → 盘点单(子单)
    → 发布任务 → 编辑态盘点 → 对比_before/_after → 计算盘点结果
    → 盘盈(0)/盘亏(2)/相符(1)/不符(3) → 保存/提交 → 审批
```

### 核心数据模型

盘点单使用 `_before` / `_after` 字段对记录盘点前后的资产状态：

| 字段 | 说明 |
|------|------|
| `xxx_before` | 盘点前的原始值 |
| `xxx_after` | 盘点后的实际值 |
| `inventory_flag` | 是否盘到（布尔） |
| `inventory_verfiresult` | 盘点核实结果 |
| `inventory_result` | 盘点结果编码（0=盘盈, 1=相符, 2=盘亏, 3=不符） |
| `DiffDetails` | 差异明细（自动填充变更字段名） |

### 盘点单核心模式

#### 1. 盘到标识联动

```javascript
viewModel.getGridModel('bodyvos').on('afterCellValueChange', function (data) {
    var grid = viewModel.getGridModel('bodyvos');
    var rowIndex = data.rowIndex;

    if (data.cellName === 'inventory_flag') {
        var isFound = data.value;  // true = 盘到, false = 未盘到

        if (isFound) {
            // 盘到：设置核实结果为"相符"
            grid.setCellValue(rowIndex, 'inventory_verfiresult', '1');
            grid.setCellValue(rowIndex, 'inventory_result', '1');
        } else {
            // 未盘到：核实结果和盘点结果清空
            grid.setCellValue(rowIndex, 'inventory_verfiresult', '');
            grid.setCellValue(rowIndex, 'inventory_result', '2');
        }
    }

    // _after 字段变更时计算差异
    if (data.cellName.endsWith('_after')) {
        var row = grid.getRow(rowIndex);
        var beforeKey = data.cellName.replace('_after', '_before');
        var beforeVal = row[beforeKey];
        var afterVal = data.value;

        if (beforeVal !== afterVal) {
            // 值变化了，记录差异
            updateDiffDetails(grid, rowIndex, row);
        }

        // 重新计算盘点结果
        recalcInventoryResult(grid, rowIndex, row);
    }
});
```

#### 2. Before/After 对比工具函数

```javascript
// 检查 before/after 是否完全匹配
function isBeforeAfterAllMatch(row) {
    var beforeKeys = Object.keys(row).filter(function (k) { return k.endsWith('_before'); });
    for (var i = 0; i < beforeKeys.length; i++) {
        var afterKey = beforeKeys[i].replace('_before', '_after');
        if (row[beforeKeys[i]] !== row[afterKey]) {
            return false;
        }
    }
    return true;
}

// 获取差异字段列表
function getBeforeAfterNotMatch(row) {
    var diffs = [];
    var beforeKeys = Object.keys(row).filter(function (k) { return k.endsWith('_before'); });
    for (var i = 0; i < beforeKeys.length; i++) {
        var afterKey = beforeKeys[i].replace('_before', '_after');
        if (row[beforeKeys[i]] !== row[afterKey]) {
            diffs.push(beforeKeys[i].replace('_before', ''));
        }
    }
    return diffs;
}

// 清空 After 字段
function clearTargetAfterProps(row) {
    var afterKeys = Object.keys(row).filter(function (k) { return k.endsWith('_after'); });
    for (var i = 0; i < afterKeys.length; i++) {
        row[afterKeys[i]] = null;
    }
}

// 复制 Before 到 After
function copyBeforeToAfter(row) {
    var beforeKeys = Object.keys(row).filter(function (k) { return k.endsWith('_before'); });
    for (var i = 0; i < beforeKeys.length; i++) {
        var afterKey = beforeKeys[i].replace('_before', '_after');
        row[afterKey] = row[beforeKeys[i]];
    }
}
```

#### 3. Excel 导入处理（移动端）

```javascript
viewModel.on('beforeImportRender', function (data) {
    var rows = data.rows || [];
    var grid = viewModel.getGridModel('bodyvos');
    var existingRows = grid ? grid.getAllData() : [];

    var updateOperations = [];
    var insertOperations = [];

    for (var i = 0; i < rows.length; i++) {
        var importRow = rows[i];
        var equipCode = importRow.equip_code;

        // 查找是否已存在
        var existingIdx = -1;
        for (var j = 0; j < existingRows.length; j++) {
            if (existingRows[j].equip_code === equipCode) {
                existingIdx = j;
                break;
            }
        }

        if (existingIdx >= 0) {
            // 更新操作
            var merged = Object.assign({}, existingRows[existingIdx]);
            // 处理 inventory_flag
            merged.inventory_flag = (importRow.inventory_flag === '是');
            // 复制 before 到 after（如果需要）
            copyBeforeToAfter(merged);
            updateOperations.push({ index: existingIdx, row: merged });
        } else {
            // 新增操作
            var newRow = buildNewRowFromImport(importRow);
            insertOperations.push(newRow);
        }
    }

    // 批量更新
    if (updateOperations.length > 0) {
        var indexes = updateOperations.map(function (op) { return op.index; });
        var rowObjs = updateOperations.map(function (op) { return op.row; });
        grid.updateRows(indexes, rowObjs);
    }

    // 批量插入
    if (insertOperations.length > 0) {
        grid.insertRows(existingRows.length, insertOperations);
    }

    return false;  // 阻止默认导入，我们自己处理了
});
```

## 新线资产业务流

### 业务流程

```
接收单(主单) → 反馈 to 京投(外部系统)
     ↓ 分单
接收单(子单) → 反馈 to 主单
     ↓ 分单
接收单(孙单) → 反馈 to 子单

核验单(主单) → 反馈 to 京投, 生成卡片
     ↓ 分单
核验单(子单) → 反馈 to 主单
     ↓ 分单
核验单(孙单) → 反馈 to 子单
```

### 三级单据差异

| 维度 | 主单 | 子单 | 孙单 |
|------|------|------|------|
| 特性 | lazyLoadByPage, asyncSave, filteringCrossPage | lazyLoadByPage, asyncSave | 无 |
| asyncSaveSubTabNum | 50 | 500 | N/A |
| beforePush 校验 | 维保单位 + 专业 | 维保部门 + 监管部门 | 无 |
| 反馈 API | mainToJtFeedbackReturn | sonToMainFeedbackReturn | grandSonToSonFeedbackReturn |
| 组织锁定 | 无 | beforeValueChange 锁定 orgId_name | 同子单 |
| modeChange | 无 | 无 | 编辑态设置必填 |

### 主单脚本模板

```javascript
viewModel.on('customInit', function () {
    viewModel.enableFeature('lazyLoadByPage');
    viewModel.enableFeature('asyncSave');
    viewModel.enableFeature('filteringCrossPage');
});

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
```

### 子单/孙单组织锁定

```javascript
viewModel.get('orgId_name').on('beforeValueChange', function () {
    // 编辑模式下锁定组织，禁止修改
    return false;
});
```

### 供应商自动创建

```javascript
function querySuppliers(names) {
    if (!names || names.length === 0) return;

    var domainKey = viewModel.getDomainKey();
    var proxy = cb.rest.DynamicProxy.create({
        querySuppliers: {
            url: '/api/supplier/batchCreate?domainKey=' + domainKey,
            method: 'POST'
        }
    });

    proxy.querySuppliers({ supplierNames: names }, function (err, result) {
        if (err) {
            cb.utils.alert('供应商创建失败: ' + err.message, 'warning');
            return;
        }
        // 供应商创建成功，可以关联引用
    });
}
```

## 清册验收业务流

### 业务流程

```
清册单（3个tab: 新增/更新改造/拆除）
    → 选择项目 → 自动填充表头 + 三个孙表数据
    → 实物资产编码选择 → 联动查询卡片信息 → 填充行数据
    → 保存前校验父资产关系
    → 验收单 → 同步企管平台
```

### 清册单核心模式

#### 项目选择联动

```javascript
viewModel.get('pk_project').on('afterValueChange', function (data) {
    var projectId = data.value;
    if (!projectId) return;

    // 查询项目信息并填充表头
    var domainKey = viewModel.getDomainKey();
    var proxy = cb.rest.DynamicProxy.create({
        queryProject: {
            url: '/api/project/query?domainKey=' + domainKey,
            method: 'GET'
        }
    });

    proxy.queryProject({ pk_project: projectId }, function (err, result) {
        if (err) { cb.utils.alert(err.message, 'error'); return; }
        if (result) {
            // 填充表头
            viewModel.get('pk_org').setValue(result.pk_org);
            viewModel.get('project_name').setValue(result.name);

            // 填充三个孙表（新增/更新改造/拆除）
            fillSubTable('addList', result.addItems);
            fillSubTable('updateList', result.updateItems);
            fillSubTable('demoliteList', result.demoliteItems);
        }
    });
});

function fillSubTable(gridName, items) {
    var grid = viewModel.getGridModel(gridName);
    if (!grid || !items || items.length === 0) return;
    grid.clear();
    items.forEach(function (item) {
        grid.appendRow(item);
    });
}
```

#### 实物编码选择联动

```javascript
viewModel.getGridModel('bodyvos').on('beforeBrowse', function (arg) {
    if (arg.cellName === 'equip_code') {
        var orgId = viewModel.get('pk_org').getValue();
        arg.context.setFilter({
            isExtend: true,
            simpleVOs: [{ field: 'pk_org', op: 'eq', value1: orgId }]
        });
    }
});

viewModel.getGridModel('bodyvos').on('afterCellValueChange', function (data) {
    if (data.cellName === 'equip_code') {
        var grid = viewModel.getGridModel('bodyvos');
        var rowIndex = data.rowIndex;
        var equipCode = data.value;

        // 查询卡片信息
        queryAssetCard(equipCode, function (card) {
            if (card) {
                grid.updateRow(rowIndex, {
                    pk_asset: card.pk_asset,
                    pk_asset_name: card.name,
                    equip_model: card.model,
                    use_date: card.use_date
                });
            }
        });
    }
});
```

## 资产变动单

### 变动类型与字段联动

资产变动单支持多种变动类型，每种类型需要展示不同的字段组合：

```javascript
viewModel.get('transType').on('afterValueChange', function (data) {
    var transType = data.value;
    // 根据变动类型显示/隐藏字段
    toggleFieldsByTransType(transType);
});

function toggleFieldsByTransType(transType) {
    var fieldGroups = {
        '4A35-01': ['target_dept', 'target_user', 'target_location'],       // 调拨
        '4A35-01-01': ['owned_target_dept'],                                 // 自有调拨
        '4A35-01-02': ['entrusted_target_dept']                              // 受托调拨
    };

    var showFields = fieldGroups[transType] || [];
    var allFields = getAllChangeFields();

    allFields.forEach(function (fieldId) {
        var field = viewModel.get(fieldId);
        if (field) {
            var shouldShow = showFields.indexOf(fieldId) !== -1;
            field.setVisible(shouldShow);
        }
    });
}
```

## 资产拆分单

### 拆分逻辑

```javascript
viewModel.get('btnDivide') && viewModel.get('btnDivide').on('click', function () {
    var grid = viewModel.getGridModel('bodyvos');
    var indexes = grid.getSelectedRowIndexes();

    if (!indexes || indexes.length === 0) {
        cb.utils.alert('请选择要拆分的资产', 'warning');
        return;
    }

    cb.utils.confirm('确定拆分选中的资产？', function () {
        var domainKey = viewModel.getDomainKey();
        var proxy = cb.rest.DynamicProxy.create({
            divideAsset: {
                url: '/api/asset/divide?domainKey=' + domainKey,
                method: 'POST'
            }
        });

        proxy.divideAsset({ ids: indexes }, function (err, result) {
            if (err) { cb.utils.alert(err.message, 'error'); return; }
            cb.utils.alert('拆分成功', 'success');
            viewModel.execute('refresh');
        });
    });
});
```

## 列表页模式

### 任务分配

```javascript
viewModel.on('customInit', function () {
    // 列表页添加自定义按钮
});

viewModel.get('btnAssign') && viewModel.get('btnAssign').on('click', function () {
    var grid = viewModel.getGridModel();
    var selectedRows = grid.getSelectedRowIndexes();

    if (!selectedRows || selectedRows.length === 0) {
        cb.utils.alert('请选择要分配的任务', 'warning');
        return;
    }

    // 调用分配 API
    var domainKey = viewModel.getDomainKey();
    var proxy = cb.rest.DynamicProxy.create({
        assignTask: {
            url: '/api/task/assign?domainKey=' + domainKey,
            method: 'POST'
        }
    });

    proxy.assignTask({ ids: selectedRows }, function (err, result) {
        if (err) { cb.utils.alert(err.message, 'error'); return; }
        cb.utils.alert('分配成功', 'success');
        viewModel.execute('refresh');
    });
});
```

## 事务类型控制

不同事务类型需要不同的按钮和字段行为：

```javascript
viewModel.on('afterLoadData', function () {
    var transType = viewModel.get('transType').getValue();

    // 根据事务类型隐藏按钮
    if (transType === '4A35-01-02') {
        // 受托调拨隐藏某些按钮
        viewModel.get('button31if') && viewModel.get('button31if').setVisible(false);
    }

    // 自有调拨显示额外按钮
    if (transType === '4A35-01-01') {
        viewModel.get('btnOwnedAction') && viewModel.get('btnOwnedAction').setVisible(true);
    }
});
```

## userDefines 自定义字段

通过 `userDefines__xxx` 模式访问自定义字段：

```javascript
// 访问命名自定义字段
viewModel.get('userDefines__plan_spec_after').getValue();
viewModel.get('userDefines__plan_spec_after').setValue(value);

// 访问 T-code 自定义字段
viewModel.get('userDefines__T0002').getValue();
viewModel.get('userDefines__T0003').setValue(value);
```

## 日期计算

```javascript
// 获取北京时间日期
function getDate() {
    var date = new Date();
    var utc8Date = new Date(date.getTime() + 8 * 60 * 60 * 1000);
    return utc8Date.toISOString().split('T')[0];
}

// 计算下次盘点日期
function calculateNextCheckDate(lastCheckDate, checkPeriod, calcMethod) {
    if (!lastCheckDate || !checkPeriod) return '';

    var date = new Date(lastCheckDate);
    if (calcMethod === 'byMonth') {
        date.setMonth(date.getMonth() + checkPeriod);
    } else if (calcMethod === 'byYear') {
        date.setFullYear(date.getFullYear() + checkPeriod);
    }

    var y = date.getFullYear();
    var m = String(date.getMonth() + 1).padStart(2, '0');
    var d = String(date.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + d;
}
```
