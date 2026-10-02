from memory.database import Database


class MemoryManager:
    def __init__(self, database=None):
        self.database = database or Database()

    def save_message(self, role, content):
        role = str(role).strip().lower()
        content = str(content).strip()

        if role not in ("user", "assistant", "system"):
            raise ValueError("Unsupported message role.")

        if not content:
            return False

        with self.database.connection() as connection:
            connection.execute(
                """
                INSERT INTO messages (role, content)
                VALUES (?, ?)
                """,
                (role, content),
            )

        return True

    def get_history(self, limit=50):
        limit = max(1, min(int(limit), 500))

        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT role, content, created_at
                FROM messages
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            dict(row)
            for row in reversed(rows)
        ]

    def clear_history(self):
        with self.database.connection() as connection:
            connection.execute(
                "DELETE FROM messages"
            )

    def save_memory(self, content, category="general"):
        content = str(content).strip()
        category = str(category).strip() or "general"

        if not content:
            return {
                "success": False,
                "error": "Memory content cannot be empty.",
            }

        with self.database.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO memories (category, content)
                VALUES (?, ?)
                """,
                (category, content),
            )

            memory_id = cursor.lastrowid

        return {
            "success": True,
            "id": memory_id,
            "content": content,
            "category": category,
        }

    def search_memories(self, query="", limit=20):
        query = str(query).strip()
        limit = max(1, min(int(limit), 100))

        with self.database.connection() as connection:
            if query:
                rows = connection.execute(
                    """
                    SELECT id, category, content,
                           created_at, updated_at
                    FROM memories
                    WHERE content LIKE ?
                       OR category LIKE ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (
                        f"%{query}%",
                        f"%{query}%",
                        limit,
                    ),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id, category, content,
                           created_at, updated_at
                    FROM memories
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def delete_memory(self, memory_id):
        with self.database.connection() as connection:
            cursor = connection.execute(
                "DELETE FROM memories WHERE id = ?",
                (int(memory_id),),
            )

        return cursor.rowcount > 0