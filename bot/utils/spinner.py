import asyncio
from telegram.constants import ParseMode

def create_spinner():
    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    current_steps = []  # List to store completed steps
    current_step = None  # Current step being processed
    update_event = asyncio.Event()

    async def task_loop(msg, stop_event):
        i = 0
        while not stop_event.is_set():
            spinner_char = spinner_frames[i % len(spinner_frames)]

            # Build the display text with completed and current steps
            lines = []
            for step in current_steps:
                lines.append(f"[ * ] {step}")

            if current_step:
                lines.append(f"[ {spinner_char} ] {current_step}")

            full_text = "```\n" + "\n".join(lines) + "\n```"
            await msg.edit_text(full_text, parse_mode=ParseMode.MARKDOWN_V2)

            i += 1
            try:
                await asyncio.wait_for(update_event.wait(), timeout=0.25)
                update_event.clear()
            except asyncio.TimeoutError:
                pass

        # Final display with all steps completed
        lines = []
        for step in current_steps:
            lines.append(f"[ * ] {step}")

        full_text = "```\n" + "\n".join(lines) + "\n```"
        await msg.edit_text(full_text, parse_mode=ParseMode.MARKDOWN_V2)

    def start_step(text: str):
        nonlocal current_step
        current_step = text
        update_event.set()

    def complete_step():
        nonlocal current_step
        if current_step:
            current_steps.append(current_step)
            current_step = None
            update_event.set()

    return task_loop, start_step, complete_step
