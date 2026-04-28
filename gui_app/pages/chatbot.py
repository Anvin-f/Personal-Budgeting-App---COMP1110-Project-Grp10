import threading
import tkinter as tk

import core.settings as app_settings
from core.chatbot import build_financial_context, get_chat_response

from ..base import Page
from ..constants import ACCENT, BG, BORDER, CARD, FONT, FONT_H, TEXT, FONT_FAMILY
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
        header.pack(fill="x", padx=16, pady=(14, 10))
        tk.Label(
            header,
            text="💬  Chat with your Budget AI",
            bg=CARD,
            fg=TEXT,
            font=(FONT_FAMILY, 13, "bold"),
        ).pack(side="left")
        button(header, "✨  Clear", self._clear_chat, color="#6b7280").pack(side="right")

        tk.Frame(chat_card, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(0, 10))

        # Scrollable message area with canvas for better layout
        msg_container = tk.Frame(chat_card, bg=CARD)
        msg_container.pack(fill="both", expand=True, padx=12, pady=8)

        scrollbar = tk.Scrollbar(msg_container)
        scrollbar.pack(side="right", fill="y")

        canvas = tk.Canvas(
            msg_container,
            bg=CARD,
            highlightthickness=0,
            bd=0,
            yscrollcommand=scrollbar.set,
        )
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=canvas.yview)

        # Frame inside canvas for messages
        self.messages_frame = tk.Frame(canvas, bg=CARD)
        canvas.create_window((0, 0), window=self.messages_frame, anchor="nw", width=canvas.winfo_width())
        
        def on_frame_config(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_config(event):
            canvas.itemconfig(canvas.find_withtag("all")[0] if canvas.find_withtag("all") else None, width=event.width)
        
        self.messages_frame.bind("<Configure>", on_frame_config)
        canvas.bind("<Configure>", on_canvas_config)
        
        self.chat_display = canvas

        # Input area
        tk.Frame(chat_card, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 0))

        input_area = tk.Frame(chat_card, bg=CARD)
        input_area.pack(fill="x", padx=16, pady=(10, 14))

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
            padx=12,
            pady=10,
            relief="flat",
            insertbackground=TEXT,
        )
        self.input_field.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.input_field.bind("<Return>", self._on_enter)

        self.send_btn = button(input_area, "📤", self._send_message, color=ACCENT)
        self.send_btn.pack(side="right", ipady=8)

        self.status_label = tk.Label(
            chat_card,
            text="",
            bg=CARD,
            fg="#9ca3af",
            font=(FONT_FAMILY, 9),
        )
        self.status_label.pack(anchor="w", padx=16, pady=(0, 6))

        self._conversation = []
        self._show_welcome()

    def _show_welcome(self):
        self._add_message(
            "Hello! I'm your personal finance assistant. Ask me anything about your "
            "spending, budgets, or transactions.\n\n"
            "Examples:\n"
            "  • How much have I spent this month?\n"
            "  • Which category am I overspending on?\n"
            "  • Show me my recent transactions\n"
            "  • Am I on track with my food budget?",
            is_user=False,
            is_hint=False
        )
        self._add_hint("Tip: Add your Anthropic API key in Settings to start chatting.")

    def _add_message(self, text, is_user=False, is_hint=False):
        """Add a message bubble to the conversation."""
        msg_bubble = tk.Frame(self.messages_frame, bg=CARD)
        msg_bubble.pack(fill="x", padx=4, pady=4)
        
        # Determine colors based on message type
        if is_hint:
            bg_color = "#f0fdf4"
            text_color = "#6b7280"
            label_color = "#10b981"
            is_user = False
        elif is_user:
            bg_color = "#dbeafe"
            text_color = "#1f2937"
            label_color = ACCENT
        else:
            bg_color = "#f3f4f6"
            text_color = TEXT
            label_color = "#10b981"
        
        # Create bubble container
        bubble = tk.Frame(msg_bubble, bg=bg_color, relief="flat", bd=0)
        if is_user:
            bubble.pack(anchor="e", padx=(40, 4))
        else:
            bubble.pack(anchor="w", padx=(4, 40))
        
        # Message content
        content = tk.Frame(bubble, bg=bg_color)
        content.pack(fill="both", expand=True, padx=12, pady=10)
        
        # Sender label
        sender = "You" if is_user else ("AI Assistant" if not is_hint else "💡 Hint")
        tk.Label(
            content,
            text=sender,
            bg=bg_color,
            fg=label_color,
            font=(FONT_FAMILY, 9, "bold"),
            anchor="w",
        ).pack(fill="x")
        
        # Message text
        tk.Label(
            content,
            text=text,
            bg=bg_color,
            fg=text_color,
            font=FONT,
            justify="left",
            wraplength=500,
            anchor="w",
        ).pack(fill="both", expand=True, padx=(0, 0), pady=(4, 0))
        
        # Scroll to bottom
        self.chat_display.yview_moveto(1.0)

    def _add_hint(self, text):
        """Add a hint message."""
        self._add_message(text, is_user=False, is_hint=True)

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
            self._add_message(
                "No API key found. Please go to Settings and enter your Anthropic API key.",
                is_user=False,
            )
            return

        self.input_field.delete("1.0", "end")
        self._add_message(text, is_user=True)

        self._conversation.append({"role": "user", "content": text})

        self.send_btn.configure(state="disabled", text="⏳")
        self.input_field.configure(state="disabled")
        self.status_label.configure(text="AI is thinking...")

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
        self._add_message(reply, is_user=False)
        self._enable_input()
        self.status_label.configure(text="")

    def _on_error(self, msg):
        if self._conversation and self._conversation[-1]["role"] == "user":
            self._conversation.pop()
        error_message = f"I encountered an error: {msg}"
        self._add_message(error_message, is_user=False)
        self._enable_input()
        self.status_label.configure(text="")

    def _enable_input(self):
        self.send_btn.configure(state="normal", text="📤")
        self.input_field.configure(state="normal")
        self.input_field.focus_set()

    def _clear_chat(self):
        self._conversation.clear()
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        self._show_welcome()

    def load(self):
        pass
