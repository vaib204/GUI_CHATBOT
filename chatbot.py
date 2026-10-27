
import tkinter as tk
from tkinter import scrolledtext
from threading import Thread
from queue import Queue, Empty
from ollama import chat


# ================= CONFIGURATION =================

MODEL = "llama3.2:1b"

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are Marvellous Python Tutor, an expert Python teacher. "
        "Explain concepts in simple English. Help beginners debug code "
        "and provide correct Python examples."
    )
}

messages = [SYSTEM_MESSAGE.copy()]
result_queue = Queue()
is_generating = False


# ================= MAIN WINDOW =================

root = tk.Tk()
root.title("Marvellous Python Tutor")
root.geometry("850x650")
root.minsize(600, 450)
root.configure(bg="#171923")

BG = "#171923"
PANEL = "#252A3A"
TEXT = "#FFFFFF"
ACCENT = "#6C63FF"
GREEN = "#63D6A5"


# ================= HEADER =================

header = tk.Frame(root, bg=PANEL, padx=15, pady=12)
header.pack(fill="x")

tk.Label(
    header,
    text="Marvellous Python Tutor",
    font=("Segoe UI", 18, "bold"),
    bg=PANEL,
    fg=TEXT
).pack(side="left")

status = tk.Label(
    header,
    text="Ready",
    font=("Segoe UI", 10),
    bg=PANEL,
    fg=GREEN
)
status.pack(side="right")


# ================= CHAT DISPLAY =================

chat_box = scrolledtext.ScrolledText(
    root,
    wrap=tk.WORD,
    font=("Segoe UI", 11),
    bg=BG,
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat",
    padx=15,
    pady=12,
    state="disabled"
)

chat_box.pack(
    fill="both",
    expand=True,
    padx=12,
    pady=12
)

chat_box.tag_config(
    "user",
    foreground="#A99EFF",
    font=("Segoe UI", 11, "bold")
)

chat_box.tag_config(
    "ai",
    foreground=GREEN,
    font=("Segoe UI", 11, "bold")
)

chat_box.tag_config(
    "body",
    foreground=TEXT,
    font=("Segoe UI", 11)
)


def show_message(sender, message, tag):
    """Display a message in the chat window."""
    chat_box.configure(state="normal")

    chat_box.insert(tk.END, sender + "\n", tag)
    chat_box.insert(tk.END, message + "\n\n", "body")

    chat_box.configure(state="disabled")
    chat_box.see(tk.END)


show_message(
    "Marvellous AI",
    "Welcome! Ask me any Python programming question.",
    "ai"
)


# ================= INPUT PANEL =================

input_panel = tk.Frame(
    root,
    bg=PANEL,
    padx=10,
    pady=10
)

input_panel.pack(
    fill="x",
    padx=12,
    pady=(0, 12)
)


# White background and black text make typing visible.
input_box = tk.Text(
    input_panel,
    height=3,
    wrap=tk.WORD,
    font=("Consolas", 12),
    bg="#FFFFFF",
    fg="#000000",
    insertbackground="#000000",
    selectbackground="#B8D4FF",
    selectforeground="#000000",
    relief="solid",
    bd=1,
    padx=10,
    pady=8,
    undo=True
)

input_box.pack(
    side="left",
    fill="both",
    expand=True,
    padx=(0, 10)
)


# ================= OLLAMA WORKER =================

def ollama_worker(history):
    """Generate an answer without freezing the GUI."""
    try:
        response = chat(
            model=MODEL,
            messages=history
        )

        answer = response.message.content

        result_queue.put(("success", answer))

    except Exception as error:
        result_queue.put(
            ("error", f"{type(error).__name__}: {error}")
        )


# ================= SEND MESSAGE =================

def send_message(event=None):
    global is_generating

    if is_generating:
        return "break"

    question = input_box.get(
        "1.0",
        "end-1c"
    ).strip()

    if not question:
        input_box.focus_set()
        return "break"

    if question.lower() == "exit":
        root.destroy()
        return "break"

    show_message("You", question, "user")

    input_box.delete("1.0", tk.END)

    messages.append({
        "role": "user",
        "content": question
    })

    is_generating = True

    send_button.config(state="disabled")
    clear_button.config(state="disabled")
    input_box.config(state="disabled")

    status.config(
        text="Thinking...",
        fg="#F4C95D"
    )

    # Pass a separate copy of the conversation to the worker.
    history = [item.copy() for item in messages]

    Thread(
        target=ollama_worker,
        args=(history,),
        daemon=True
    ).start()

    return "break"


# ================= CHECK AI RESPONSE =================

def check_results():
    global is_generating

    try:
        while True:
            kind, result = result_queue.get_nowait()

            if kind == "success":
                messages.append({
                    "role": "assistant",
                    "content": result
                })

                show_message(
                    "Marvellous AI",
                    result,
                    "ai"
                )

                status.config(
                    text="Ready",
                    fg=GREEN
                )

            else:
                # Remove the failed question from history.
                if messages and messages[-1]["role"] == "user":
                    messages.pop()

                show_message(
                    "Error",
                    result + "\n\nCheck Ollama and the model.",
                    "ai"
                )

                status.config(
                    text="Error",
                    fg="#FF7777"
                )

            is_generating = False

            send_button.config(state="normal")
            clear_button.config(state="normal")
            input_box.config(state="normal")
            input_box.focus_set()

    except Empty:
        pass

    if root.winfo_exists():
        root.after(100, check_results)


# ================= CLEAR CHAT =================

def clear_chat():
    if is_generating:
        return

    messages.clear()
    messages.append(SYSTEM_MESSAGE.copy())

    chat_box.configure(state="normal")
    chat_box.delete("1.0", tk.END)
    chat_box.configure(state="disabled")

    show_message(
        "Marvellous AI",
        "Chat cleared! Ask a new question.",
        "ai"
    )

    input_box.focus_set()


# ================= BUTTONS =================

send_button = tk.Button(
    input_panel,
    text="Send",
    command=send_message,
    bg=ACCENT,
    fg="#FFFFFF",
    activebackground="#554CE0",
    activeforeground="#FFFFFF",
    font=("Segoe UI", 11, "bold"),
    relief="flat",
    cursor="hand2",
    padx=18,
    pady=10
)

send_button.pack(
    side="right",
    padx=(0, 5)
)


clear_button = tk.Button(
    input_panel,
    text="Clear",
    command=clear_chat,
    bg="#41475A",
    fg="#FFFFFF",
    activebackground="#515970",
    activeforeground="#FFFFFF",
    font=("Segoe UI", 10),
    relief="flat",
    cursor="hand2",
    padx=12,
    pady=10
)

clear_button.pack(
    side="right",
    padx=(0, 8)
)


# ================= KEYBOARD SHORTCUTS =================

# Enter sends the prompt.
input_box.bind("<Return>", send_message)

# Shift + Enter inserts a new line.
input_box.bind(
    "<Shift-Return>",
    lambda event: None
)


# ================= START APPLICATION =================

input_box.focus_set()

root.after(100, check_results)

root.mainloop()
