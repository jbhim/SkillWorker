# 生命周期与事件

本文档是 `mdf-script-development` skill 的支持文件，描述 MDF 前端脚本的完整生命周期事件顺序和使用规范。

## 详情页（单据页）事件顺序

以下事件按执行顺序排列：

```
1. customInit          → 初始化入口，特性开关、按钮显隐、CSS注入
2. afterLoadData       → 数据加载完成后，按钮配置、表格状态、列配置
3. modeChange          → 模式切换时触发（browse/edit/add）
4. beforeValidate      → 保存前校验，返回 false 阻止保存
5. beforePush          → 推单（生单）前校验，返回 false 阻止推单
6. beforeWorkflow      → 工作流/审批前触发
7. afterWorkflowBeforeQueryAsync → 异步工作流查询
8. afterSubmit         → 提交成功后触发
9. destroyVM           → ViewModel 销毁时清理
```

## 列表页事件顺序

```
1. customInit          → 初始化
2. afterLoadData       → 列表数据加载完成后
3. beforeImportRender  → Excel 导入渲染前（拦截处理导入数据）
4. afterSubmit         → 提交成功后
```

## 各事件详解

### customInit

**触发时机**: 页面初始化，最早可执行的钩子

**用途**:
- 启用平台特性（懒加载、异步保存等）
- 设置按钮初始显隐
- 注入自定义 CSS
- 初始化业务状态变量
- 注册环境配置

**示例**:
```javascript
viewModel.on('customInit', () => {
    // 启用特性
    viewModel.enableFeature('lazyLoadByPage');
    viewModel.enableFeature('asyncSave');
    viewModel.enableFeature('filteringCrossPage');

    // 按钮显隐控制
    const btnSave = viewModel.get('btnSave');
    btnSave && btnSave.setVisible(true);

    // 注入 CSS（必填字段表头标红）
    const style = document.createElement('style');
    const css = '.meta-table .public_fixedDataTableCell_wrap3 { color: rgb(223, 17, 34); }';
    style.sheet && style.sheet.insertRule(css, 0);
    document.head.appendChild(style);
});
```

### afterLoadData

**触发时机**: 单据/列表数据加载完成后

**用途**:
- 根据单据状态控制按钮显隐
- 配置表格列状态（隐藏列、只读列等）
- 设置表体行初始状态
- 根据业务规则动态调整 UI

**示例**:
```javascript
viewModel.on('afterLoadData', () => {
    // 根据单据状态隐藏按钮
    const billStatus = viewModel.get('billStatus').getValue();
    if (billStatus === 'APPROVED') {
        viewModel.get('btnEdit') && viewModel.get('btnEdit').setVisible(false);
    }

    // 设置表格列只读
    const grid = viewModel.getGridModel('bodyvos');
    if (grid) {
        grid.setColumnState('someField', 'disabled', true);
    }

    // 根据事务类型控制
    const transType = viewModel.get('transType').getValue();
    if (transType === '4A35-01-02') {
        viewModel.get('button31if') && viewModel.get('button31if').setVisible(false);
    }
});
```

### modeChange

**触发时机**: 单据模式切换时（浏览/编辑/新增）

**参数**: `data.mode` - 当前模式 `'browse'` | `'edit'` | `'add'`

**示例**:
```javascript
viewModel.on('modeChange', (data) => {
    if (data.mode === 'edit') {
        // 编辑模式下设置某些字段必填
        viewModel.get('someField') && viewModel.get('someField').setState('bCanModify', true);
    }
    if (data.mode === 'browse') {
        // 浏览模式下隐藏操作按钮
        viewModel.get('btnEdit') && viewModel.get('btnEdit').setVisible(false);
    }
});
```

### beforeValidate

**触发时机**: 用户点击保存按钮，框架执行校验前

**返回值**: 返回 `false` 可阻止保存

**示例**:
```javascript
viewModel.on('beforeValidate', () => {
    const data = viewModel.getAllData();
    const bodyvos = data.bodyvos || [];
    const errors = [];

    // 校验逻辑
    for (let i = 0; i < bodyvos.length; i++) {
        const row = bodyvos[i];
        if (!row.pk_asset || !row.pk_asset_name) {
            errors.push('第 ' + (i + 1) + ' 行缺少资产编码');
        }
    }

    if (errors.length > 0) {
        cb.utils.alert(errors.join('\n'), 'error');
        return false;
    }
    return true;
});
```

