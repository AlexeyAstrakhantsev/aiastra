import os
from github import Github
from github.Repository import Repository
from dotenv import load_dotenv

load_dotenv()


class GitHubAgent:
    """
    Агент для взаимодействия с GitHub API.
    Позволяет загружать файлы и создавать репозитории.
    """

    def __init__(self) -> None:
        self.token = os.getenv("GITHUB_TOKEN")
        self.github = Github(self.token)
        self.user = self.github.get_user()

    def get_or_create_repo(self, repo_name: str) -> Repository:
        """
        Получает репозиторий или создаёт новый.

        :param repo_name: Название репозитория
        :return: Объект репозитория
        """
        try:
            repo = self.github.get_repo(f"{self.user.login}/{repo_name}")
        except Exception:
            repo = self.user.create_repo(repo_name, private=False)
        return repo

    def upload_file(
            self, repo_name: str, file_path: str,
            commit_message: str = "Добавлен новый файл") -> None:
        """
        Загружает файл в репозиторий.

        :param repo_name: Название репозитория
        :param file_path: Локальный путь к файлу
        :param commit_message: Сообщение коммита
        """
        repo = self.get_or_create_repo(repo_name)
        file_name = os.path.basename(file_path)

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        try:
            repo.create_file(file_name, commit_message, content)
            print(f"✅ Файл {file_name} успешно загружен в {repo_name}")
        except Exception as e:
            print(f"❌ Ошибка загрузки файла: {e}")
