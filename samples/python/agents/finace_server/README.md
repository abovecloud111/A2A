## 财务报销合规检查代理

这个示例使用 A2A 协议创建了一个简单的"财务报销合规检查"代理，可以帮助员工检查他们的报销申请是否符合公司规定。

该代理处理多种类型的报销请求，并根据公司规定的标准对每一项进行审核，包括交通费、餐饮费、住宿费和办公用品等。

## 前提条件

- Python 3.9 或更高版本
- UV

## 运行示例

1. 导航到代理目录：
   ```bash
   cd A2A/samples/python/agents/finace_server
   ```

2. 运行代理：
   ```bash
   uv run .
   ```

3. 代理将在 http://localhost:10004 上启动

## 使用方法

该代理接受 JSON 格式的报销数据，格式如下：

```json
{
  "expenses": [
    {
      "类别": "交通费",
      "金额": 200,
      "日期": "2025-04-14",
      "是否有发票": true
    },
    {
      "类别": "餐饮费",
      "金额": 80,
      "日期": "2025-04-14",
      "是否有发票": true
    }
  ]
}
```

代理将检查每个报销项目是否符合公司规定，并返回详细的审核结果。
