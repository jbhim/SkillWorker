# API 参考

本文档是 `mdf-script-development` skill 的支持文件，提供完整的 MDF 前端脚本 API 参考。

## 核心命名空间

| 命名空间 | 说明 |
|---------|------|
| `viewModel` | 页面视图模型根对象，所有脚本的入口点 |
| `cb.rest` | REST 客户端，网络请求和远程函数调用 |
| `cb.utils` | 工具函数集（弹窗、确认、加载、引用等） |
| `cb.extend` | 扩展注册中心（环境配置、特性开关） |
| `cb.context` | 上下文工具（获取用户信息等） |
| `cb.lang` | 国际化（i18n）模板工具 |
| `window.jDiwork` | 跨窗口服务调用（打开单据、服务等） |

---

## viewModel 方法

### 事件监听

```javascript
viewModel.on(eventName, callback)    // 注册事件监听
viewModel.un(eventName)              // 移除事件监听
```

### 数据获取

```javascript
viewModel.get(fieldId)               // 获取字段/按钮/子模型，返回对应 Model
viewModel.getGridModel([gridName])   // 获取表格模型，不传参数时返回默认表格
viewModel.getAllData()               // 获取完整单据数据（表头 + 表体）
viewModel.getData()                  // 获取单据数据（子集）
viewModel.getParams()                // 获取路由/URL 参数
viewModel.getDomainKey()             // 获取当前域标识
viewModel.getCache(key)              // 获取缓存值
viewModel.getState(key)              // 获取状态值
```

### 数据操作

```javascript
viewModel.clear()                    // 清空所有字段
viewModel.validate()                 // 触发表单校验
viewModel.collectData()              // 收集数据用于保存（移动端常用）
viewModel.setProxy(config)           // 创建代理对象用于 API 调用
```

### 页面控制

```javascript
viewModel.execute(action, params)    // 执行框架动作
// action 可选值: 'refresh', 'updateViewMeta', 'customEventBeforeSave', 'endBatchModifyVoucher'
viewModel.enableFeature(name)        // 启用平台特性
// name 可选值: 'lazyLoadByPage', 'asyncSave', 'filteringCrossPage'
viewModel.communication({type: 'return'})  // 跨 ViewModel 通信
```

---

## 字段模型 (Field Model)

通过 `viewModel.get(fieldId)` 获取。

### 值操作

```javascript
field.getValue()                     // 获取字段值
field.setValue(value)                // 设置字段值
```

### 状态控制

```javascript
field.setState(key, value)           // 设置字段状态
// key: 'disabled' | 'readOnly' | 'bCanModify' | 'cShowCaption' | 'visible'

field.setVisible(bool)               // 显示/隐藏字段
field.setDisabled(bool)              // 启用/禁用字段
field.setReadOnly(bool)              // 设置只读
```

### 字段事件

```javascript
field.on('beforeValueChange', (data) => {
    // 返回 false 可阻止值变更
})
field.on('afterValueChange', (data) => {
    // data.value - 新值
    // data.oldValue - 旧值
})
field.on('valueChange', (data) => {})
field.on('blur', (data) => {})
field.on('beforeBrowse', (arg) => {
    // 参照浏览前过滤，通过 arg.context.setFilter() 或 setTreeFilter()
})
field.on('beforeReferOkClick', (data) => {
    // 返回 false 可阻止参照确认
})
```

### 参照字段过滤示例

```javascript
field.on('beforeBrowse', (arg) => {
    const condition = {
        isExtend: true,
        simpleVOs: [{ field: 'fieldName', op: 'eq', value1: someValue }]
    };
    arg.context.setFilter(condition);    // 普通参照
    // 或 arg.context.setTreeFilter(condition);  // 树形参照
});
```

---

## 表格模型 (Grid Model)

通过 `viewModel.getGridModel(gridName)` 获取。

### 行数据操作

```javascript
gridModel.getRows()                    // 获取当前页行数据
gridModel.getAllData()                 // 获取所有行数据
gridModel.getRow(index)                // 获取单行
gridModel.updateRow(index, rowObj)     // 更新单行
gridModel.updateRows(indexes, rowObjs) // 批量更新行
gridModel.insertRows(position, rows)   // 插入行
gridModel.appendRow(row)               // 追加行
gridModel.clear()                      // 清空所有行
```

### 单元格操作

```javascript
gridModel.setCellValue(index, key, value)    // 设置单元格值
gridModel.getCellValue(index, key)           // 获取单元格值
gridModel.setCellState(index, key, stateKey, value)  // 设置单元格状态
// stateKey: 'disabled' | 'bCanModify'
```

### 列操作

```javascript
gridModel.setColumnState(key, stateKey, value)  // 设置整列状态（所有行）
gridModel.setColumnValue(key, value)            // 设置整列值（所有行）
gridModel.getColumns()                          // 获取列元数据
gridModel.getColumn(key)                        // 获取单列元数据
```

### 选中与焦点

```javascript
gridModel.getSelectedRowIndexes()        // 获取选中行索引数组
gridModel.getFocusedRowIndex()           // 获取焦点行索引
gridModel.setFocusedRowIndex(index)      // 设置焦点行
```

### 分页

