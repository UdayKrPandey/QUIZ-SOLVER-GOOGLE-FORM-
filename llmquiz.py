import asyncio
import re
import sys

from openai import AsyncOpenAI
from playwright.async_api import async_playwright


LLM_MODEL_NAME = "gemini-3.5-flash-lite"

LLM_CLIENT = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key="PUT UR whatveaaa like api key",
    timeout=180.0
)


PROFILE_DIR = "./google_form_chrome"


MCQ_SYSTEM_PROMPT = """
You are an extremely accurate quiz solver.

You are solving a PRACTICE quiz.

Read the question and options carefully.

Your ENTIRE response must be:

<answer>EXACT OPTION TEXT</answer>

Rules:
1. Return ONLY one option.
2. Copy the option text exactly as provided.
3. Do not explain.
4. Do not add anything outside <answer> tags.
5. If the question is ambiguous, still choose the most
   defensible option.
"""



MULTI_SELECT_SYSTEM_PROMPT = """
You are an extremely accurate quiz solver.

You are solving a PRACTICE quiz.

This is a multiple-select question.

Your response must contain every correct option.

Format:

<answer>
EXACT OPTION TEXT 1
EXACT OPTION TEXT 2
</answer>

Rules:
1. Return ONLY the correct option texts.
2. One option per line.
3. Copy option text exactly.
4. Do not explain.
"""



async def query_llm(system_prompt, user_prompt, task_type="QUIZ"):

    max_api_retries = 5
    base_wait_time = 10

    for attempt in range(1, max_api_retries + 1):

        try:

            print(
                f"\n[{task_type}] Sending request "
                f"(Attempt {attempt}/{max_api_retries})..."
            )

            response = await LLM_CLIENT.chat.completions.create(

                model=LLM_MODEL_NAME,

                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],

                temperature=0.0,
                max_tokens=500,

                stop=[
                    "<|im_end|>",
                    "<|endoftext|>"
                ],

                stream=True
            )

            full_response = ""

            async for chunk in response:

                if chunk.choices:

                    delta = chunk.choices[0].delta

                    if hasattr(delta, "content") and delta.content:

                        text = delta.content

                        print(text, end="")
                        sys.stdout.flush()

                        full_response += text

            print("\n")

            return full_response.strip()

        except Exception as e:

            error_msg = str(e).lower()

            if (
                "429" in error_msg
                or "rate limit" in error_msg
                or "quota" in error_msg
            ):

                wait_time = base_wait_time * attempt

                print(
                    f"\n[RATE LIMIT] Waiting "
                    f"{wait_time} seconds..."
                )

                await asyncio.sleep(wait_time)

            else:

                print(f"\n[LLM ERROR] {e}")

                await asyncio.sleep(5)

    return ""



def extract_answer(response):

    if not response:
        return ""

    match = re.search(
        r"<answer>(.*?)</answer>",
        response,
        re.IGNORECASE | re.DOTALL
    )

    if match:

        return match.group(1).strip()

    return response.strip()



async def is_google_form(page):

    try:

        url = page.url.lower()

        if "docs.google.com/forms" in url:

            return True

        title = await page.title()

        if "google forms" in title.lower():

            return True

    except:

        pass

    return False



async def find_form_page(context):


    for page in context.pages:

        if await is_google_form(page):

            return page

    return None



async def get_question_blocks(page):

    """
    Google Forms places each individual question inside:

        [role="listitem"]

    Therefore:

        Q1 = listitem 1
        Q2 = listitem 2
        Q3 = listitem 3

    This is the key to handling multiple questions
    on the same Google Forms page.
    """

    items = page.locator(
        '[role="listitem"]'
    )

    count = await items.count()

    question_blocks = []

    for i in range(count):

        item = items.nth(i)

        try:

            if not await item.is_visible():

                continue

            radios = item.locator(
                '[role="radio"]'
            )

            checkboxes = item.locator(
                '[role="checkbox"]'
            )

            radio_count = await radios.count()
            checkbox_count = await checkboxes.count()


            if (
                radio_count == 0
                and checkbox_count == 0
            ):

                continue

            question_blocks.append(item)

        except:

            continue

    return question_blocks



async def get_question_text(question):

    try:

        text = await question.inner_text()

        return text.strip()

    except:

        return ""



async def get_radio_options(question):

    radios = question.locator(
        '[role="radio"]'
    )

    count = await radios.count()

    options = []

    for i in range(count):

        radio = radios.nth(i)

        try:

            if not await radio.is_visible():

                continue

            label = await radio.get_attribute(
                "aria-label"
            )

            if label:

                options.append({
                    "element": radio,
                    "text": label.strip()
                })

        except:

            continue

    return options



