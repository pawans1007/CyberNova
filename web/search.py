from ddgs import DDGS


class WebSearch:
    def __init__(self, max_results=5):
        self.max_results = max(1, min(max_results, 10))

    def search(self, query):
        query = str(query).strip()

        if not query:
            return {
                "success": False,
                "error": "Search query cannot be empty.",
                "results": [],
            }

        try:
            with DDGS() as ddgs:
                raw_results = list(
                    ddgs.text(
                        query,
                        max_results=self.max_results,
                    )
                )

            results = []

            for item in raw_results:
                results.append({
                    "title": item.get("title", "Untitled"),
                    "url": item.get("href", ""),
                    "snippet": item.get("body", ""),
                })

            return {
                "success": True,
                "query": query,
                "results": results,
            }

        except Exception as error:
            return {
                "success": False,
                "error": str(error),
                "results": [],
            }