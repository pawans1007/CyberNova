
import re
from memory.database import Database


class MemoryManager:
    def __init__(self, database=None):
        self.database = database or Database()

    # --------------------------------------------------
    # MESSAGE HISTORY
    # --------------------------------------------------

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

        return [dict(row) for row in reversed(rows)]

    def clear_history(self):
        with self.database.connection() as connection:
            connection.execute("DELETE FROM messages")

    # --------------------------------------------------
    # MEMORY NORMALIZATION
    # --------------------------------------------------

    @staticmethod
    def _normalize_memory(content):
        """
        Normalize memory text for duplicate detection.
        """
        return " ".join(
            re.findall(r"\w+", str(content).lower())
        )

    # --------------------------------------------------
    # SAVE MEMORY
    # --------------------------------------------------

    def save_memory(self, content, category="general"):
        content = str(content).strip()
        category = str(category).strip().lower() or "general"

        if not content:
            return {
                "success": False,
                "error": "Memory content cannot be empty.",
            }

        normalized_content = self._normalize_memory(content)

        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, category, content
                FROM memories
                WHERE category = ?
                """,
                (category,),
            ).fetchall()

            # Check for exact duplicates.
            for row in rows:
                existing_normalized = self._normalize_memory(
                    row["content"]
                )

                if existing_normalized == normalized_content:
                    return {
                        "success": True,
                        "id": row["id"],
                        "content": row["content"],
                        "category": row["category"],
                        "duplicate": True,
                    }

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
            "duplicate": False,
        }

    # --------------------------------------------------
    # UPDATE MEMORY
    # --------------------------------------------------

    def update_memory(self, memory_id, content, category=None):
        content = str(content).strip()

        if not content:
            return {
                "success": False,
                "error": "Memory content cannot be empty.",
            }

        try:
            memory_id = int(memory_id)
        except (ValueError, TypeError):
            return {
                "success": False,
                "error": "Invalid memory ID.",
            }

        with self.database.connection() as connection:
            existing = connection.execute(
                """
                SELECT id, category
                FROM memories
                WHERE id = ?
                """,
                (memory_id,),
            ).fetchone()

            if not existing:
                return {
                    "success": False,
                    "error": "Memory not found.",
                }

            new_category = (
                str(category).strip().lower()
                if category is not None
                else existing["category"]
            ) or "general"

            connection.execute(
                """
                UPDATE memories
                SET content = ?,
                    category = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (content, new_category, memory_id),
            )

        return {
            "success": True,
            "id": memory_id,
            "content": content,
            "category": new_category,
        }

    # --------------------------------------------------
    # SEARCH MEMORIES
    # --------------------------------------------------

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

        return [dict(row) for row in rows]

    # --------------------------------------------------
    # RELEVANT MEMORY RETRIEVAL
    # --------------------------------------------------

    def get_relevant_memories(self, query, limit=5):
        query = str(query).strip().lower()
        limit = max(1, min(int(limit), 20))

        if not query:
            return []

        stop_words = {
            "the", "and", "for", "are", "you", "your",
            "with", "that", "this", "what", "when",
            "where", "which", "who", "how", "why",
            "can", "could", "would", "should", "have",
            "has", "had", "was", "were", "will", "shall",
            "from", "into", "about", "please", "tell",
            "show", "give", "make", "does", "did",
            "its", "it's", "not", "but", "then",
            "remember", "memory", "memories", "using",
            "use", "used", "my", "me", "i", "am",
            "is", "a", "an", "to", "of", "in", "on",
            "it", "as", "at", "by", "be", "do",
            "project", "application",
        }

        words = re.findall(
            r"\b[a-zA-Z0-9_+#.-]+\b",
            query,
        )

        original_terms = {
            word for word in words
            if len(word) > 1 and word not in stop_words
        }

        if not original_terms:
            return []

        # Expand common terms to related technical vocabulary.
        synonym_groups = [
            {
                "gui", "ui", "interface", "desktop",
                "frontend", "visual",
            },
            {
                "framework", "toolkit", "library",
            },
            {
                "database", "db", "storage", "sqlite",
            },
            {
                "voice", "speech", "audio", "microphone",
                "vosk",
            },
            {
                "ai", "llm", "model", "assistant",
            },
            {
                "python", "pyside6", "pyqt", "tkinter",
                "kivy", "wxpython",
            },
            {
                "web", "browser", "internet", "search",
            },
            {
                "security", "cybersecurity", "pentest",
                "penetration", "vulnerability",
            },
        ]

        expanded_terms = set(original_terms)

        for group in synonym_groups:
            if original_terms.intersection(group):
                expanded_terms.update(group)

        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, category, content,
                       created_at, updated_at
                FROM memories
                ORDER BY updated_at DESC
                """
            ).fetchall()

        scored_memories = []

        for row in rows:
            memory = dict(row)

            content = str(
                memory.get("content", "")
            ).lower()

            category = str(
                memory.get("category", "")
            ).lower()

            memory_words = set(
                re.findall(
                    r"\b[a-zA-Z0-9_+#.-]+\b",
                    content,
                )
            )

            category_words = set(
                re.findall(
                    r"\b[a-zA-Z0-9_+#.-]+\b",
                    category,
                )
            )

            direct_matches = original_terms.intersection(
                memory_words
            )

            expanded_matches = (
                expanded_terms - original_terms
            ).intersection(memory_words)

            category_matches = original_terms.intersection(
                category_words
            )

            score = 0

            # Direct query matches have the highest weight.
            score += len(direct_matches) * 3

            # Related vocabulary gets a smaller weight.
            score += len(expanded_matches)

            # Matching categories provide additional relevance.
            score += len(category_matches) * 2

            # Reward memories that contain the complete query.
            if query in content:
                score += 5

            # Reward memories that match a larger portion
            # of the query.
            if original_terms:
                coverage = (
                    len(direct_matches) / len(original_terms)
                )
                score += coverage * 4

            if score > 0:
                memory["_relevance_score"] = score
                scored_memories.append(memory)

        # Sort by relevance. Recent memories retain priority
        # when relevance scores are equal.
        scored_memories.sort(
            key=lambda item: item["_relevance_score"],
            reverse=True,
        )

        results = []

        for memory in scored_memories[:limit]:
            memory.pop("_relevance_score", None)
            results.append(memory)

        return results

    # --------------------------------------------------
    # DELETE MEMORY
    # --------------------------------------------------

    def delete_memory(self, memory_id):
        try:
            memory_id = int(memory_id)
        except (ValueError, TypeError):
            return False

        with self.database.connection() as connection:
            cursor = connection.execute(
                "DELETE FROM memories WHERE id = ?",
                (memory_id,),
            )

        return cursor.rowcount > 0

    # --------------------------------------------------
    # CONVERSATION SUMMARY
    # --------------------------------------------------

    def save_conversation_summary(self, summary):
        summary = str(summary).strip()

        with self.database.connection() as connection:
            connection.execute(
                """
                INSERT INTO conversation_state (id, summary)
                VALUES (1, ?)
                ON CONFLICT(id) DO UPDATE SET
                    summary = excluded.summary,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (summary,),
            )

        return True

    def get_conversation_summary(self):
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT summary
                FROM conversation_state
                WHERE id = 1
                """
            ).fetchone()

        return row["summary"] if row else ""

    def clear_conversation_summary(self):
        with self.database.connection() as connection:
            connection.execute(
                """
                UPDATE conversation_state
                SET summary = '',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
                """
            )