const tg = window.Telegram?.WebApp;

const input = document.querySelector("#textInput");
const output = document.querySelector("#resultOutput");
const amountInput = document.querySelector("#amountInput");
const amountLabel = document.querySelector("#amountLabel");
const intensityInput = document.querySelector("#intensityInput");
const intensityLabel = document.querySelector("#intensityLabel");
const copyButton = document.querySelector("#copyButton");
const sendButton = document.querySelector("#sendButton");
const randomFillButton = document.querySelector("#randomFillButton");
const activeEffectLabel = document.querySelector("#activeEffectLabel");
const statusLine = document.querySelector("#statusLine");
const effects = Array.from(document.querySelectorAll(".effect[data-action]"));

const SPAM_MAX = 50;
const RANDOM_MAX = 120;

const wordsPool = [
  "капібара", "шаурма", "космос", "клавіатура", "пельмень", "турбо", "желейний",
  "мемний", "піксель", "чайник", "нічний", "генератор", "рандом", "печиво",
  "квест", "нейронка", "борщ", "магічний", "хаос", "ультра", "дивний", "сирник",
  "батон", "драма", "банан", "телепорт", "піжама", "картопля", "пилосос",
  "мікрохвильовка", "вареник", "батискаф", "креветка", "супергерой", "турбобатон",
  "екскаватор", "паляниця", "пончик", "вайб", "шкарпетка", "калькулятор",
  "пиріжок", "каструля", "стікер", "хрумкий", "кринж", "легендарний", "трамвай",
  "бургер", "бульбашка", "лохина", "пульт", "тапок", "понеділок", "дискотека",
  "йогурт", "сковорідка", "сирена", "хмаринка", "фікус", "сарделька", "мемолог",
  "гарбуз", "круасан", "чебурек", "магнітофон", "сюрприз", "завгосп", "кнопкодав",
  "мегафон", "жужик", "супчик", "галактичний", "сосиска", "комбайн", "танцюрист",
  "директор", "шалений", "пранк", "блискавка", "дзвіночок", "інопланетянин",
];

const emojis = ["😂", "🔥", "💀", "🤯", "✨", "🫠", "😎", "🥔", "🚀", "🍕", "🧃", "🪩", "🤌", "📢", "🧀", "🫡"];
const samples = [
  "цей чат зараз вибухне",
  "батон полетів у космос",
  "пельмень натиснув не ту кнопку",
  "нейронка знову щось придумала",
  "каструля просить адмінку",
  "тапок знайшов сенс життя",
  "калькулятор образився на математику",
  "шаурма вийшла на новий рівень",
  "понеділок отримав бан",
];
const memes = [
  "Коли {text}, але батон уже в космосі.",
  "{text}? Звучить як план на 3 ночі і 2 нервові зриви.",
  "POV: ти відкрив чат, а там {text}.",
  "Це не баг, це {text} в режимі турбо.",
  "Якщо життя дало тобі {text}, зроби з цього мем.",
  "У паралельному всесвіті {text} уже стало державною програмою.",
  "Мама: не роби {text}. Я через 5 хвилин: {text}.",
  "Я: сьогодні без пригод. Також я через 10 хвилин: {text}.",
  "Коли хотів нормально, але вийшло {text}.",
  "Адмін пішов на хвилинку, і тут почалось: {text}.",
  "Цей момент, коли {text} звучить занадто переконливо.",
  "Вчора це був жарт, сьогодні це вже {text}.",
  "Не чіпай, це {text}, воно працює на чесному слові.",
  "У підручнику з хаосу перший розділ називається: {text}.",
  "Коли всі мовчать, але {text} вже все пояснило.",
  "Мемологія 101: бачиш {text} - робиш скрін.",
  "Якби цей чат був фільмом, назва була б: {text}.",
  "Ніхто: абсолютно ніхто. Пельмень у кутку: {text}.",
  "Це {text}, але з вайбом генерального плану.",
  "Коли мозок сказав sleep, а руки написали: {text}.",
];
const roasts = [
  "{text}? Це звучить як план, який писали на серветці.",
  "{text} має вайб презентації за 7 хвилин до дедлайну.",
  "{text} настільки впевнене, що навіть калькулятор попросив паузу.",
  "{text} не провал, просто дуже смілива версія хаосу.",
  "{text} зайшло в чат і зробило вигляд, що так і треба.",
  "{text} виглядає як ідея після третьої кави.",
  "{text} має енергію кнопки, яку не треба було натискати.",
  "{text} настільки дивне, що навіть рандом попросив інструкцію.",
  "{text} виглядає як план Б, коли план А був пельмень.",
  "{text} зайшло занадто впевнено для такої кількості хаосу.",
  "{text} звучить як повідомлення, яке треба було стерти, але вже пізно.",
  "{text} - це не помилка, це характер.",
  "{text} настільки мемне, що йому потрібен власний адмін.",
];
const zalgoMarks = ["\u0300", "\u0301", "\u0302", "\u0303", "\u0304", "\u0306", "\u0307", "\u0308", "\u0309", "\u030a", "\u030b", "\u030c"];

