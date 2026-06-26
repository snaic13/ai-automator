from openai import OpenAI
from config import OPENAI_API_KEY, MODEL, MAX_TOKENS

client = OpenAI(api_key=OPENAI_API_KEY)

def automate_task(prompt: str, system_prompt: str = "You are a helpful business automation assistant.") -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=MAX_TOKENS
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    result = automate_task("Summarize the key benefits of AI automation for small businesses in 3 bullet points.")
    print(result)
