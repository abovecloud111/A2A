from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from task_manager import AgentTaskManager
from agent import FinanceAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10004)
def main(host, port):
    try:
        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="process_finance_reimbursement",
            name="财务报销合规检查",
            description="根据公司规定审核和处理员工的各类报销申请。",
            tags=["财务", "报销", "合规", "经费"],
            examples=["我需要报销一些差旅费用", "帮我检查这些报销项目是否合规"],
        )
        agent_card = AgentCard(
            name="财务报销合规检查代理",
            description="这个代理负责处理员工的报销请求，审核是否符合公司规定的各类报销标准。",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=FinanceAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=FinanceAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=FinanceAgent()),
            host=host,
            port=port,
        )
        server.start()
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)
    
if __name__ == "__main__":
    main()
