import asyncio
import json
import re
import time
import dotenv
import os
from playwright.async_api import async_playwright
from openai import OpenAI
from pathlib import Path

# === OpenAI Assistant Moderation ===
def get_moderation_judgment(text):
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    try:
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
        while True:
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status in ["completed", "failed", "cancelled"]:
                break
            time.sleep(1)
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        latest = messages.data[0].content[0].text.value.strip()
        print("\n--- ASSISTANT RAW OUTPUT ---\n", latest)
        match = re.search(r"\{.*\}", latest, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception as e:
                print("⚠️ Failed to parse JSON:", e)
        else:
            print("⚠️ No JSON found in assistant response.")
    except Exception as e:
        print("⚠️ Error calling assistant API:", e)
    return {"approved": False, "reason": "Unable to parse moderation result."}

# === Moderation Flow ===
# async def moderate_all_pending():
#     async with async_playwright() as p:
#         browser = await p.chromium.launch_persistent_context(
#             user_data_dir="/Users/victor/Library/Application Support/Google/Chrome/Default",
#             headless=False,
#             # args=["--start-maximized"],
#             executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
#         )
#         page = browser.pages[0]
#         await page.goto("https://www.ratemyplacement.co.uk/control/vue/reviews/unmoderated")
#         await page.wait_for_selector(".tabulator-row")
async def moderate_all_pending():
    # Dynamically resolve the current user’s Chrome profile path
    chrome_profile = Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "Default"

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(chrome_profile),
            headless=False,
            # args=["--start-maximized"],
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        )
        page = browser.pages[0]
        await page.goto("https://www.ratemyplacement.co.uk/control/vue/reviews/unmoderated")
        await page.wait_for_selector(".tabulator-row")

        total = await page.eval_on_selector(
            ".tabulator-table",
            "el => el.querySelectorAll('.tabulator-row').length"
        )
        print(f"Found {total} pending reviews on the first page.")

        for i in range(total):
            print(f"🔍 Reviewing #{i+1}/{total}")
            selector = f".tabulator-row:nth-child({i+1}) .tabulator-cell[tabulator-field='created'] a.fa-pen"
            pencil = await page.query_selector(selector)
            if not pencil:
                print(f"⚠️ Pencil icon not found for row {i+1}, skipping.")
                continue

            # Navigate into the review page
            await pencil.click()
            await page.wait_for_load_state("domcontentloaded")

            # Extract review text
            # review_text = await page.evaluate(r"""
            # () => {
            #     const isVisible = el => {
            #         const s = window.getComputedStyle(el);
            #         return s.display !== 'none' && s.visibility !== 'hidden' && el.offsetHeight > 0;
            #     };
            #     const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
            #     let node, text = '';
            #     while (node = walker.nextNode()) {
            #         if (node.parentElement && isVisible(node.parentElement) && node.nodeValue.trim()) {
            #             text += node.nodeValue + '\n';
            #         }
            #     }
            #     return text;
            # }
            # """
            # )
                        # Extract review text from the `.Moderate` container
            review_text = await page.text_content("div.Moderate")
            if not review_text or not review_text.strip():
                print(f"⚠️ No review text found for #{i+1}, skipping.")
                await page.go_back()
                await page.wait_for_selector(".tabulator-row")
                continue
            print(f"🔍 Extracted review text for #{i+1}")
            # Get approval decision and reason
            moderation = get_moderation_judgment(review_text)
            print(f"Result for review #{i+1}:", moderation)

            moderation = get_moderation_judgment(review_text)
            print(f"Result for review #{i+1}:", moderation)

            # Inject popup with verdict
            await page.evaluate(
                """(mod) => {
                    const existing = document.getElementById('moderation-popup');
                    if (existing) existing.remove();
                    const c = document.createElement('div');
                    c.id = 'moderation-popup';
                    Object.assign(c.style, {
                        position: 'fixed', top: '50%', left: '50%',
                        transform: 'translate(-50%, -50%)', background: 'white',
                        border: '3px solid #222', padding: '20px 28px',
                        fontFamily: 'sans-serif', fontSize: '16px', color: 'black',
                        zIndex: '9999', boxShadow: '0 6px 16px rgba(0,0,0,0.4)',
                        borderRadius: '10px', minWidth: '400px', textAlign: 'center'
                    });
                    const msg = mod.approved
                        ? `<strong style='color: green;'>✅ Review approved</strong><p style='margin-top:8px;'>${mod.reason}</p>`
                        : `<strong style='color: red;'>❌ Review rejected</strong><p style='margin-top:8px;'>${mod.reason}</p>`;
                    c.innerHTML = msg;
                    document.body.appendChild(c);
                }""",
                moderation
            )

            # If rejected, flag the review and leave a comment
            # if not moderation['approved']:
            #     # Click "Flag Review"
            #     await page.click("a.Button--orangeGhost")
            #     # Wait for textarea to appear and fill it
            #     await page.fill("textarea.Form-textArea", moderation['reason'])
            #     # Save comment
            #     await page.wait_for_selector("button:has-text('Save Comment')")
            #     await page.click("button:has-text('Save Comment')")
            #   else 
            # #     # Click "Approve Review"
            # await page.click("a.Button--green")
            # #     # Wait for confirmation
            # await page.wait_for_selector("button:has-text('Ser Review Live')")
            # await page.click("button:has-text('Ser Review Live')")
    


            # Pause so you can see the popup
            await asyncio.sleep(2)

            # Remove popup before navigating back
            await page.evaluate("""
                (() => {
                    const p = document.getElementById('moderation-popup');
                    if (p) p.remove();
                })();
            """
            )

            # Go back to list and wait for it to re-render
            await page.go_back()
            await page.wait_for_selector(".tabulator-row")

        print("🎉 All pending reviews processed.")
        await asyncio.Future()  # Keep browser open

# === Entry Point ===
if __name__ == '__main__':
    asyncio.run(moderate_all_pending())
