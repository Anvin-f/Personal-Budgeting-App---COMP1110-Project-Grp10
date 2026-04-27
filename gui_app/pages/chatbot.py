import threading
import tkinter as tk

import core.settings as app_settings
from core.chatbot import build_financial_context, get_chat_response

from ..base import Page
from ..constants import ACCENT, BG, BORDER, CARD, FONT, FONT_H, TEXT
from ..helpers import button, card, page_header


class ChatbotPage(Page):
    def build(self):
        page_header(self, "AI Assistant")

        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=24, pady=(12, 18))

        chat_card = card(main)
        chat_card.pack(fill="both", expand=True)

        # Header row
        header = tk.Frame(chat_card, bg=CARD)
        header.pack(fill="x", padx=16, pady=(14, 0))
        tk.Label(
            header,
            text="Chat with your Budget AI",
            bg=CARD,
            fg=TEXT,
            font=("Helvetica Neue", 13, "bold"),
        ).pack(side="left")
        button(header, "Clear Chat", self._clear_chat, color="#6b7280").pack(side="right")

        tk.Frame(chat_card, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(10, 0))

        # Scrollable message area
        msg_frame = tk.Frame(chat_card, bg=CARD)
        msg_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(msg_frame)
        scrollbar.pack(side="right", fill="y")

        self.chat_display = tk.Text(
            msg_frame,
            bg=CARD,
            fg=TEXT,
            font=FONT,
            wrap="word",
            state="disabled",
            bd=0,
            highlightthickness=0,
            padx=16,
            pady=12,
            relief="flat",
            cursor="arrow",
            yscrollcommand=scrollbar.set,
        )
        self.chat_display.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.chat_display.yview)

        self.chat_display.tag_configure("user_label", font=("Helvetica Neue", 9, "bold"), foreground=ACCENT)
        self.chat_display.tag_configure("user_text", font=FONT, foreground=TEXT, lmargin1=24, lmargin2=24)
        self.chat_display.tag_configure("ai_label", font=("Helvetica Neue", 9, "bold"), foreground="#10b981")
        self.chat_display.tag_configure("ai_text", font=FONT, foreground=TEXT, lmargin1=24, lmargin2=24)
        self.chat_display.tag_configure("error_text", font=FONT, foreground="#ef4444", lmargin1=24, lmargin2=24)
        self.chat_display.tag_configure("hint_text", font=("Helvetica Neue", 9), foreground="#9ca3af", lmargin1=24, lmargin2=24)

        # Input area
        tk.Frame(chat_card, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(0, 0))

        input_area = tk.Frame(chat_card, bg=CARD)
        input_area.pack(fill="x", padx=16, pady=(8, 14))

        self.input_field = tk.Text(
            input_area,
            height=3,
            bg="#f3f4f6",
            fg=TEXT,
            font=FONT,
            wrap="word",
            bd=0,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=10,
            pady=8,
            relief="flat",
            insertbackground=TEXT,
        )
        self.input_field.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.input_field.bind("<Return>", self._on_enter)

        self.send_btn = button(input_area, "Send", self._send_message, color=ACCENT)
        self.send_btn.pack(side="right", ipady=8)

        self.status_label = tk.Label(
            chat_card,
            text="",
            bg=CARD,
            fg="#9ca3af",
            font=("Helvetica Neue", 9),
        )
        self.status_label.pack(anchor="w", padx=16, pady=(0, 6))

        self._conversation = []
        self._show_welcome()

    def _show_welcome(self):
        self._append("Budget AI\n", "ai_label")
        self._append(
            "Hello! I'm your personal finance assistant. Ask me anything about your "
            "spending, budgets, or transactions.\n\n"
            "Examples:\n"
            "  • How much have I spent this month?\n"
            "  • Which category am I overspending on?\n"
            "  • Show me my recent transactions\n"
            "  • Am I on track with my food budget?\n\n",
            "ai_text",
        )
        self._append("Tip: Add your Anthropic API key in Settings to start chatting.\n\n", "hint_text")

    def _append(self, text, tag):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", text, tag)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _on_enter(self, event):
        if not (event.state & 0x1):  # Shift not held — send
            self._send_message()
            return "break"

    def _send_message(self):
        text = self.input_field.get("1.0", "end").strip()
        if not text:
            return

        settings = app_settings.read_settings()
        api_key = settings.get("api_key", "").strip()
        if not api_key:
            self._append("Budget AI\n", "ai_label")
            self._append(
                "No API key found. Please go to Settings and enter your Anthropic API key.\n\n",
                "error_text",
            )
            return

        self.input_field.delete("1.0", "end")
        self._append("You\n", "user_label")
        self._append(f"{text}\n\n", "user_text")

        self._conversation.append({"role": "user", "content": text})

        self.send_btn.configure(state="disabled", text="...")
        self.input_field.configure(state="disabled")
        self.status_label.configure(text="Thinking...")

        threading.Thread(target=self._call_api, args=(api_key,), daemon=True).start()

    def _call_api(self, api_key):
        try:
            context = build_financial_context()
            reply = get_chat_response(api_key, list(self._conversation), context)
            self.after(0, self._on_success, reply)
        except Exception as exc:
            self.after(0, self._on_error, str(exc))

    def _on_success(self, reply):
        self._conversation.append({"role": "assistant", "content": reply})
        self._append("Budget AI\n", "ai_label")
        self._append(f"{reply}\n\n", "ai_text")
        self._enable_input()
        self.status_label.configure(text="")

    def _on_error(self, msg):
        if self._conversation and self._conversation[-1]["role"] == "user":
            self._conversation.pop()
        self._append("Budget AI\n", "ai_label")
        self._append(f"Error: {msg}\n\n", "error_text")
        self._enable_input()
        self.status_label.configure(text="")

    def _enable_input(self):
        self.send_btn.configure(state="normal", text="Send")
        self.input_field.configure(state="normal")
        self.input_field.focus_set()

    def _clear_chat(self):
        self._conversation.clear()
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self._show_welcome()

    def load(self):
        pass
