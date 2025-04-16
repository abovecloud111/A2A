import json
import random
from typing import Any, AsyncIterable, Dict, Optional
from datetime import datetime, time
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Local cache of created request_ids for demo purposes.
request_ids = set()

# 合法的上车地点列表
VALID_PICKUP_LOCATIONS = [
    "中关村资本大厦", "中关村资本大厦北门", "海淀区学院南路", "学院南路", "资本大厦"
]

# 不合法的上车地点关键词
INVALID_LOCATION_KEYWORDS = ["中关村", "望京", "国贸"]

def is_valid_pickup_location(location: str) -> bool:
    """
    检查上车地点是否符合公司规定。
    
    规则：
    - 上车地点必须是中关村资本大厦附近
    - 不能是中关村、望京、国贸等其他地区
    """
    # 首先检查是否明确包含合法地点
    for valid_location in VALID_PICKUP_LOCATIONS:
        if valid_location in location:
            return True
    
    # 然后检查是否包含不合法地点关键词
    # 注意：这里我们需要排除"中关村资本大厦"这样的特殊情况
    for keyword in INVALID_LOCATION_KEYWORDS:
        if keyword in location and "中关村资本大厦" not in location:
            return False
    
    # 如果既不明确合法也不明确不合法，则默认为不合法
    return False

def is_valid_pickup_time(pickup_time: str) -> tuple[bool, str]:
    """
    检查上车时间是否符合公司规定。
    
    规则：
    - 上车时间必须在晚上9点到次日凌晨5点之间
    """
    try:
        # 尝试解析时间字符串
        parsed_time = None
        
        # 尝试多种常见格式
        formats = ["%H:%M", "%H点%M分", "%H时%M分", "%H点", "%H时"]
        
        for fmt in formats:
            try:
                parsed_time = datetime.strptime(pickup_time, fmt).time()
                break
            except ValueError:
                continue
        
        if parsed_time is None:
            return False, "无法识别的时间格式，请使用 HH:MM 格式"
        
        # 检查时间是否在晚上9点到次日凌晨5点之间
        night_start = time(21, 0)  # 晚上9点
        morning_end = time(5, 0)   # 凌晨5点
        
        if parsed_time >= night_start or parsed_time <= morning_end:
            return True, ""
        else:
            return False, f"上车时间 {pickup_time} 不在允许的时间范围内（晚上9点到次日凌晨5点）"
    
    except Exception as e:
        return False, f"时间格式错误: {str(e)}，请使用 HH:MM 格式"

def create_taxi_request_form(
    pickup_location: Optional[str] = None, 
    pickup_time: Optional[str] = None, 
    date: Optional[str] = None, 
    amount: Optional[str] = None
) -> dict[str, Any]:
    """
    创建打车费报销申请表单。
    
    Args:
        pickup_location (str): 上车地点。
        pickup_time (str): 上车时间。
        date (str): 乘车日期。
        amount (str): 打车费金额。
        
    Returns:
        dict[str, Any]: 包含表单数据的字典。
    """
    request_id = "request_id_" + str(random.randint(1000000, 9999999))
    request_ids.add(request_id)
    return {
        "request_id": request_id,
        "pickup_location": "<上车地点>" if not pickup_location else pickup_location,
        "pickup_time": "<上车时间（24小时制，如 21:30）>" if not pickup_time else pickup_time,
        "date": "<乘车日期>" if not date else date,
        "amount": "<打车费金额>" if not amount else amount,
    }

def return_form(
    form_request: dict[str, Any],    
    tool_context: ToolContext,
    instructions: Optional[str] = None
) -> dict[str, Any]:
    """
    返回结构化JSON对象表示要完成的表单。
    
    Args:
        form_request (dict[str, Any]): 请求表单数据。
        tool_context (ToolContext): 工具运行的上下文。
        instructions (str): 处理表单的说明。可以为空。
        
    Returns:
        dict[str, Any]: 表单响应的JSON字典。
    """  
    if isinstance(form_request, str):
        form_request = json.loads(form_request)

    tool_context.actions.skip_summarization = True
    tool_context.actions.escalate = True
    form_dict = {
        'type': 'form',
        'form': {
            'type': 'object',
            'properties': {
                'pickup_location': {
                    'type': 'string',
                    'description': '上车地点',
                    'title': '上车地点',
                },
                'pickup_time': {
                    'type': 'string',
                    'description': '上车时间（24小时制，如 21:30）',
                    'title': '上车时间',
                },
                'date': {
                    'type': 'string',
                    'format': 'date',
                    'description': '乘车日期',
                    'title': '日期',
                },
                'amount': {
                    'type': 'string',
                    'format': 'number',
                    'description': '打车费金额',
                    'title': '金额',
                },
                'request_id': {
                    'type': 'string',
                    'description': '请求ID',
                    'title': '请求ID',
                },
            },
            'required': list(form_request.keys()),
        },
        'form_data': form_request,
        'instructions': instructions,
    }
    return json.dumps(form_dict)

