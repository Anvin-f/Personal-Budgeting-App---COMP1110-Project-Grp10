import threading
import tkinter as tk

import core.settings as app_settings
from core.chatbot import build_financial_context, get_chat_response

from ..base import Page
from ..constants import ACCENT, BG, BORDER, CARD, FONT, TEXT, FONT_FAMILY
from ..helpers import button, card, page_header


DEFAULT_PROMPT = """Based on the financial data provided, please generate a comprehensive financial summary with three sections:

1. **Spending Habits**: Analyze the user's spending patterns, including what categories they spend the most on, spending trends over time, and overall spending behavior.

2. **Budget Recommendations**: Provide specific budget recommendations for each category based on their spending patterns. Suggest realistic budget amounts that would help them manage their money better.

3. **Ways to Save Money**: Suggest concrete, actionable ways the user can save money based on their current spending habits. Provide specific tips and areas where they could reduce spending.

Format the response clearly with these three sections. Be specific with amounts using HK$ currency."""


class SummaryPage(Page):
    def build(self):
        page_header(self, "📊  Financial Summary")

        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=24, pady=(12, 18))

        # Prompt editor section
        prompt_label = tk.Label(
            main,
            text="✏️  Customize Prompt (Optional)",
            bg=BG,
            fg=TEXT,
            font=(FONT_FAMILY, 11, "bold"),
        )
        prompt_label.pack(anchor="w", pady=(0, 8))

        prompt_card = card(main)
        prompt_card.pack(fill="x", pady=(0, 12))

        # Text area for prompt
        prompt_frame = tk.Frame(prompt_card, bg=CARD)
        prompt_frame.pack(fill="both", expand=False, padx=12, pady=12)

        scrollbar = tk.Scrollbar(prompt_frame)
        scrollbar.pack(side="right", fill="y")

        self.prompt_text = tk.Text(
            prompt_frame,
            bg=CARD,
            fg=TEXT,
            font=(FONT_FAMILY, 9),
            height=6,
            width=80,
            yscrollcommand=scrollbar.set,
            insertbackground=TEXT,
            relief="flat",
            bd=0,
        )
        self.prompt_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.prompt_text.yview)

        # Insert default prompt
        self.prompt_text.insert("1.0", DEFAULT_PROMPT)

        # Buttons for prompt
        button_frame = tk.Frame(prompt_card, bg=CARD)
        button_frame.pack(fill="x", padx=12, pady=(0, 12))

        button(button_frame, "↺  Reset", self._reset_prompt, color="#6b7280").pack(side="left", padx=(0, 8))

        # Summary section header
        header = tk.Frame(main, bg=BG)
        header.pack(fill="x", pady=(12, 12))
        tk.Label(
            header,
            text="Summary Results",
            bg=BG,
            fg=TEXT,
            font=(FONT_FAMILY, 12, "bold"),
        ).pack(side="left")
        self.generate_btn = button(header, "✨  Generate Summary", self._generate_summary, color=ACCENT)
        self.generate_btn.pack(side="right")

        # Summary card
        summary_card = card(main)
        summary_card.pack(fill="both", expand=True)

        # Scrollable content
        scroll_frame = tk.Frame(summary_card, bg=CARD)
        scroll_frame.pack(fill="both", expand=True, padx=16, pady=16)

        scrollbar = tk.Scrollbar(scroll_frame)
        scrollbar.pack(side="right", fill="y")

        canvas = tk.Canvas(
            scroll_frame,
            bg=CARD,
            highlightthickness=0,
            bd=0,
            yscrollcommand=scrollbar.set,
        )
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=canvas.yview)

        self.content_frame = tk.Frame(canvas, bg=CARD)
        self.canvas_window = canvas.create_window(0, 0, window=self.content_frame, anchor="nw")
        canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas = canvas
        self._add_placeholder()

    def _on_canvas_configure(self, event):
        """Update the scroll region when canvas is resized."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # Update canvas window width to match canvas width
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _add_placeholder(self):
        """Add placeholder text."""
        placeholder = tk.Label(
            self.content_frame,
            text="Click 'Generate Summary' to get your personalized financial insights.",
            bg=CARD,
            fg="#9ca3af",
            font=(FONT_FAMILY, 11),
            wraplength=600,
            justify="center",
        )
        placeholder.pack(pady=40)

    def _reset_prompt(self):
        """Reset prompt to default."""
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", DEFAULT_PROMPT)

    def _clear_content(self):
        """Clear all content from the frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _add_section(self, title, content):
        """Add a section with title and content."""
        section = tk.Frame(self.content_frame, bg=CARD)
        section.pack(fill="x", pady=(0, 16))

        # Section title
        title_label = tk.Label(
            section,
            text=title,
            bg=CARD,
            fg=ACCENT,
            font=(FONT_FAMILY, 11, "bold"),
        )
        title_label.pack(anchor="w", pady=(0, 8))

        # Section content
        content_label = tk.Label(
            section,
            text=content,
            bg=CARD,
            fg=TEXT,
            font=FONT,
            justify="left",
            wraplength=600,
        )
        content_label.pack(anchor="w", fill="x")

        # Divider
        tk.Frame(section, bg=BORDER, height=1).pack(fill="x", pady=(8, 0))

    def _generate_summary(self):
        """Generate AI summary."""
        self.generate_btn.configure(state="disabled")
        self._clear_content()

        # Show loading state
        loading = tk.Label(
            self.content_frame,
            text="🔄  Generating your financial summary...",
            bg=CARD,
            fg="#9ca3af",
            font=(FONT_FAMILY, 11),
        )
        loading.pack(pady=40)

        # Generate summary in background thread
        threading.Thread(target=self._fetch_summary, daemon=True).start()

    def _fetch_summary(self):
        """Fetch summary from AI in background."""
        try:
            settings = app_settings.read_settings()
            api_key = settings.get("api_key", "").strip()

            if not api_key:
                self.after(
                    0,
                    self._show_error,
                    "No API key found. Please go to Settings and enter your Anthropic API key.",
                )
                return

            context = build_financial_context()

            # Get custom prompt from text area
            custom_prompt = self.prompt_text.get("1.0", "end").strip()
            if not custom_prompt:
                custom_prompt = DEFAULT_PROMPT

            messages = [{"role": "user", "content": custom_prompt}]
            reply = get_chat_response(api_key, messages, context)

            self.after(0, self._display_summary, reply)

        except Exception as exc:
            self.after(0, self._show_error, f"Error generating summary: {str(exc)}")

    def _display_summary(self, summary_text):
        """Display the generated summary."""
        self._clear_content()

        # Parse the summary into sections if it contains markers
        sections = self._parse_summary(summary_text)

        if sections:
            for title, content in sections:
                self._add_section(title, content)
        else:
            # If parsing fails, just display the full text
            self._add_section("Financial Summary", summary_text)

        self.generate_btn.configure(state="normal")
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _parse_summary(self, text):
        """Parse summary text into sections."""
        sections = []

        # Try to extract sections marked with ** or similar markers
        if "Spending Habits" in text:
            spending_start = text.find("Spending Habits")
            spending_end = text.find("Budget Recommendations", spending_start)
            if spending_end == -1:
                spending_end = len(text)
            spending_content = text[spending_start:spending_end].replace("**Spending Habits**", "").replace("*Spending Habits*", "").strip()
            if spending_content:
                sections.append(("💰 Spending Habits", spending_content))

        if "Budget Recommendations" in text:
            budget_start = text.find("Budget Recommendations")
            budget_end = text.find("Ways to Save Money", budget_start)
            if budget_end == -1:
                budget_end = len(text)
            budget_content = text[budget_start:budget_end].replace("**Budget Recommendations**", "").replace("*Budget Recommendations*", "").strip()
            if budget_content:
                sections.append(("📈 Budget Recommendations", budget_content))

        if "Ways to Save Money" in text:
            save_start = text.find("Ways to Save Money")
            save_content = text[save_start:].replace("**Ways to Save Money**", "").replace("*Ways to Save Money*", "").strip()
            if save_content:
                sections.append(("💡 Ways to Save Money", save_content))

        return sections if sections else []

    def _show_error(self, error_msg):
        """Show error message."""
        self._clear_content()

        error_label = tk.Label(
            self.content_frame,
            text=f"❌ {error_msg}",
            bg=CARD,
            fg="#ef4444",
            font=(FONT_FAMILY, 11),
            wraplength=600,
            justify="center",
        )
        error_label.pack(pady=40)

        self.generate_btn.configure(state="normal")
