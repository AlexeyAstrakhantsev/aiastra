import os
import tweepy
from dotenv import load_dotenv

load_dotenv()


class TwitterAgent:
    """Агент для работы с Twitter API. Позволяет публиковать твиты."""

    def __init__(self) -> None:
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = os.getenv("TWITTER_ACCESS_SECRET")

        self.auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
        self.auth.set_access_token(self.access_token, self.access_secret)
        self.api = tweepy.API(self.auth)

    def post_tweet(self, message: str) -> None:
        """
        Публикует твит.

        :param message: Текст твита
        """
        try:
            self.api.update_status(message)
            print(f"✅ Твит опубликован: {message}")
        except Exception as e:
            print(f"❌ Ошибка при публикации твита: {e}")