async def get_checkbox_options(question):

    boxes = question.locator(
        '[role="checkbox"]'
    )

    count = await boxes.count()

    options = []

    for i in range(count):

        box = boxes.nth(i)

        try:

            if not await box.is_visible():

                continue

            label = await box.get_attribute(
                "aria-label"
            )

            if label:

                options.append({
                    "element": box,
                    "text": label.strip()
                })

        except:

            continue

    return options



async def select_radio(options, answer):

    target = answer.strip().lower()


    for option in options:

        if option["text"].strip().lower() == target:

            await option["element"].click(
                force=True
            )

            return True



    for option in options:

        option_text = option["text"].strip().lower()

        if (
            target in option_text
            or option_text in target
        ):

            await option["element"].click(
                force=True
            )

            return True

    return False



async def select_checkboxes(options, answer):

    answers = [
        x.strip().lower()
        for x in answer.splitlines()
        if x.strip()
    ]

    if not answers:

        return False

    selected = 0

    for option in options:

        option_text = option["text"].strip().lower()

        for target in answers:

            if (
                option_text == target
                or target in option_text
                or option_text in target
            ):

                await option["element"].click(
                    force=True
                )

                print(
                    f"[QUIZ] Selected: "
                    f"{option['text']}"
                )

                selected += 1

                break

    return selected == len(answers)



async def solve_radio_question(
    question,
    question_number
):

    options = await get_radio_options(
        question
    )

    if not options:

        return False


    question_text = await get_question_text(
        question
    )


    print("\n" + "=" * 70)

    print(
        f"[QUESTION {question_number}] "
        f"MULTIPLE CHOICE"
    )

    print("=" * 70)

    print(
        f"\n{question_text}\n"
    )


    option_text = "\n".join(
        f"- {option['text']}"
        for option in options
    )


    user_prompt = f"""
QUESTION:

{question_text}

AVAILABLE OPTIONS:

{option_text}

Return the exact correct option.
"""


    raw_answer = await query_llm(
        MCQ_SYSTEM_PROMPT,
        user_prompt,
        f"QUESTION {question_number}"
    )


    answer = extract_answer(
        raw_answer
    )


    print(
        f"\n[ANSWER] {answer}"
    )


    success = await select_radio(
        options,
        answer
    )


    if success:

        print(
            f"[SUCCESS] Question "
            f"{question_number} answered."
        )

    else:

        print(
            f"[FAILED] Could not match "
            f"answer for question "
            f"{question_number}."
        )


    return success



async def solve_checkbox_question(
    question,
    question_number
):

    options = await get_checkbox_options(
        question
    )

    if not options:

        return False


    question_text = await get_question_text(
        question
    )


    print("\n" + "=" * 70)

    print(
        f"[QUESTION {question_number}] "
        f"MULTIPLE SELECT"
    )

    print("=" * 70)

    print(
        f"\n{question_text}\n"
    )


    option_text = "\n".join(
        f"- {option['text']}"
        for option in options
    )


    user_prompt = f"""
QUESTION:

{question_text}

AVAILABLE OPTIONS:

{option_text}

Return every correct option.
"""


    raw_answer = await query_llm(
        MULTI_SELECT_SYSTEM_PROMPT,
        user_prompt,
        f"QUESTION {question_number}"
    )


    answer = extract_answer(
        raw_answer
    )


    print(
        f"\n[ANSWERS]\n{answer}"
    )


    success = await select_checkboxes(
        options,
        answer
    )


    if success:

        print(
            f"[SUCCESS] Question "
            f"{question_number} answered."
        )

    else:

        print(
            f"[FAILED] Could not match "
            f"answers for question "
            f"{question_number}."
        )


    return success



async def solve_current_page(page):

    question_blocks = await get_question_blocks(
        page
    )


    print("\n" + "=" * 70)

    print(
        f"[PAGE] Found "
        f"{len(question_blocks)} question(s)."
    )

    print("=" * 70)


    if not question_blocks:

        return 0


    solved_count = 0



    for index, question in enumerate(
        question_blocks,
        start=1
    ):

        try:

            radio_options = await get_radio_options(
                question
            )


            if radio_options:

                success = await solve_radio_question(
                    question,
                    index
                )

                if success:

                    solved_count += 1

                await page.wait_for_timeout(
                    500
                )

                continue



            checkbox_options = await get_checkbox_options(
                question
            )


            if checkbox_options:

                success = await solve_checkbox_question(
                    question,
                    index
                )

                if success:

                    solved_count += 1

                await page.wait_for_timeout(
                    500
                )

                continue


        except Exception as e:

            print(
                f"\n[QUESTION ERROR] "
                f"Question {index}: {e}"
            )


    print("\n" + "=" * 70)

    print(
        f"[PAGE COMPLETE] "
        f"Solved {solved_count}/"
        f"{len(question_blocks)} question(s)."
    )

    print("=" * 70)


    return solved_count



