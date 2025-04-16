from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from task_manager import AgentTaskManager
from agent import TaxiReimbursementAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10003)
def main(host, port):
    try:
        if not os.getenv("GOOGLE_API_KEY"):
                raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")
        
        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="process_taxi_reimbursement",
            name="处理打车费报销",
            description="根据公司规定审核和处理员工的打车费报销申请。",
            tags=["打车费", "报销", "出租车"],
            examples=["我需要报销昨晚加班打车回家的费用", "昨天晚上10点在中关村资本大厦打车回家，花了50元"],
        )
        agent_card = AgentCard(
            name="打车费报销代理",
            description="这个代理负责处理员工的打车费报销请求，审核是否符合公司规定（仅报销晚上9点到次日凌晨5点期间、从中关村资本大厦附近出发的打车费）。",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=TaxiReimbursementAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=TaxiReimbursementAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=TaxiReimbursementAgent()),
            host=host,
            port=port,
        )
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)
    
if __name__ == "__main__":
    main()
