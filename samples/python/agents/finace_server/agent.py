import json
import datetime
from typing import Any, AsyncIterable, Dict, Optional, List


class FinanceAgent:
    """财务报销合规性检查智能体。"""

    SUPPORTED_CONTENT_TYPES = ["text", "data"]

    def __init__(self):
        # 定义报销标准和规则
        self.reimbursement_rules = {
            "交通费": {
                "最高限额": 300.0,
                "需要发票": True,
                "备注": "火车限二等座，飞机限经济舱"
            },
            "餐饮费": {
                "最高限额": 100.0,
                "每日次数限制": 3,
                "需要发票": True
            },
            "住宿费": {
                "最高限额": 500.0,
                "需要发票": True,
                "备注": "限标准间"
            },
            "办公用品": {
                "最高限额": 200.0,
                "需要发票": True
            },
            "其他": {
                "最高限额": 100.0,
                "需要发票": True,
                "需要额外审批": True
            }
        }
        self.sessions = {}  # 用于存储会话状态
    
    def _check_compliance(self, expenses: List[Dict]) -> Dict[str, Any]:
        """
        检查报销项目是否合规
        
        Args:
            expenses: 报销项目列表，每个项目包含类别、金额、日期、是否有发票等信息
            
        Returns:
            包含审核结果的字典
        """
        total_amount = 0.0
        compliant_expenses = []
        non_compliant_expenses = []
        
        # 按日期分组处理餐饮费的每日限制
        daily_meals = {}
        
        for expense in expenses:
            category = expense.get("类别", "其他")
            amount = float(expense.get("金额", 0))
            date = expense.get("日期", datetime.datetime.now().strftime("%Y-%m-%d"))
            has_invoice = expense.get("是否有发票", False)
            
            # 检查该类别是否在规则中
            if category not in self.reimbursement_rules:
                category = "其他"
                
            rule = self.reimbursement_rules[category]
            is_compliant = True
            reasons = []
            
            # 检查金额是否超过限额
            if amount > rule["最高限额"]:
                is_compliant = False
                reasons.append(f"超出{category}最高限额{rule['最高限额']}元")
            
            # 检查是否有发票
            if rule["需要发票"] and not has_invoice:
                is_compliant = False
                reasons.append(f"{category}需要提供发票")
            
            # 特殊处理餐饮费的每日次数限制
            if category == "餐饮费":
                if date not in daily_meals:
                    daily_meals[date] = {"count": 0, "total": 0.0}
                
                daily_meals[date]["count"] += 1
                daily_meals[date]["total"] += amount
                
                if daily_meals[date]["count"] > rule["每日次数限制"]:
                    is_compliant = False
                    reasons.append(f"超出餐饮费每日{rule['每日次数限制']}次限制")
            
            # 记录结果
            expense_result = expense.copy()
            expense_result["合规"] = is_compliant
            
            if is_compliant:
                compliant_expenses.append(expense_result)
                total_amount += amount
            else:
                expense_result["原因"] = reasons
                non_compliant_expenses.append(expense_result)
        
        return {
            "合规报销": compliant_expenses,
            "不合规报销": non_compliant_expenses,
            "合规报销总金额": total_amount,
            "报销项目总数": len(expenses),
            "合规项目数": len(compliant_expenses),
            "不合规项目数": len(non_compliant_expenses)
        }
    
    def invoke(self, query, session_id) -> str:
        """
        处理同步报销请求
        
        Args:
            query: 用户查询或报销数据
            session_id: 会话ID
            
        Returns:
            处理结果的字符串表示
        """
        try:
            # 尝试将查询解析为JSON数据
            data = json.loads(query) if isinstance(query, str) else query
            
            if isinstance(data, dict) and "expenses" in data:
                # 处理报销数据
                result = self._check_compliance(data["expenses"])
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                return "MISSING_INFO: 请提供包含expenses字段的报销数据，格式为JSON"
        except json.JSONDecodeError:
            # 如果不是JSON，则尝试理解文本查询
            return "MISSING_INFO: 请提供有效的JSON格式报销数据"
        except Exception as e:
            return f"处理报销请求时出错: {str(e)}"

    async def stream(self, query, session_id) -> AsyncIterable[Dict[str, Any]]:
        """
        处理流式报销请求
        
        Args:
            query: 用户查询或报销数据
            session_id: 会话ID
            
        Returns:
            异步生成器，产生处理状态和结果
        """
        try:
            # 发送处理开始通知
            yield {
                "is_task_complete": False,
                "updates": "正在处理报销合规性检查..."
            }
            
            # 尝试将查询解析为JSON数据
            if isinstance(query, str):
                try:
                    data = json.loads(query)
                except json.JSONDecodeError:
                    yield {
                        "is_task_complete": True,
                        "content": "MISSING_INFO: 请提供有效的JSON格式报销数据"
                    }
                    return
            else:
                data = query
            
            if isinstance(data, dict) and "expenses" in data:
                # 处理报销数据
                result = self._check_compliance(data["expenses"])
                
                # 发送最终结果
                yield {
                    "is_task_complete": True,
                    "content": {
                        "response": {
                            "result": json.dumps(result, ensure_ascii=False)
                        }
                    }
                }
            else:
                yield {
                    "is_task_complete": True,
                    "content": "MISSING_INFO: 请提供包含expenses字段的报销数据，格式为JSON"
                }
        except Exception as e:
            yield {
                "is_task_complete": True,
                "content": f"处理报销请求时出错: {str(e)}"
            }