async def click_next(page):

    try:

        next_button = page.get_by_role(
            "button",
            name=re.compile(
                r"^Next$",
                re.IGNORECASE
            )
        )


        count = await next_button.count()


        if count == 0:

            return False


        for i in range(count):

            button = next_button.nth(i)


            if not await button.is_visible():

                continue


            print(
                "\n[NAVIGATION] "
                "Clicking NEXT..."
            )


            await button.click(
                force=True
            )



            await page.wait_for_timeout(
                1500
            )


            return True


    except Exception as e:

        print(
            f"\n[NAVIGATION ERROR] {e}"
        )


    return False



async def is_final_submit_page(page):

    try:


        next_button = page.get_by_role(
            "button",
            name=re.compile(
                r"^Next$",
                re.IGNORECASE
            )
        )


        for i in range(
            await next_button.count()
        ):

            if await next_button.nth(i).is_visible():

                return False



        submit_button = page.get_by_role(
            "button",
            name=re.compile(
                r"^Submit$",
                re.IGNORECASE
            )
        )


        for i in range(
            await submit_button.count()
        ):

            if await submit_button.nth(i).is_visible():

                return True


    except:

        pass


    return False



async def main():

    print("=" * 70)
    print("GOOGLE FORMS PRACTICE QUIZ SOLVER")
    print("=" * 70)


    print("""
The browser will open automatically.

1. Open your Google Form in this browser.
2. Go to the FIRST quiz page.
3. Leave it there.
4. The script finds EVERY question on that page.
5. Gemini solves EVERY question.
6. The script selects EVERY answer.
7. The script clicks NEXT.
8. It repeats on the next page.
9. At the final Submit page, it stops.

IMPORTANT:
- Every question on a page is solved.
- Next is automatic.
- Submit is NEVER clicked.
""")



    async with async_playwright() as p:



        browser = await p.chromium.launch_persistent_context(

            user_data_dir=PROFILE_DIR,

            headless=False,

            args=[
                "--disable-blink-features=AutomationControlled"
            ]
        )



        page = await browser.new_page()


        print(
            "\n[SYSTEM] Chromium opened."
        )

        print(
            "[SYSTEM] Open your Google Form in this browser."
        )



        form_page = None


        while form_page is None:

            form_page = await find_form_page(
                browser
            )


            if form_page is None:

                print(
                    "\n[WAITING] "
                    "Waiting for Google Form..."
                )

                await asyncio.sleep(2)



        page = form_page


        await page.bring_to_front()


        print(
            "\n[CONNECTED] "
            "Google Form detected!"
        )


        print(
            f"[URL] {page.url}"
        )



        while True:

            try:

                print("\n\n")

                print("#" * 70)

                print(
                    "# SCANNING CURRENT FORM PAGE"
                )

                print("#" * 70)


                await page.wait_for_timeout(
                    1000
                )



                solved = await solve_current_page(
                    page
                )



                if solved > 0:

                    print(
                        "\n[PAGE] "
                        "All detected questions processed."
                    )



                next_clicked = await click_next(
                    page
                )


                if next_clicked:

                    print(
                        "[NAVIGATION] "
                        "Next page loaded."
                    )


                    continue



                await page.wait_for_timeout(
                    1000
                )


                if await is_final_submit_page(
                    page
                ):

                    print("\n" + "=" * 70)

                    print(
                        "[QUIZ COMPLETE]"
                    )

                    print("=" * 70)


                    print("""
EVERY QUESTION HAS BEEN SOLVED.

The form is now on the final SUBMIT page.

The script will NOT click Submit.

Review all answers in the browser.

When you are satisfied, click Submit yourself.
""")


                    break



                if solved == 0:

                    print("\n" + "=" * 70)

                    print(
                        "[WARNING] "
                        "No supported questions detected."
                    )

                    print("=" * 70)


                    print("""
The page has:

- No supported question
- No Next button
- No final Submit button

The script will stop rather than do
anything unexpected.
""")


                    break



                print(
                    "\n[WARNING] "
                    "Questions were solved, "
                    "but Next was not found."
                )


                break


            except Exception as e:

                print(
                    f"\n[ERROR] {e}"
                )


                choice = await asyncio.to_thread(
                    input,
                    "\nPress ENTER to retry or Q to quit: "
                )


                if choice.strip().lower() == "q":

                    break



        print(
            "\n[SYSTEM] Script stopped."
        )


        print(
            "[SYSTEM] Chromium remains open."
        )


        await asyncio.to_thread(
            input,
            "\nPress ENTER to close Chromium..."
        )


        await browser.close()



if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print(
            "\n[STOP] Script interrupted by user."
        )

    except Exception as e:

        print(
            f"\n[CRITICAL ERROR] {e}"
        )