def reimburse_taxi(request_id: str, pickup_location: str, pickup_time: str) -> dict[str, Any]:
    """
    根据公司政策审核并报销打车费用。
    
    规则：
    - 上车时间必须在晚上9点到次日凌晨5点
    - 上车地点必须是中关村资本大厦附近，不能是中关村、望京、国贸等其他地点
    """
    if request_id not in request_ids:
        return {"request_id": request_id, "status": "拒绝", "reason": "无效的请求ID"}
    
    # 检查上车地点是否符合规定
    if not is_valid_pickup_location(pickup_location):
        return {
            "request_id": request_id, 
            "status": "拒绝", 
            "reason": f"上车地点'{pickup_location}'不符合公司规定，必须是中关村资本大厦附近"
        }
    
    # 检查上车时间是否符合规定
    valid_time, time_error = is_valid_pickup_time(pickup_time)
    if not valid_time:
        return {
            "request_id": request_id, 
            "status": "拒绝", 
            "reason": time_error
        }
    
    # 符合所有规定，批准报销
    return {"request_id": request_id, "status": "批准"}


class TaxiReimbursementAgent:
    """处理打车费用报销的代理。"""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = "remote_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def invoke(self, query, session_id) -> str:
        session = self._runner.session_service.get_session(
            app_name=self._agent.name, user_id=self._user_id, session_id=session_id
        )
        content = types.Content(
            role="user", parts=[types.Part.from_text(text=query)]
        )
        if session is None:
            session = self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        events = self._runner.run(
            user_id=self._user_id, session_id=session.id, new_message=content
        )
        if not events or not events[-1].content or not events[-1].content.parts:
            return ""
        return "\n".join([p.text for p in events[-1].content.parts if p.text])

    async def stream(self, query, session_id) -> AsyncIterable[Dict[str, Any]]:
        session = self._runner.session_service.get_session(
            app_name=self._agent.name, user_id=self._user_id, session_id=session_id
        )
        content = types.Content(
            role="user", parts=[types.Part.from_text(text=query)]
        )
        if session is None:
            session = self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                response = ""
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    response = "\n".join([p.text for p in event.content.parts if p.text])
                elif (
                    event.content
                    and event.content.parts
                    and any([True for p in event.content.parts if p.function_response])):
                    response = next((p.function_response.model_dump() for p in event.content.parts))
                yield {
                    "is_task_complete": True,
                    "content": response,
                }
            else:
                yield {
                    "is_task_complete": False,
                    "updates": "正在处理打车费报销请求...",
                }

    def _build_agent(self) -> LlmAgent:
        """构建打车费报销代理的LLM代理。"""
        return LlmAgent(
            model="gemini-2.0-flash-001",
            name="taxi_reimbursement_agent",
            description=("这个代理处理员工的打车费报销请求，根据公司规定审核打车费用是否符合报销条件。"),
            instruction="""
你是一个处理打车费报销的代理。

当你收到打车费报销请求时，应首先使用 create_taxi_request_form() 创建一个新的请求表单。如果用户提供了表单所需的任何信息，请使用用户提供的值，否则保留默认占位符。表单包含以下字段：
  1. '上车地点'：员工上车的地点
  2. '上车时间'：员工上车的时间（24小时制，如 21:30）
  3. '乘车日期'：乘车的日期
  4. '金额'：打车费金额

创建表单后，应返回调用 return_form 的结果，并传入 create_taxi_request_form 调用返回的表单数据。

当收到用户填写的表单后，应检查表单是否包含所有必需信息：
  1. '上车地点'：员工上车的地点
  2. '上车时间'：员工上车的时间
  3. '乘车日期'：乘车的日期
  4. '金额'：打车费金额

如果缺少任何信息，应直接调用 return_form 方法拒绝请求，并提供缺失的字段。

对于完整的报销请求，应使用 reimburse_taxi() 函数根据公司规定审核打车费用：
- 公司仅报销上车时间为晚上9点到次日凌晨5点期间的打车费
- 上车地点必须是中关村资本大厦附近（可接受：中关村资本大厦、中关村资本大厦北门、海淀区学院南路）
- 不报销上车地点为中关村、望京、国贸等其他地方的打车费（注意：中关村资本大厦是例外，是可以的）

在回复中，应包含请求ID和报销请求的状态（批准或拒绝），以及如果拒绝的话，拒绝的原因。
""",
            tools=[
                create_taxi_request_form,
                reimburse_taxi,
                return_form,
            ],
        )