```javascript
gridModel.setPageSize(n)                 // 设置每页大小
gridModel.setPageInfo(info)              // 设置分页信息
gridModel._get_data('pageInfo')          // 获取内部页信息对象
gridModel.execute('lazyLoadByPageInfo')  // 执行懒加载
```

### 整体控制

```javascript
gridModel.setDisabled(bool)              // 启用/禁用整个表格
```

### 表格事件

```javascript
gridModel.on('afterCellValueChange', (data) => {
    // data.rowIndex, data.cellName, data.value
    // data.indexs 用于批量操作场景
})
gridModel.on('beforeCellValueChange', (data) => {
    // 返回 false 可阻止单元格值变更
})
gridModel.on('beforeInsertRow', (args) => {
    // 可在行插入前修改 incoming row，args.isCopy 判断是否复制操作
})
gridModel.on('afterInsertRow', (args) => {})
gridModel.on('beforeBrowse', (arg) => {
    // arg.cellName - 触发参照的列名
    // arg.context.setFilter() / setTreeFilter()
})
gridModel.on('beforeCellJointQuery', (arg) => {})
gridModel.on('afterSetDataSource', (data) => {})
gridModel.on('beforeSetActionsState', (data) => {
    // 控制行操作按钮显隐
})
```

### 编辑行弹窗

```javascript
const editModal = gridModel.getEditRowModel();
// 用于行编辑弹窗的自定义 DOM 操作
// 监听 tableEditRowModalDidMount 事件
```

---

## cb.rest API

### DynamicProxy（代理调用）

```javascript
const proxy = cb.rest.DynamicProxy.create({
    actionName: {
        url: '/api/path?domainKey=xxx',
        method: 'POST',    // GET | POST | PUT | DELETE
        options: {         // 可选
            header: { 'Content-Type': 'application/json' }
        }
    }
});

// 回调风格
proxy.actionName(params, (err, result) => {
    if (err) { cb.utils.alert(err.message, 'error'); return; }
    // 处理 result
});
```

### invokeFunction（远程函数调用）

```javascript
// 同步调用
const result = cb.rest.invokeFunction('functionName', params, null, null, { async: false });

// 回调风格
cb.rest.invokeFunction('functionName', params, (err, result) => {
    if (err) { cb.utils.alert(err.message, 'error'); return; }
    // 处理 result
}, viewModel, { async: false });
```

### 用户上下文

```javascript
cb.rest.AppContext.user.userId       // 当前用户 ID
cb.rest.AppContext.user.userName     // 当前用户名
cb.rest.AppContext.user.identityId   // 当前身份 ID
```

### 其他

```javascript
cb.rest._ah.currentBillIsOffline()   // 检查当前单据是否离线模式
cb.rest._appendUrl(url, queryParams) // 拼接查询参数到 URL
```

---

## cb.utils API

### 弹窗与提示

```javascript
cb.utils.alert(message, type)
// type: 'error' | 'success' | 'warning' | 'info'

cb.utils.confirm(message, onOk, onCancel, title, okText)
```

### 参照操作

```javascript
cb.utils.getRefDataByCommon(field, conditions)    // 查询参照数据
cb.utils.triggerReferBrowse(field, conditions)    // 触发参照浏览（带过滤条件）
```

### 加载控制

```javascript
cb.utils.loadingControl.start({ diworkCode })     // 开始 loading
cb.utils.loadingControl.end({ diworkCode })       // 结束 loading
```

### 附件

```javascript
cb.utils.bindAttachmentPromise(viewModel, data)   // 绑定附件到单据
```

### 类型检查

```javascript
cb.utils.isPlainObject(val)                       // 是否为纯对象
```

### 用户信息

```javascript
cb.utils.getUser(domainKey)                       // 获取用户信息
```

### 国际化

```javascript
cb.lang.template('template_key', { params })      // i18n 模板
cb.utils.templateByUuid(uuid)                     // 通过 UUID 获取模板
```

---

## cb.extend API

### 环境注册

```javascript
cb.extend.registerEnv(domainKey, config)
// config 示例:
// {
//     pullVoucherCarryDetail: true,    // 拉单携带明细
//     createCodeCarryDetail: true,     // 生单携带编码明细
//     performance: { asyncSave: true } // 性能配置
// }
```

---

## window.jDiwork API

### 打开服务/单据

```javascript
window.jDiwork.openService(
    serviceId,
    { billtype: 'xxx', billno: 'xxx' },
    { data: { mode: 'edit', readOnly: false, id: 'xxx' } }
);
```

---

## viewModel 常用属性

```javascript
viewModel.viewCode        // 视图编码
viewModel.billtype        // 单据类型
viewModel.domainKey       // 域标识
viewModel.mode            // 当前模式: 'browse' | 'edit' | 'add'
```

## 字段命名约定

- 字段名使用 snake_case
- 嵌套/参照字段用 `__` 分隔（如 `pk_org__name`）
- userDefines 自定义字段使用 `T` 前缀编码（T0002, T0003 等）
- 盘点类单据使用 `_before` / `_after` 后缀区分前后值
- 表格名遵循 `module_table_bList` 模式，子表加 `_sList`，孙表加 `_gsList`