let selectedAction = "meme";

function pick(items) {
  return items[Math.floor(Math.random() * items.length)];
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function getAmount() {
  const max = selectedAction === "spam" ? SPAM_MAX : RANDOM_MAX;
  return clamp(Number(amountInput.value) || 1, 1, max);
}

function parts(text) {
  return text.trim().split(/\s+/).filter(Boolean);
}

function shuffle(items) {
  const copy = [...items];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const target = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[target]] = [copy[target], copy[index]];
  }
  return copy;
}

function randomText(count) {
  const words = Array.from({ length: clamp(count, 1, RANDOM_MAX) }, () => pick(wordsPool));
  const sentence = words.join(" ");
  return `${sentence.charAt(0).toUpperCase()}${sentence.slice(1)}.`;
}

function vapor(text) {
  return [...text.trim()]
    .map((char, index, chars) => {
      const code = char.charCodeAt(0);
      if (char === " ") return "\u3000";
      if (code >= 33 && code <= 126) return String.fromCharCode(code + 0xfee0);
      const next = chars[index + 1] || "";
      return /\p{L}|\p{N}/u.test(char) && /\p{L}|\p{N}/u.test(next) ? `${char}\u3000` : char;
    })
    .join("");
}

function zalgo(text, intensity) {
  return [...text.trim().slice(0, 300)]
    .map((char) => {
      if (!char.trim()) return char;
      const marks = Array.from({ length: intensity }, () => pick(zalgoMarks));
      return `${char}${marks.join("")}`;
    })
    .join("");
}

function title(text) {
  return text.replace(/\S+/g, (word) => word[0].toUpperCase() + word.slice(1).toLowerCase());
}

function applyEffect(action, text) {
  const clean = text.trim();
  const amount = getAmount();
  const intensity = clamp(Number(intensityInput.value) || 1, 1, 5);

  if (action === "random") return randomText(amount);
  if (!clean) return "Введи текст.";

  if (action === "caps") return clean.toUpperCase();
  if (action === "lower") return clean.toLowerCase();
  if (action === "title") return title(clean);
  if (action === "mock") {
    let upper = false;
    return [...clean]
      .map((char) => {
        if (!/\p{L}/u.test(char)) return char;
        upper = !upper;
        return upper ? char.toLowerCase() : char.toUpperCase();
      })
      .join("");
  }
  if (action === "reverse") return [...clean].reverse().join("");
  if (action === "shuffle") {
    const textParts = parts(clean);
    if (textParts.length === 1) return shuffle([...textParts[0]]).join("");
    return shuffle(textParts).join(" ");
  }
  if (action === "clap") {
    const textParts = parts(clean);
    if (textParts.length === 1) return [...textParts[0]].join(" 👏 ");
    return textParts.join(" 👏 ");
  }
  if (action === "emoji") {
    return parts(clean)
      .map((word) => `${word} ${Array.from({ length: intensity }, () => pick(emojis)).join("")}`)
      .join(" ");
  }
  if (action === "vapor") return vapor(clean);
  if (action === "zalgo") return zalgo(clean, intensity);
  if (action === "meme") return pick(memes).replaceAll("{text}", clean.slice(0, 160));
  if (action === "roast") return pick(roasts).replaceAll("{text}", clean.slice(0, 160));
  if (action === "spam") return Array.from({ length: amount }, () => clean).join("\n");
  return clean;
}

