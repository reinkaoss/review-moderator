# import asyncio
# import json
# from playwright.async_api import async_playwright
# from openai import OpenAI
# import time
# import re


# def get_moderation_judgment(text):
#     client = OpenAI(api_key="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")  # Replace with your key

#     try:
#         # Step 1: Create a thread
#         thread = client.beta.threads.create()

#         # Step 2: Add message to thread
#         client.beta.threads.messages.create(
#             thread_id=thread.id,
#             role="user",
#             content=text[:4000]  # Only send visible content
#         )

#         # Step 3: Run the assistant
#         run = client.beta.threads.runs.create(
#             thread_id=thread.id,
#             assistant_id="asst_lGqUAJU0X6XGHrg9BzDuh9CN"
#         )

#         # Step 4: Wait for run to complete
#         while True:
#             run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
#             if run.status in ["completed", "failed", "cancelled"]:
#                 break
#             time.sleep(1)

#         # Step 5: Get the response message
#         messages = client.beta.threads.messages.list(thread_id=thread.id)
#         latest = messages.data[0].content[0].text.value.strip()

#         # # Step 6: Parse it (expecting JSON!)
#         # print("\n--- ASSISTANT RAW OUTPUT ---\n", latest)
#         # cleaned = latest.strip("`").strip()
#         # if cleaned.startswith("json"):
#         #     cleaned = cleaned[4:].strip()
#         # return json.loads(cleaned)

#         print("\n--- ASSISTANT RAW OUTPUT ---\n", latest)

#         json_block = re.search(r'\{.*\}', latest, re.DOTALL)

#         if json_block:
#             try:
#                 return json.loads(json_block.group())
#             except Exception as e:
#                 print("⚠️ Failed to parse JSON block:", e)
#         else:
#             print("⚠️ No JSON found in response.")

#         # Fallback if parsing fails
#         return {
#             "approved": False,
#             "reason": "Unable to parse a valid JSON response from Assistant."
#         }


#     except Exception as e:
#         print("⚠️ Error using Assistant API:", e)
#         return {"approved": False, "reason": "Error retrieving moderation result."}


# # === Main Script ===
# async def moderate_and_highlight(url):
#     async with async_playwright() as p:
#         # browser = await p.chromium.launch(headless=False, args=["--window-size=1280,800"])
#         browser = await p.chromium.launch_persistent_context(
#     user_data_dir="/Users/victor/Library/Application Support/Google/Chrome/Profile 1",  # or Default
#     headless=False,
#     args=["--start-maximized"]
# )

#         page = await browser.new_page()
#         await page.goto(url)

#         # # Extract visible text
#         visible_text = await page.evaluate(r"""
#         () => {
#             const isVisible = el => {
#                 const style = window.getComputedStyle(el);
#                 return style && style.display !== "none" && style.visibility !== "hidden" && el.offsetHeight > 0;
#             };
#             const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
#             let node, textContent = "";
#             while (node = walker.nextNode()) {
#                 if (node.parentElement && isVisible(node.parentElement) && node.nodeValue.trim()) {
#                     textContent += node.nodeValue + "\n";
#                 }
#             }
#             return textContent;
#         }
#         """)


#         # Get moderation result from GPT
#         moderation = get_moderation_judgment(visible_text)
#         print("\n⚠️ Moderation result:", moderation)

#         # Inject verdict popup
#         await page.evaluate(
#             """(moderation) => {
#                 const container = document.createElement("div");
#                 container.style.position = "fixed";
#                 container.style.top = "50%";
#                 container.style.left = "50%";
#                 container.style.transform = "translate(-50%, -50%)";
#                 container.style.background = "white";
#                 container.style.border = "3px solid #222";
#                 container.style.padding = "20px 28px";
#                 container.style.fontFamily = "sans-serif";
#                 container.style.fontSize = "16px";
#                 container.style.color = "black";
#                 container.style.zIndex = "9999";
#                 container.style.boxShadow = "0 6px 16px rgba(0,0,0,0.4)";
#                 container.style.borderRadius = "10px";
#                 container.style.minWidth = "400px";
#                 container.style.textAlign = "center";

#                 const msg = moderation.approved
#                     ? `<strong style='color: green;'>✅ Review approved</strong><p style='margin-top: 8px;'>${moderation.reason}</p>`
#                     : `<strong style='color: red;'>❌ Review rejected</strong><p style='margin-top: 8px;'>${moderation.reason}</p>`;

#                 container.innerHTML = msg;
#                 document.body.appendChild(container);
#             }""",
#             moderation
# )


#         await asyncio.Future()  # Keeps browser open

# # === Run It ===
# # url = "https://www.ratemyplacement.co.uk/control/vue/reviews/185514"
# url = "https://www.ratemyplacement.co.uk/control/vue/reviews/187328"  # Replace with the URL you want to test
# asyncio.run(moderate_and_highlight(url))

import asyncio
import json
import re
import time
from playwright.async_api import async_playwright
from openai import OpenAI

# === OpenAI Assistant Moderation ===
def get_moderation_judgment(text: str) -> dict:
    client = OpenAI(api_key="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")  # Replace with your key")  # ← your key

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
