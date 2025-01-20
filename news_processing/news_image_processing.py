import logging
import os
import asyncio
import random
import time

import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from news_processing.news_API import BingNewsAPI

get_news = BingNewsAPI()

# Шлях до папки для збереження зображень
PATH = os.path.abspath('tmp_pic/')
# print(PATH)
FONT_PATH = os.path.abspath('fonts/Roboto-Regular.ttf')



async def picture_process(pic_url: str, text_to_image: str, need_to_resize: bool = False):
    # Отримуємо ім'я зображення з URL
    image_name = pic_url.split('/')[-1]
    image_save_path = f"{PATH}/{image_name}.jpg"
    output_image_path = f"{PATH}/output_{image_name}.jpg"

    # Якщо немає зображення, використовуємо зображення з котиком
    if 'None' in pic_url or not pic_url:
        pic_url = 'https://cdn2.thecatapi.com/images/YQtmOXP0_.jpg'

    # Завантажуємо зображення
    try:
        await download_image(pic_url, image_save_path)
        print('step 1, Image was downloaded')
    except Exception as e:
        logging.exception('Cant download the picture', exc_info=e)

        # Якщо картинку не вдалося завантажити, генеруємо випадкове зображення з текстом
        create_random_image_with_text(text_to_image, output_image_path)
        logging.warning('Generated random image with text')
        return output_image_path

    if need_to_resize:
        try:
            await resize_and_pad_image_to_square(image_path=image_save_path, output_path=output_image_path)
            print('step 2, Image was resized and padded')
        except Exception as e:
            logging.exception('Cant resize the image', exc_info=e)

    # Додаємо текст на зображення з градієнтом
    try:
        add_text_with_gradient(image_path=image_save_path, text=text_to_image, output_path=output_image_path,
                               font_path=FONT_PATH)
        logging.warning('step 3, Text with gradient was added to the image')
    except Exception as e:
        logging.exception('Cant add text to the image', exc_info=e)

        # Якщо не вдалось додати текст, генеруємо просте зображення з текстом
        create_random_image_with_text(text_to_image, output_image_path)
        logging.warning('Generated random image with text as a fallback')

    return output_image_path


async def download_image(image_url, save_path):
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status == 200:
                async with aiofiles.open(save_path, 'wb') as f:
                    await f.write(await response.read())


def add_text_with_gradient(image_path, text, output_path, font_path='', font_size=24):
    # Завантажуємо зображення
    image_path = os.path.abspath(image_path)
    # print("Image path from ()add_text_with_gradient", image_path)
    try:
        image = Image.open(image_path).convert("RGBA")
        width, height = image.size

        # Створюємо напівпрозорий градієнтний шар
        gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient)
    except Exception as e:
        logging.exception('Cant open image', exc_info=e)

    # Генеруємо градієнт: зверху темний, знизу прозорий
    for i in range(height):
        alpha = int(255 * (1 - (i / height)))  # Зменшення альфа значення знизу вгору
        draw.line([(0, i), (width, i)], fill=(0, 0, 0, alpha))

    # Накладаємо градієнт на зображення
    combined = Image.alpha_composite(image, gradient)

    # Створюємо об'єкт для малювання і додаємо текст
    draw = ImageDraw.Draw(combined)

    try:
        # Завантажуємо шрифт
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        logging.exception('Cant open font file', exc_info=e)

    # Розбиваємо текст на рядки, які помістяться на зображенні
    max_width = width - 20
    lines = []
    words = text.split(' ')
    current_line = ""

    lines = []
    words = text.split('\n')  # Розбиваємо текст на рядки за символом нового рядка

    for paragraph in words:
        current_line = ""
        paragraph_words = paragraph.split(' ')  # Розбиваємо кожен параграф на слова
        for word in paragraph_words:
            test_line = current_line + word + " "
            text_bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            if text_width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "

        if current_line:
            lines.append(current_line)
        lines.append("")  # Додаємо порожній рядок для розділення параграфів

    line_height = font.getbbox("A")[3] + 20  # Висота рядка та відступ між рядками

    # Початкова позиція тексту (зверху і зліва)
    x = 10
    y = 10  # Відступ від верхнього краю

    # Додаємо кожен рядок на зображення
    for line in lines:
        draw.text((x, y), line, font=font, fill="white")
        y += line_height

    # Конвертуємо результат в RGB і зберігаємо
    combined = combined.convert("RGB")
    combined.save(output_path)


