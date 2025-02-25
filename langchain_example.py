from langchain_deepseek import ChatDeepSeek
#from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryMemory
from langchain.agents import initialize_agent, Tool
from tavily import TavilyClient
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)
load_dotenv()

class TavilySearchTool:
    """Инструмент для поиска через Tavily с обработкой результатов"""
    
    def __init__(self):
        self.client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
    def search(self, query: str) -> str:
        """Выполняет поиск и возвращает текстовые результаты"""
        try:
            logger.info(f"🔍 Поиск: {query}")
            result = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=3,
                include_answer=True
            )
            
            if not result.get("results"):
                return "Информация не найдена"
                
            # Форматируем результаты в текстовый вид
            response = []
            if result.get("answer"):
                response.append(f"Ответ: {result['answer']}")
                
            for idx, res in enumerate(result["results"][:3], 1):
                response.append(
                    f"{idx}. [{res['title']}]({res['url']}): {res['content']}"
                )
            
            return "\n\n".join(response)
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            return "Ошибка при получении информации"

# Инициализация моделей и инструментов
tavily_tool = TavilySearchTool()

llm = ChatDeepSeek(
    model=os.getenv("OPENAI_API_MODEL", "deepseek-chat"),
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.7,
    api_base=os.getenv("OPENAI_API_BASE_URL", "https://api.deepseek.com/v1")
)

tools = [
    Tool(
        name="InternetSearch",
        func=tavily_tool.search,
        description=(
            "Полезно для поиска актуальной информации в интернете. "
            "Используй для вопросов о текущих событиях, погоде, "
            "последних новостях или специфических данных."
        )
    )
]

# memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
memory = ConversationSummaryMemory(
    llm=llm, memory_key="chat_history", return_messages=True)

agent = initialize_agent(
    tools,
    llm,
    agent="chat-conversational-react-description",
    memory=memory,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=3,

)

# Запуск чат-бота
print("Система: Привет! Я могу ответить на ваши вопросы. Для выхода введите 'exit'")
while True:
    try:
        user_input = input("Вы: ").strip()
        if user_input.lower() in {'exit', 'выход', 'quit'}:
            break
            
        response = agent.run({"input": user_input})
        print(f"\nСистема: {response}\n")
        
    except Exception as e:
        print(f"⚠️ Произошла ошибка: {str(e)}")
        memory.clear()  # Очистка памяти при ошибках