# 常见模式

本文档是 `mdf-script-development` skill 的支持文件，提供 MDF 前端脚本的常见开发模式。

## 表格单元格值变更联动

最常用模式：当某个单元格值改变时，联动更新同其他单元格或触发 API 调用。

```javascript
viewModel.getGridModel('bodyvos').on('afterCellValueChange', (data) => {
    const grid = viewModel.getGridModel('bodyvos');
    const rowIndex = data.rowIndex;
    const cellName = data.cellName;

    if (cellName === 'is_confirmed') {
        const confirmed = data.value;
        // 联动设置同其他单元格
        grid.setCellValue(rowIndex, 'confirm_time', new Date().toISOString());
        grid.setCellState(rowIndex, 'confirm_remark', 'disabled', !confirmed);
    }

    if (cellName === 'equip_code') {
        // 装备编码变化后查询并填充装备信息
        const equipCode = data.value;
        queryEquipInfo(equipCode, (equip) => {
            if (equip) {
                grid.updateRow(rowIndex, {
                    equip_name: equip.name,
                    equip_model: equip.model,
                    pk_asset: equip.pk_asset
                });
            }
        });
    }
});
```

### 批量单元格状态设置

```javascript
function batchSetCellState(gridModel, rowIndex, keys, stateKey, value) {
    keys.forEach((key) => {
        gridModel.setCellState(rowIndex, key, stateKey, value);
    });
}

// 使用
batchSetCellState(grid, rowIndex,
    ['pk_asset__name', 'equip_code', 'equip_model'],
    'disabled', true
);
```

## 字段值变更联动

```javascript
viewModel.get('pk_org').on('afterValueChange', (data) => {
    // 组织变化后联动更新下属单位
    const orgId = data.value;
    if (orgId) {
        // 触发查询并填充
        querySubUnits(orgId, (units) => {
            viewModel.get('pk_unit').setValue(units[0].id);
        });
    }
});

// 阻止值变更
viewModel.get('orgId_name').on('beforeValueChange', () => {
    // 编辑模式下禁止修改组织
    if (viewModel.mode === 'edit') {
        return false;
    }
});
```

## 按钮点击处理

```javascript
// 标准模式：守卫 + 点击处理
viewModel.get('button31if') && viewModel.get('button31if').on('click', () => {
    // 1. 获取当前数据
    const data = viewModel.getAllData();

    // 2. 前置校验
    if (!data.header || !data.header.pk_org) {
        cb.utils.alert('请先选择组织', 'error');
        return;
    }

    // 3. 显示确认
    cb.utils.confirm('确定要执行此操作吗？', () => {
        // 4. 显示 loading
        cb.utils.loadingControl.start({ diworkCode: 'my-operation' });

        // 5. 发起 API 调用
        const domainKey = viewModel.getDomainKey();
        const proxy = cb.rest.DynamicProxy.create({
            myAction: {
                url: '/api/asset/myAction?domainKey=' + domainKey,
                method: 'POST'
            }
        });

        proxy.myAction({ pk_org: data.header.pk_org }, (err, result) => {
            cb.utils.loadingControl.end({ diworkCode: 'my-operation' });
            if (err) {
                cb.utils.alert(err.message, 'error');
                return;
            }
            cb.utils.alert('操作成功', 'success');
            viewModel.execute('refresh');
        });
    });
});
```

### 按钮点击打开新单据

```javascript
viewModel.get('btnViewDetail') && viewModel.get('btnViewDetail').on('click', () => {
    window.jDiwork.openService(
        'serviceId',
        { billtype: 'asset_card', billno: '资产卡片' },
        { data: { mode: 'browse', readOnly: true, id: billId } }
    );
});
```

## 代理调用模式

### 标准回调模式

```javascript
const domainKey = viewModel.getDomainKey();
const proxy = cb.rest.DynamicProxy.create({
    queryData: {
        url: '/api/asset/query?domainKey=' + domainKey,
        method: 'POST'
    },
    saveData: {
        url: '/api/asset/save?domainKey=' + domainKey,
        method: 'PUT'
    }
});

proxy.queryData(params, (err, result) => {
    if (err) {
        cb.utils.alert(err.message, 'error');
        return;
    }
    if (result) {
        // 处理结果
    }
});
```

### 同步函数调用

