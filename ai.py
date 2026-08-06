import logging
import openai
from config import AI_API_KEY

# It's better to initialize the client once.
if AI_API_KEY and AI_API_KEY != "YOUR_AI_API_KEY_HERE":
    client = openai.AsyncOpenAI(api_key=AI_API_KEY)
else:
    client = None

AI_PROMPT_TEMPLATE = {
    "uz": (
        "Sen tanishuv boti uchun yordamchisan. Foydalanuvchi ma'lumotlariga asoslanib, u uchun qisqa, samimiy va jozibali 'bio' (o'zi haqida ma'lumot) yarat. Bio 2-3 gapdan oshmasin. Javob faqat bio matnidan iborat bo'lsin, sarlavhalarsiz.\n\n"
        "Foydalanuvchi ma'lumotlari:\n"
        "- Ism: {name}\n"
        "- Yosh: {age}\n"
        "- Shahar: {city}\n"
        "- Qiziqishlar: {interests}\n\n"
        "Yaratilgan bio:"
    ),
    "ru": (
        "Ты ассистент для бота знакомств. На основе данных пользователя, создай для него короткое, дружелюбное и привлекательное 'био' (информацию о себе). Био не должно превышать 2-3 предложения. Ответ должен содержать только текст био, без заголовков.\n\n"
        "Данные пользователя:\n"
        "- Имя: {name}\n"
        "- Возраст: {age}\n"
        "- Город: {city}\n"
        "- Интересы: {interests}\n\n"
        "Сгенерированное био:"
    ),
    "en": (
        "You are an assistant for a dating bot. Based on the user's data, create a short, friendly, and engaging 'bio' (about me) for them. The bio should not exceed 2-3 sentences. The response should only contain the bio text, without any titles.\n\n"
        "User data:\n"
        "- Name: {name}\n"
        "- Age: {age}\n"
        "- City: {city}\n"
        "- Interests: {interests}\n\n"
        "Generated bio:"
    ),
}

AI_NOT_CONFIGURED_TEXT = {
    "uz": "Afsuski, AI yordamchisi hozircha sozlanmagan.",
    "ru": "К сожалению, AI-помощник в данный момент не настроен.",
    "en": "Sorry, the AI assistant is not configured at the moment.",
}

AI_QUOTA_ERROR_TEXTS = {
    "uz": "Afsuski, AI xizmatida vaqtinchalik muammo yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring.",
    "ru": "К сожалению, в работе AI-сервиса возникла временная проблема. Пожалуйста, попробуйте позже.",
    "en": "Unfortunately, there was a temporary issue with the AI service. Please try again later.",
}

async def generate_bio_with_ai(user_data: dict, language: str = "uz") -> str | None:
    """Generates a user bio using an AI model based on user data."""
    if not client:
        logging.warning("AI client is not initialized. Check AI_API_KEY.")
        return AI_NOT_CONFIGURED_TEXT.get(language, AI_NOT_CONFIGURED_TEXT["uz"])

    prompt = AI_PROMPT_TEMPLATE.get(language, AI_PROMPT_TEMPLATE["uz"]).format(
        name=user_data.get("name", "N/A"),
        age=user_data.get("age", "N/A"),
        city=user_data.get("city", "N/A"),
        interests=", ".join(user_data.get("interests_names", [])),
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=150,
        )
        generated_bio = response.choices[0].message.content.strip()
        return generated_bio
    except openai.APIStatusError as e:
        if e.status_code == 429:
            logging.error(f"AI bio generation failed due to insufficient quota: {e}")
            return AI_QUOTA_ERROR_TEXTS.get(language, AI_QUOTA_ERROR_TEXTS["uz"])
        logging.error(f"AI bio generation failed with API error: {e}")
        return None
    except Exception as e:
        logging.error(f"AI bio generation failed: {e}")
        return None