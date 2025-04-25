import asyncio
import json
import re
import time
import dotenv
import os
from playwright.async_api import async_playwright
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# === OpenAI Assistant Moderation ===
def get_moderation_judgment(text: str) -> dict:
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"))

    try:
        # Start a thread with your custom assistant
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=text[:4000]
        )
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id="asst_lGqUAJU0X6XGHrg9BzDuh9CN"
        )

        # Poll until done
        while True:
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status in ("completed", "failed", "cancelled"):
                break
            time.sleep(1)

        # Grab the assistant’s reply
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        latest = messages.data[0].content[0].text.value.strip()
        print("\n--- ASSISTANT RAW OUTPUT ---\n", latest)

        # Extract JSON inside it
        m = re.search(r"\{.*\}", latest, re.DOTALL)
        if m:
            return json.loads(m.group())
        else:
            print("⚠️ No JSON found in assistant response.")
    except Exception as e:
        print("⚠️ Error calling assistant API:", e)

    return {"approved": False, "reason": "Unable to parse moderation result."}


# === Single-Review Flow ===
async def moderate_and_highlight(url: str):
    async with async_playwright() as p:
        # Launch *your* Chrome with profile so you're already logged in
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="/Users/victor/Library/Application Support/Google/Chrome/Default",
            headless=False,
            args=["--start-maximized"],
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        )

        page = browser.pages[0]
        await page.goto(url)

        # 1) Wait for the review container
        await page.wait_for_selector("div.Moderate", timeout=15000)

        # 2) Grab only that text
        visible_text = await page.text_content("div.Moderate")
        if not visible_text or not visible_text.strip():
            print("⚠️ No review content found; aborting.")
        else:
            print("🔍 Extracted review text:\n", visible_text[:200], "…")

            # 3) Send to your assistant
            moderation = get_moderation_judgment(visible_text)
            print("\n⚠️ Moderation result:", moderation)

            # 4) Show a centered popup with the verdict
            await page.evaluate(
                """(mod) => {
                    // Remove any old popup
                    const old = document.getElementById('moderation-popup');
                    if (old) old.remove();

                    const c = document.createElement('div');
                    c.id = 'moderation-popup';
                    Object.assign(c.style, {
                        position: 'fixed',
                        top: '50%', left: '50%',
                        transform: 'translate(-50%, -50%)',
                        background: 'white',
                        border: '3px solid #222',
                        padding: '20px 28px',
                        fontFamily: 'sans-serif',
                        fontSize: '16px',
                        color: 'black',
                        zIndex: '9999',
                        boxShadow: '0 6px 16px rgba(0,0,0,0.4)',
                        borderRadius: '10px',
                        minWidth: '400px',
                        textAlign: 'center'
                    });

                    const msg = mod.approved
                        ? `<strong style='color: green;'>✅ Review approved</strong>
                           <p style='margin-top:8px;'>${mod.reason}</p>`
                        : `<strong style='color: red;'>❌ Review rejected</strong>
                           <p style='margin-top:8px;'>${mod.reason}</p>`;

                    c.innerHTML = msg;
                    document.body.appendChild(c);
                }""",
                moderation
            )

        # 5) Keep the browser open so you can inspect
        await asyncio.Future()


if __name__ == "__main__":
    url = "https://www.ratemyplacement.co.uk/control/vue/reviews/187357"
    asyncio.run(moderate_and_highlight(url))
