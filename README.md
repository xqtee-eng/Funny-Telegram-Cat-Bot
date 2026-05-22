# Telegram Text Fun Bot

Telegram-бот на Python без зовнішніх Python-залежностей. Він робить ефекти з текстом: random, mock case, reverse, shuffle, clap, emoji, meme, roast, vaporwave, zalgo, caps/lower/title і обмежений spam окремими повідомленнями.

У проєкті також є Telegram Mini App у папці `mini_app`: маленький веб-інтерфейс, з якого можна вибрати ефект, налаштувати кількість/інтенсивність і відправити результат боту.

## Швидкий Запуск

Відкрий PowerShell у папці проєкту:

```powershell
cd C:\Users\ivan-\Documents\Codex\2026-05-21\new-chat
```

Запусти все однією командою:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_all.ps1
```

Цей скрипт автоматично:

- запускає локальний сайт Mini App на `http://127.0.0.1:8787`
- запускає `localhost.run` HTTPS-тунель
- чекає, поки тунель реально відкриється
- оновлює `TELEGRAM_WEB_APP_URL` у `.env`
- оновлює кнопку Mini App у Telegram
- запускає `bot.py`

Вікно PowerShell треба тримати відкритим, поки бот працює.

## Зупинка

Щоб зупинити бота, сайт і тунель:

```powershell
powershell -ExecutionPolicy Bypass -File .\stop_all.ps1
```

Якщо бот запущений у поточному вікні, `Ctrl+C` зупинить тільки `bot.py`. Для повної зупинки Mini App сервера і тунелю все одно використовуй `stop_all.ps1`.

## Налаштування `.env`

Файл `.env` має містити токен бота:

```env
TELEGRAM_BOT_TOKEN=your_real_token_from_botfather
TELEGRAM_WEB_APP_URL=https://your-public-https-site.example
```

`TELEGRAM_WEB_APP_URL` можна не прописувати вручну для локального запуску. `start_all.ps1` сам отримає новий `localhost.run` URL і запише його через `sync_tunnel_url.py`.

Не публікуй `.env` і не кидай токен у відкриті чати.

## Ручний Запуск

Якщо треба запускати все окремо для дебагу, відкрий кілька PowerShell-вікон у цій папці.

Бот:

```powershell
python bot.py
```

Mini App сервер:

```powershell
python -m http.server 8787 --directory mini_app
```

HTTPS-тунель:

```powershell
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=localhostrun_known_hosts -o ServerAliveInterval=30 -R 80:127.0.0.1:8787 nokey@localhost.run
```

Після запуску тунелю онови кнопку Mini App:

```powershell
python sync_tunnel_url.py
```

Якщо Mini App показує `no tunnel here :(` або `sync_tunnel_url.py` дає `503`, зазвичай протух тунель. Перезапусти тунель і знову виконай:

```powershell
python sync_tunnel_url.py
```

## Mini App

Папка `mini_app` містить статичний сайт:

- `index.html` - структура Mini App
- `styles.css` - стилізація
- `app.js` - логіка ефектів і відправка даних у Telegram

Mini App відправляє дані в бота через `Telegram.WebApp.sendData`. Бот приймає ці дані, застосовує вибраний ефект і надсилає результат у чат.

Для постійного домену краще задеплоїти `mini_app` на нормальний HTTPS-хостинг і прописати URL у `.env`. `localhost.run` підходить для тестів, але його домени тимчасові.

## Команди Бота

Після запуску бот реєструє Telegram command menu. У чаті з ботом почни вводити `/`, і Telegram покаже список команд з описами.

- `/start` - показати список команд
- `/help` - показати список команд
- `/random [кількість]` - випадковий текст
- `/caps <текст>` - великі літери
- `/lower <текст>` - маленькі літери
- `/title <текст>` - кожне слово з великої
- `/mock <текст>` - чергування регістру
- `/reverse <текст>` - текст навпаки
- `/shuffle <текст>` - перемішати слова або літери
- `/clap <текст>` - хлопки між словами
- `/emoji <текст>` - рандомні emoji між словами
- `/vapor <текст>` - vaporwave-стиль
- `/zalgo <текст>` - хаотичні символи над літерами
- `/meme <текст>` - мемний шаблон
- `/roast <текст>` - м'який жарт над текстом
- `/spam <1-50> <текст>` - надіслати текст окремими повідомленнями
- `/app` - показати кнопку відкриття Mini App
- `/cancel` - скасувати команду, яка чекає наступний текст

Команди для текстових ефектів можна використовувати напряму:

```text
/reverse привіт
```

Або надіслати команду без тексту, наприклад `/reverse`, після чого бот попросить текст наступним повідомленням. Також можна відповісти командою на вже надіслане повідомлення.

Якщо просто надіслати боту текст без команди, він застосує випадковий ефект.

## Spam Ліміт

`/spam` надсилає окремі повідомлення, але має ліміт 50 повідомлень, cooldown і паузу між повідомленнями. У групах команду можуть запускати тільки адміни. Це зроблено, щоб бот не перетворювався на інструмент для небажаних розсилок.

## Профіль Бота

Під час старту бот автоматично оновлює slash-меню команд і кнопку Mini App/меню.

Назву, опис і короткий опис краще міняти окремо:

```powershell
python configure_profile.py
```

Не запускай `configure_profile.py` часто: Telegram ставить довгий rate limit на зміну профілю.

Аватарку Bot API не змінює. Її треба поставити вручну через BotFather:

```text
/mybots -> FunnyBot -> Edit Bot -> Edit Botpic
```

## Перевірка

Запуск тестів:

```powershell
python -m unittest
```

Перевірка синтаксису:

```powershell
python -m compileall .
```
