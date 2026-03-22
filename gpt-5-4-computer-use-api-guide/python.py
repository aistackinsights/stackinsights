import base64
import time
from playwright.sync_api import sync_playwright
from openai import OpenAI

client = OpenAI()  # Reads OPENAI_API_KEY from environment


def capture_screenshot(page) -> str:
    """Capture page screenshot and return as base64 PNG."""
    png_bytes = page.screenshot(type="png")
    return base64.b64encode(png_bytes).decode("utf-8")


def execute_actions(page, actions: list) -> None:
    """Execute a batch of computer_call actions in order."""
    for action in actions:
        match action.type:
            case "click":
                page.mouse.click(
                    action.x,
                    action.y,
                    button=getattr(action, "button", "left"),
                )
            case "double_click":
                page.mouse.dblclick(action.x, action.y)
            case "scroll":
                page.mouse.move(action.x, action.y)
                page.mouse.wheel(
                    getattr(action, "scrollX", 0),
                    getattr(action, "scrollY", 0),
                )
            case "keypress":
                for key in action.keys:
                    page.keyboard.press(" " if key == "SPACE" else key)
            case "type":
                page.keyboard.type(action.text)
            case "wait":
                time.sleep(2)
            case "screenshot":
                pass  # handled outside
            case _:
                raise ValueError(f"Unknown action type: {action.type}")


def run_computer_agent(task: str, start_url: str) -> str:
    """
    Run a GPT-5.4 computer-use agent against a browser page.
    Returns the model's final text output when the task is complete.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(start_url)

        # Initial request — no screenshot yet, model will request one
        response = client.responses.create(
            model="gpt-5.4",
            tools=[{"type": "computer"}],
            input=task,
        )

        while True:
            # Find computer_call in output, if any
            computer_call = next(
                (item for item in response.output if item.type == "computer_call"),
                None,
            )

            if computer_call is None:
                # Task complete — extract final text message
                final_message = next(
                    (item for item in response.output if item.type == "message"),
                    None,
                )
                browser.close()
                return final_message.content[0].text if final_message else ""

            # Execute the action batch (may include a screenshot-only turn)
            execute_actions(page, computer_call.actions)

            # Capture updated state
            screenshot_b64 = capture_screenshot(page)

            # Feed screenshot back and continue
            response = client.responses.create(
                model="gpt-5.4",
                tools=[{"type": "computer"}],
                previous_response_id=response.id,
                input=[
                    {
                        "type": "computer_call_output",
                        "call_id": computer_call.call_id,
                        "output": {
                            "type": "computer_screenshot",
                            "image_url": f"data:image/png;base64,{screenshot_b64}",
                            "detail": "original",  # Full resolution — up to 10.24M px
                        },
                    }
                ],
            )


# Example usage
if __name__ == "__main__":
    result = run_computer_agent(
        task="Find the top headline on Hacker News and copy its title.",
        start_url="https://news.ycombinator.com/",
    )
    print(result)