def delete_old_files(folder_path, max_age_minutes):
    """
    Видаляє файли в папці, які старіші за вказаний час (в хвилинах).
    """
    current_time = time.time()
    max_age_seconds = max_age_minutes * 60

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        # print("folepath from ()delete_old_files", file_path)

        if os.path.isfile(file_path):
            file_mod_time = os.path.getmtime(file_path)
            file_age_seconds = current_time - file_mod_time

            # Якщо файл старіший за max_age_seconds, видаляємо його
            if file_age_seconds > max_age_seconds:
                try:
                    os.remove(file_path)
                    print(f'Файл {filename} був видалений, оскільки його вік перевищує {max_age_minutes} хвилин.')
                    logging.warning(f'Файл {filename} був видалений, оскільки його вік перевищує {max_age_minutes} хвилин.')
                except Exception as e:
                    logging.exception(f'Помилка при видаленні файлу {filename}:', exc_info=e)
                    print(f'Помилка при видаленні файлу {filename}:', e)


async def resize_and_pad_image_to_square(image_path, output_path):
    # Завантажуємо зображення
    image = Image.open(image_path)
    original_width, original_height = image.size

    # Перевіряємо, чи зображення не квадратне
    if original_width != original_height:
        # Визначаємо, що робити залежно від того, яке вимірювання більше
        if original_width > original_height:
            # Додаємо поля зверху і знизу, щоб зробити його квадратним
            new_size = (original_width, original_width)
            padding = (0, (original_width - original_height) // 2)  # Паддинг рівномірний з обох сторін
        else:
            # Додаємо поля зліва і справа
            new_size = (original_height, original_height)
            padding = ((original_height - original_width) // 2, 0)

        # Створюємо нове квадратне зображення з чорним фоном
        new_image = Image.new("RGB", new_size, "black")

        # Вставляємо оригінальне зображення в центр
        new_image.paste(image, padding)

        # Зберігаємо результат
        new_image.save(output_path)
    else:
        # Якщо зображення вже квадратне, просто зберігаємо його
        image.save(output_path)

#Створюємо випадкове зображення з текстом
def create_random_image_with_text(text, output_path, width=800, height=600):
    # Створюємо порожнє зображення випадкового кольору
    color = tuple(random.randint(100, 255) for _ in range(3))  # Випадковий світлий колір
    image = Image.new('RGB', (width, height), color)

    # Створюємо об'єкт для малювання і додаємо текст
    draw = ImageDraw.Draw(image)
    try:

        font = ImageFont.truetype(FONT_PATH, 40)
    except Exception as e:
        logging.exception('Cant open font file, using default font', exc_info=e)
        font = ImageFont.load_default()

    # Розбиваємо текст на рядки
    lines = []
    words = text.split(' ')
    current_line = ""
    max_width = width - 20

    for word in words:
        test_line = current_line + word + " "
        text_bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        if text_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + " "

    if current_line:
        lines.append(current_line)

    # Додаємо кожен рядок на зображення
    x = 10
    y = 10  # Відступ від верхнього краю
    line_height = font.getbbox("A")[3] + 10  # Висота рядка та відступ між рядками

    for line in lines:
        draw.text((x, y), line, font=font, fill="black")
        y += line_height

    # Зберігаємо зображення
    image.save(output_path)


async def main(topic, channel=None):
    """
    Основна функція для публікації новин в потрібні канали Telegram.
    """
    # Отримуємо новини
    responses = await get_news.main(request=topic, channel=channel, search_type='standart')
    not_image = 'https://cdn2.thecatapi.com/images/YQtmOXP0_.jpg'
    themes_dict: dict = {'themes': responses}
    topic_text = themes_dict['themes'][topic].get('general_text')
    topic_url = themes_dict['themes'][topic].get('url')
    # topic_text = await read_news(content_link=topic_url, general_text=topic_text)
    topic_picture = themes_dict['themes'][topic].get('image_url')
    topic_url = f' <a href="{topic_url}"><b> Джерело </b></a>'


    if 'thecatapi.com' in topic_picture:
        picture_url = topic_picture
    elif 'None' in topic_picture:
        picture_url = not_image
    else:
        picture_url = topic_picture[:-4] + 'Api'


    # Створюємо папку, якщо її немає
    if not os.path.exists(PATH):
        os.makedirs(PATH)

    # Видаляємо файли, старіші 10 хвилин
    delete_old_files(PATH, 10)
    await asyncio.sleep(1)

    # Завантажуємо зображення
    output_image_path = await picture_process(pic_url=picture_url, text_to_image=topic_text)

    return output_image_path, topic_url


if __name__ == '__main__':
    asyncio.run(main(topic='Суслики'))