```javascript
// 同步调用远程函数（阻塞 UI）
const result = cb.rest.invokeFunction(
    'functionName',
    { param1: 'value1' },
    null, null,
    { async: false }
);
```

### 带 viewModel 的函数调用

```javascript
cb.rest.invokeFunction(
    'functionName',
    { param1: 'value1' },
    (err, result) => {
        if (err) { cb.utils.alert(err.message, 'error'); return; }
        // 处理结果
    },
    viewModel,
    { async: true }
);
```

## 参照浏览过滤

### 字段参照过滤

```javascript
viewModel.get('pk_asset').on('beforeBrowse', (arg) => {
    const condition = {
        isExtend: true,
        simpleVOs: [
            { field: 'pk_org', op: 'eq', value1: orgId },
            { field: 'status', op: 'eq', value1: 'ACTIVE' }
        ]
    };
    arg.context.setFilter(condition);
});
```

### 表格参照过滤

```javascript
viewModel.getGridModel('bodyvos').on('beforeBrowse', (arg) => {
    if (arg.cellName === 'pk_asset') {
        const rowIndex = arg.rowIndex;
        const orgId = viewModel.get('pk_org').getValue();
        const condition = {
            isExtend: true,
            simpleVOs: [{ field: 'pk_org', op: 'eq', value1: orgId }]
        };
        arg.context.setFilter(condition);
    }
});
```

### 树形参照过滤

```javascript
field.on('beforeBrowse', (arg) => {
    const condition = {
        isExtend: true,
        simpleVOs: [{ field: 'pk_group', op: 'eq', value1: groupId }]
    };
    arg.context.setTreeFilter(condition);  // 注意是 setTreeFilter
});
```

## 表格行操作

### 新增行并设置初始值

```javascript
viewModel.get('btnAddRow') && viewModel.get('btnAddRow').on('click', () => {
    const grid = viewModel.getGridModel('bodyvos');
    if (!grid) return;

    const newRow = {
        row_id: generateId(),
        pk_org: viewModel.get('pk_org').getValue(),
        pk_org_name: viewModel.get('pk_org_name').getValue(),
        equip_code: '',
        inventory_flag: false,
        inventory_verfiresult: ''
    };
    grid.appendRow(newRow);
});
```

### 批量更新行

```javascript
const grid = viewModel.getGridModel('bodyvos');
const indexes = grid.getSelectedRowIndexes();
if (!indexes || indexes.length === 0) {
    cb.utils.alert('请先选择要操作的行', 'warning');
    return;
}

const rows = indexes.map((idx) => {
    return { inventory_flag: true };
});
grid.updateRows(indexes, rows);
```

### 删除选中行

```javascript
viewModel.get('btnDelete') && viewModel.get('btnDelete').on('click', () => {
    const grid = viewModel.getGridModel('bodyvos');
    const indexes = grid.getSelectedRowIndexes();
    if (!indexes || indexes.length === 0) {
        cb.utils.alert('请先选择要删除的行', 'warning');
        return;
    }

    cb.utils.confirm('确定删除选中的 ' + indexes.length + ' 行？', () => {
        // 注意：MDF 没有直接删除行的 API
        // 通常通过标记删除状态或在保存前过滤实现
        grid.clear(); // 清空后重建
    });
});
```

## 数据校验模式

### 保存前校验

```javascript
viewModel.on('beforeValidate', () => {
    const data = viewModel.getAllData();
    const bodyvos = data.bodyvos || [];
    const errorMsgs = [];

    for (let i = 0; i < bodyvos.length; i++) {
        const row = bodyvos[i];
        const rowNum = i + 1;

        if (!row.pk_asset) {
            errorMsgs.push('第 ' + rowNum + ' 行缺少资产');
        }
        if (row.amount && isNaN(Number(row.amount))) {
            errorMsgs.push('第 ' + rowNum + ' 行金额格式不正确');
        }
    }

    if (errorMsgs.length > 0) {
        cb.utils.alert(errorMsgs.join('\n'), 'error');
        return false;
    }
    return true;
});
```

### 父资产关系校验

