from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "moocs_user"
    db_password: str = "123456789"
    db_name: str = "moocs_db"

    # Coursera connector
    coursera_mode: str = "scrape"
    coursera_sitemap_index: str = "https://www.coursera.org/sitemap.xml"
    coursera_course_sitemap: str = "https://www.coursera.org/sitemap~www~courses.xml"
    coursera_max_urls: int = 5000

    # MIT OpenCourseWare connector
    mit_ocw_mode: str = "scrape"
    mit_ocw_sitemap_index: str = "https://ocw.mit.edu/sitemap.xml"
    mit_ocw_sitemaps: str = "https://ocw.mit.edu/sitemap-www.xml"
    mit_ocw_max_urls: int = 5000

    # HTTP politeness and retries
    http_timeout_s: int = 30
    http_sleep_ms: int = 200
    http_max_retries: int = 5

    # Optional credentials/tokens
    coursera_auth_token: str | None = None


settings = Settings()
