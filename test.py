import asyncio
from playwright.async_api import async_playwright

async def highlight_and_scroll(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)

        

        # Inject JS: highlight all "Customer" and scroll to first one
        highlight_script = """
        (() => {
            const word = "scheme";
            const regex = new RegExp(word, "gi");
            let matches = [];

            function highlight(node) {
            if (node.nodeType === Node.TEXT_NODE && regex.test(node.nodeValue)) {
                const span = document.createElement("span");
                span.innerHTML = node.nodeValue.replace(regex, match => {
                const mark = document.createElement('mark');
                mark.style.backgroundColor = "yellow";
                mark.style.color = "black";
                mark.textContent = match;
                matches.push(mark);
                return mark.outerHTML;
                });
                const wrapper = document.createElement("span");
                wrapper.innerHTML = span.innerHTML;
                node.parentNode.replaceChild(wrapper, node);
            } else if (node.nodeType === Node.ELEMENT_NODE && node.childNodes) {
                Array.from(node.childNodes).forEach(highlight);
            }
            }

            highlight(document.body);

            let index = 0;
            function scrollToNextMatch() {
            if (matches.length > 0) {
                matches[index].scrollIntoView({ behavior: "smooth", block: "center" });
                index = (index + 1) % matches.length;
                setTimeout(scrollToNextMatch, 1000); // Adjust delay as needed
            }
            }

            if (matches.length > 0) {
            setTimeout(scrollToNextMatch, 500);
            }
        })();
        """

        await page.evaluate(highlight_script)

        print("✅ 'Customer' highlighted and scrolled into view. Browser will remain open.")
        await asyncio.Future()  # Keep it running

# Set your desired URL
url_to_check = "https://www.ratemyplacement.co.uk/placement-review/186915/linklaters/vacation-scheme-student"
asyncio.run(highlight_and_scroll(url_to_check))