function updateControls() {
  const amountMax = selectedAction === "spam" ? SPAM_MAX : RANDOM_MAX;
  const usesAmount = selectedAction === "spam" || selectedAction === "random";
  const usesIntensity = selectedAction === "emoji" || selectedAction === "zalgo";

  amountInput.max = String(amountMax);
  amountInput.disabled = !usesAmount;
  amountLabel.textContent = selectedAction === "spam" ? "Messages" : selectedAction === "random" ? "Words" : "Amount";
  if (Number(amountInput.value) > amountMax) amountInput.value = String(amountMax);
  if (selectedAction === "spam" && Number(amountInput.value) < 3) amountInput.value = "3";

  intensityInput.disabled = !usesIntensity;
  intensityLabel.textContent = "Intensity";
  activeEffectLabel.textContent = effects.find((effect) => effect.dataset.action === selectedAction)?.textContent || selectedAction;
}

function render() {
  updateControls();
  output.value = applyEffect(selectedAction, input.value);
  output.textContent = output.value;
}

function sendToBot() {
  statusLine.textContent = "";
  const data = JSON.stringify({
    action: selectedAction,
    text: input.value.trim(),
    count: getAmount(),
    intensity: clamp(Number(intensityInput.value) || 1, 1, 5),
  });

  if (!tg?.sendData) {
    statusLine.textContent = "Відкрий Mini App через кнопку /app у чаті з ботом, щоб Telegram дозволив відправку.";
    return;
  }

  try {
    tg.MainButton?.showProgress?.(false);
    tg.sendData(data);
    statusLine.textContent = "Надіслано. Якщо чат не оновився, відкрий Mini App через /app, а не через нижнє меню.";
    window.setTimeout(() => tg.MainButton?.hideProgress?.(), 1200);
  } catch {
    tg.MainButton?.hideProgress?.();
    statusLine.textContent = "Telegram не прийняв дані. Відкрий Mini App через /app у чаті з ботом.";
    tg.showPopup?.({
      title: "Не вийшло",
      message: "Telegram не прийняв дані. Скопіюй результат або відкрий Mini App через кнопку бота ще раз.",
      buttons: [{ type: "ok" }],
    });
  }
}

effects.forEach((button) => {
  button.addEventListener("click", () => {
    effects.forEach((effect) => effect.classList.remove("is-active"));
    button.classList.add("is-active");
    selectedAction = button.dataset.action;
    render();
    tg?.HapticFeedback?.selectionChanged?.();
  });
});

input.addEventListener("input", render);
amountInput.addEventListener("input", render);
intensityInput.addEventListener("input", render);

copyButton.addEventListener("click", async () => {
  await navigator.clipboard?.writeText(output.value || output.textContent);
  tg?.showPopup?.({ title: "Готово", message: "Скопійовано.", buttons: [{ type: "ok" }] });
});

randomFillButton.addEventListener("click", () => {
  input.value = pick(samples);
  render();
});

sendButton.addEventListener("click", sendToBot);

tg?.ready?.();
tg?.expand?.();
tg?.MainButton?.setText?.("Надіслати боту");
tg?.MainButton?.enable?.();
tg?.MainButton?.show?.();
tg?.MainButton?.onClick?.(sendToBot);

render();