### beforePush

**触发时机**: 推单（生单/下推）操作前

**返回值**: 返回 `false` 可阻止推单

**示例**:
```javascript
viewModel.on('beforePush', () => {
    const grid = viewModel.getGridModel('bodyvos');
    const rows = grid ? grid.getRows() : [];

    for (let i = 0; i < rows.length; i++) {
        if (!rows[i].pk_maintenance_unit || !rows[i].pk_maintenance_unit_name) {
            cb.utils.alert('第 ' + (i + 1) + ' 行缺少维保单位', 'error');
            return false;
        }
    }
    return true;
});
```

### batchModifySetFields

**触发时机**: 用户打开批改弹窗时

**用途**: 控制批改弹窗中显示哪些字段

**示例**:
```javascript
viewModel.on('batchModifySetFields', (data) => {
    data.setFields = data.setFields.filter((field) => {
        return field.key === 'pk_asset__name'
            || field.key === 'equip_code'
            || field.key === 'inventory_flag';
    });
});
```

### beforeCellValueChange (表格事件)

**触发时机**: 表格单元格值即将变化前

**返回值**: 返回 `false` 可阻止值变更

### afterCellValueChange (表格事件)

**触发时机**: 表格单元格值变化后

**参数**:
- `data.rowIndex` - 行索引
- `data.cellName` - 列名
- `data.value` - 新值
- `data.indexs` - 批量操作时的索引数组

### beforeInsertRow (表格事件)

**触发时机**: 新行即将插入前

**参数**: `args.isCopy` - 是否为复制操作

### afterInsertRow (表格事件)

**触发时机**: 新行插入后

### beforeBrowse (表格/字段事件)

**触发时机**: 参照浏览弹窗打开前

**用途**: 设置参照过滤条件

## 事件注册最佳实践

### 1. 空值守卫

```javascript
// 始终在注册事件前检查对象是否存在
viewModel.get('buttonXX') && viewModel.get('buttonXX').on('click', () => { ... });
viewModel.getGridModel('xxx') && viewModel.getGridModel('xxx').on('afterCellValueChange', () => { ... });
```

### 2. 事件顺序

推荐的脚本结构（按事件执行顺序排列）:

```
1. customInit       → 特性开关、按钮显隐
2. afterLoadData    → 数据驱动的状态配置
3. modeChange       → 模式相关逻辑
4. 字段/表格事件    → beforeValueChange, afterCellValueChange 等
5. beforeValidate   → 保存前校验
6. beforePush       → 推单前校验
7. batchModifySetFields → 批改字段过滤
8. 辅助函数         → 工具方法定义
```

### 3. 避免重复注册

MDF 脚本在每次页面加载时完整执行一次，事件无需手动解绑（`viewModel.destroyVM` 时自动清理）。但要注意：

- 不要在一个脚本中对同一事件注册多次
- 主单/子单/孙单的脚本分别注册，不会互相干扰

### 4. debugger 语句

**禁止**在生产代码中保留 `debugger` 语句。开发调试时可使用，提交前必须移除。

## 特殊事件

### beforeImportRender (列表页)

用于拦截 Excel 导入数据，在导入渲染前处理。

```javascript
viewModel.on('beforeImportRender', (data) => {
    // data.rows 为导入的原始行数据
    // 可以修改 rows 或返回错误阻止导入
    return true;  // 返回 false 阻止导入
});
```

### afterFileUpload / afterFileDelete

用于跟踪附件上传/删除状态。

```javascript
viewModel.on('afterFileUpload', (data) => {
    // data 包含上传文件信息
});
viewModel.on('afterFileDelete', (data) => {
    // data 包含删除文件信息
});
```

### beforeBatchpush

批量推单前的钩子。

```javascript
viewModel.on('beforeBatchpush', () => {
    // 设置批量推单的来源应用编码等
});
```

### beforePullFile

拉单时携带附件的钩子。

```javascript
viewModel.on('beforePullFile', (data) => {
    // 控制拉单时是否携带附件
});
```
