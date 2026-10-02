from memory.database import Database


DEFAULT_SETTINGS = {
    "ollama_host": "http://localhost:11434",
    "ollama_model": "qwen2.5:3b-instruct",
    "voice_enabled": "false",
    "voice_wake_word_enabled": "false",
    "speech_rate": "175",
    "theme": "dark",
}


class SettingsManager:
    def __init__(self, database=None):
        self.database = database or Database()
        self._initialize_defaults()

    def _initialize_defaults(self):
        for key, value in DEFAULT_SETTINGS.items():
            self.set_default(key, value)

    def set_default(self, key, value):
        with self.database.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO settings (key, value)
                VALUES (?, ?)
                """,
                (str(key), str(value)),
            )

    def get(self, key, default=None):
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT value
                FROM settings
                WHERE key = ?
                """,
                (str(key),),
            ).fetchone()

        if row is None:
            return default

        return row["value"]

    def set(self, key, value):
        with self.database.connection() as connection:
            connection.execute(
                """
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (str(key), str(value)),
            )

        return True

    def get_all(self):
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT key, value
                FROM settings
                ORDER BY key
                """
            ).fetchall()

        return {
            row["key"]: row["value"]
            for row in rows
        }

    def reset(self):
        with self.database.connection() as connection:
            connection.execute(
                "DELETE FROM settings"
            )

        self._initialize_defaults()