```javascript
function checkAllCriticalParts(bodyvos) {
    const errorMsgs = [];
    for (let i = 0; i < bodyvos.length; i++) {
        const row = bodyvos[i];
        if (row.important_composition_list && row.important_composition_list.length > 0) {
            const parts = row.important_composition_list;
            for (let j = 0; j < parts.length; j++) {
                if (!parts[j].pk_asset || !parts[j].pk_asset_name) {
                    errorMsgs.push('第 ' + (i + 1) + ' 行重要组成缺少资产编码');
                }
            }
        }
    }
    return errorMsgs;
}

viewModel.on('beforeValidate', () => {
    const data = viewModel.getAllData();
    const errorMsgs = checkAllCriticalParts(data.bodyvos || []);
    if (errorMsgs.length > 0) {
        cb.utils.alert(errorMsgs.join('\n'), 'error');
        return false;
    }
    return true;
});
```

## 加载控制

```javascript
// 开始 loading
cb.utils.loadingControl.start({ diworkCode: 'my-operation' });

// 发起异步操作
proxy.myAction(params, (err, result) => {
    // 结束 loading（确保在回调中执行，无论成功或失败）
    cb.utils.loadingControl.end({ diworkCode: 'my-operation' });

    if (err) {
        cb.utils.alert(err.message, 'error');
        return;
    }
    cb.utils.alert('操作成功', 'success');
    viewModel.execute('refresh');
});
```

## 确认对话框

```javascript
cb.utils.confirm(
    '确定要执行此操作吗？',  // 消息
    () => {            // 确认回调
        // 执行操作
    },
    () => {            // 取消回调（可选）
        // 取消操作
    },
    '确认标题',              // 标题（可选）
    '确定'                   // 确认按钮文本（可选）
);
```

## 自定义 CSS 注入

常用于必填字段表头标红等场景：

```javascript
viewModel.on('customInit', () => {
    const cusStyle =
        '.meta-table .public_fixedDataTableCell_wrap3 .fixedDataTableRowLayout_rowWrapper > div:nth-child(13) > div > span,' +
        '.meta-table .public_fixedDataTableLayout_fixedDataTableDivider > div:nth-child(13) > span {' +
        '    color: rgb(223, 17, 34) !important;' +
        '}';
    const style = document.createElement('style');
    style.sheet && style.sheet.insertRule(cusStyle, 0);
    document.head.appendChild(style);
});
```

## 特性启用

```javascript
viewModel.on('customInit', () => {
    // 分页懒加载
    viewModel.enableFeature('lazyLoadByPage');
    // 异步保存
    viewModel.enableFeature('asyncSave');
    // 跨页过滤
    viewModel.enableFeature('filteringCrossPage');
});
```

## 环境注册（推单行为控制）

```javascript
viewModel.on('customInit', () => {
    const domainKey = viewModel.getDomainKey();
    cb.extend.registerEnv(domainKey, {
        pullVoucherCarryDetail: true,   // 拉单携带明细
        createCodeCarryDetail: true     // 生单携带编码明细
    });
});
```

## Excel 下载

```javascript
function downloadTemplate(templateId, fileName) {
    const url = '/api/template/download/' + templateId;
    fetch(url)
        .then((res) => res.blob())
        .then((blob) => {
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = fileName;
            link.click();
            URL.revokeObjectURL(link.href);
        })
        .catch((err) => {
            cb.utils.alert('下载失败: ' + err.message, 'error');
        });
}
```

## 批改弹窗字段过滤

```javascript
viewModel.on('batchModifySetFields', (data) => {
    // 只允许批改指定字段
    const allowedFields = [
        'pk_asset__name', 'equip_code', 'inventory_flag',
        'inventory_verfiresult', 'inventory_result'
    ];
    data.setFields = data.setFields.filter((field) => {
        return allowedFields.indexOf(field.key) !== -1;
    });
});
```

## 分页设置

```javascript
viewModel.on('afterLoadData', () => {
    const grid = viewModel.getGridModel('bodyvos');
    if (grid) {
        grid.setPageSize(1000);
        grid.setPageInfo({
            isPagination: true,
            pageSize: 1000,
            pageCount: 1,
            pageNo: 1,
            itemCount: 0
        });
    }
});
```

## 跨 ViewModel 通信

```javascript
// 发送方
viewModel.communication({
    type: 'return',
    payload: { result: 'success', data: someData }
});

// 在 openService 打开的页面中，通过 communication 返回数据给父页面