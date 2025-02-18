import logging
import json
import os
import re
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_deepseek import ChatDeepSeek
from agents.telegram_agent import TelegramAgent
from agents.github_agent import GitHubAgent
from agents.tavily_agent import TavilyAgent

# Загружаем переменные окружения
load_dotenv()

logger = logging.getLogger(__name__)

# Загружаем ключи API
DEEPSEEK_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("OPENAI_API_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("OPENAI_API_MODEL", "deepseek-chat")

# Создаем LLM модель DeepSeek
llm = ChatDeepSeek(
    model=DEEPSEEK_MODEL,
    api_key=DEEPSEEK_API_KEY,
    temperature=0.7,
    api_base=DEEPSEEK_BASE_URL
)

# Определяем память
memory = ConversationBufferMemory(memory_key="history")


# --- Декоратор для логирования шагов ---
def log_step(step_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"🔹 Начинаем шаг: {step_name}")
            result = func(*args, **kwargs)
            logger.info(f"✅ Завершен шаг: {step_name}, результат: {result}")
            return result
        return wrapper
    return decorator


# --- 1. Анализ задачи ---
def clean_and_parse_response(response):
    """Очищает JSON-ответ от <think>...<think> и парсит его."""
    try:
        content = response.content.strip()
        
        # Убираем <think>...</think>
        clean_json = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        
        # Декодируем JSON
        parsed_json = json.loads(clean_json)

        logger.info(f"📊 Анализ задачи: {parsed_json}")  # Логируем результат анализа

        return parsed_json
    
    except json.JSONDecodeError:
        logger.error(f"❌ Ошибка JSON: {response.content}")
        return {"summary": "Ошибка анализа", "tools": []}  # Безопасный fallback


analyze_prompt = PromptTemplate(
    input_variables=["task_description"],
    template="""
    Ты AI-ассистент. Определи, какие инструменты (GitHub, Twitter, Telegram, Tavily) 
    нужно использовать для выполнения задачи.

    Пример ответа:
    {{
        "summary": "Задача требует публикации в Twitter и уведомления в Telegram.",
        "tools": ["twitter", "telegram"]
    }}

    Важно: Верни JSON без лишнего текста!

    Входная задача: {task_description}
    """
)


def parse_analysis_response(response):
    """Парсит JSON-ответ от модели, сохраняя исходный task_description."""
    try:
        content = response.content.strip()
        clean_json = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        parsed_json = json.loads(clean_json)
        
        logger.info(f"📊 Разобранный анализ: {parsed_json}")
        
        return {
            # Сохраняем исходный task_description из контекста
            "task_description": response.task_description,  
            "analysis": parsed_json
        }
    except Exception as e:
        logger.error(f"❌ Ошибка парсинга: {e}")
        return {
            "task_description": response.task_description,
            "analysis": {"summary": "Ошибка анализа", "tools": []}
        }


analyze_chain = (
    RunnableLambda(lambda x: {"input_task": x})
    | analyze_prompt
    | llm
    | RunnableLambda(lambda response: parse_analysis_response(
        # Передаем исходное описание задачи в парсер
        response.with_task_description(response.context["input_task"])
    ))
)


# analyze_chain = analyze_prompt | llm | RunnableLambda(lambda response: {"analysis": clean_and_parse_response(response)})
# analyze_chain = (
#     RunnableLambda(lambda x: {"task_description": x})  # Передаем задачу дальше
#     | analyze_prompt
#     | llm
#     | RunnableLambda(lambda response: {
#         "task_description": response["task_description"],  # Теперь передаем дальше
#         "analysis": clean_and_parse_response(response)
#     })
# )


# --- 2. Поиск в интернете ---
@log_step("Поиск в интернете")
def search_internet(inputs):
    """Поиск информации, если Tavily включен в список инструментов."""
    analysis = inputs.get("analysis", {})
    task_description = inputs["task_description"]

    logger.info(f"📥 Входные данные в поиск: {inputs}")

    if not analysis.get("tools"):
        logger.warning("⚠️ Внимание: список инструментов пуст! Анализ может быть некорректным.")
    
    if not task_description:
        logger.error("❌ Ошибка: `task_description` пустой, невозможно выполнить поиск.")
        return {"analysis": analysis, "task_description": task_description, "internet_results": []}

    tavily_agent = TavilyAgent()

    try:
        search_results = tavily_agent.search(task_description) if "tavily" in analysis.get("tools", []) else []
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении поиска: {e}")
        search_results = []

    return {"analysis": analysis, "task_description": task_description, "internet_results": search_results}

# --- 3. Выполнение задачи ---
@log_step("Выполнение задачи")
def execute_task(inputs):
    """Выполнение задачи с нужными инструментами."""
    analysis = inputs.get("analysis", {})
    task_description = inputs.get("task_description", "")
    tools = analysis.get("tools", [])

    logger.info(f"📥 Входные данные в выполнение: {inputs}")  # Логируем входные данные

    if not tools:
        logger.warning("⚠️ Внимание: нет инструментов для выполнения! Возможно, ошибка анализа.")

    results = []

    if "telegram" in tools:
        telegram_agent = TelegramAgent()
        result = telegram_agent.send_message(f"🔔 Выполняю задачу: {task_description}")
        results.append(f"📢 Telegram: {result}")

    if "github" in tools:
        github_agent = GitHubAgent()
        repo_name = "ai-agent-tasks"
        result = github_agent.create_issue(repo_name, "AI Task", task_description)
        results.append(f"🔧 GitHub Issue: {result}")

    return {"analysis": analysis, "execution_results": results}


# --- 4. Формирование ответа ---
@log_step("Формирование ответа")
def summarize_result(inputs):
    """Формирует финальный ответ."""
    execution_results = inputs.get("execution_results", [])

    if not execution_results:
        response = "⚠️ Ошибка! Никакие действия не были выполнены."
        logger.error(response)
    else:
        response = f"✅ Задача выполнена!\n{'\n'.join(execution_results)}"

    return {"response": response}


# --- Собираем пайплайн ---
def build_agent_chain():
    """Создает цепочку обработки с логами."""
    return (
        RunnableLambda(lambda x: {"task_description": x})  # Начало (вход)
        | analyze_chain
        | RunnableLambda(search_internet)
        | RunnableLambda(execute_task)
        | RunnableLambda(summarize_result)
    )
