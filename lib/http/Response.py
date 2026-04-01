from typing import Dict


class Response:
    def __init__(
        self,
        status_code: int = 200,
        headers: Dict[str, str] | None = None,
        body: str = ""
    ):
        self._default_status = status_code
        self._default_headers = dict(headers) if headers else {}
        self._default_body = body

        self.status_code: int = status_code
        self.headers: Dict[str, str] = dict(headers) if headers else {}
        self.body: str = body
        self.sent: bool = False

    # ---------- Mutators ----------

    def set_content_type(self, content_type: str) -> "Response":
        self.headers["Content-Type"] = content_type
        return self

    def set_status_code(self, code: int) -> None:
        self.status_code = code

    def set_header(self, name: str, value: str) -> None:
        self.headers[name] = value

    def set_body(self, content: str) -> None:
        self.body = content

    def redirect(self, url: str, status_code: int = 302) -> None:
        self.status_code = status_code
        self.headers["Location"] = url

    # ---------- Accessors ----------

    def get_status_code(self) -> int:
        return self.status_code

    def get_headers(self) -> Dict[str, str]:
        return self.headers

    def get_body(self) -> str:
        return self.body

    # ---------- Lifecycle ----------

    def reset(self) -> None:
        """
        Reset response to its initial constructor state.
        Safe for reuse from a service container.
        """
        self.status_code = self._default_status
        self.headers.clear()
        self.headers.update(self._default_headers)
        self.body = self._default_body
        self.sent = False

    def send(self) -> None:
        """
        Send response with proper CGI headers.
        
        For CGI, we must output:
        1. Status line (optional for 200)
        2. Headers (Content-Type is required)
        3. Blank line
        4. Body content
        """
        if self.sent:
            return

        # Ensure Content-Type is set (required for CGI)
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "text/html; charset=utf-8"

        # Output Status header if not 200
        if self.status_code != 200:
            print(f"Status: {self.status_code}")

        # Output all headers
        for name, value in self.headers.items():
            print(f"{name}: {value}")

        # Blank line separates headers from body (CRITICAL for CGI)
        print()

        # Output body
        print(self.body, end="")

        self.sent = True 