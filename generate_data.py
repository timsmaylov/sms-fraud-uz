"""Generates a synthetic dataset of Uzbek and Russian SMS messages.

Real SMS corpora for Uzbekistan are not publicly available, so messages are
assembled from parts modelled on common scam patterns and on ordinary
messages. A scam message is "pretext + call to action"; an ordinary one is a
bank notification, OTP code, reminder or personal chat. Each message keeps the
id of its pretext/kind in the `template` column (shared by the Russian and
Uzbek variants) so that evaluation can hold out whole kinds of messages.
"""
import csv
import random
from pathlib import Path

random.seed(7)

BANKS = ['Uzcard', 'Humo', 'Kapitalbank', 'Hamkorbank', "Ipak Yo'li", 'Agrobank', 'TBC Bank', 'Anorbank']
SHOPS = ['KORZINKA', 'MAKRO', 'HAVAS', 'TEXNOMART', 'EVOS', 'YANDEX GO', 'UZUM MARKET', 'BELLISSIMO']
NAMES = ['Азиз', 'Дильноза', 'Тимур', 'Мадина', 'Бахтиёр', 'Нилуфар', 'Жасур', 'Камила']
NAMES_UZ = ['Aziz', 'Dilnoza', 'Timur', 'Madina', 'Baxtiyor', 'Nilufar', 'Jasur', 'Kamila']
DOMAINS = ['click-bonus.uz', 'payme-uz.top', 'uzcard-verify.com', 'humo-pay.online', 'bank-uz.site',
           'prize-uzb.net', 'my-gov-uz.info', 'mygov-uz.click', 'uz-post.delivery', 'soliq-uz.org']


def card():
    return f'{random.choice(["8600", "9860", "5614"])} **** {random.randint(1000, 9999)}'


def amount():
    return f'{random.randint(1, 900) * 1000:,}'.replace(',', ' ')


def code():
    return str(random.randint(100000, 999999))


def phone():
    ops = ['90', '91', '93', '94', '97', '99', '33', '88']
    return f'+998{random.choice(ops)}{random.randint(1000000, 9999999)}'


def day():
    return f'{random.randint(1, 28):02d}.{random.randint(1, 12):02d}'


def maybe(s, p=0.3):
    return s if random.random() < p else ''


# --- scams -----------------------------------------------------------------

FRAUD_PRETEXT_RU = [
    lambda: f'{random.choice(BANKS)}: ваша карта {card()} заблокирована.',
    lambda: f'Поздравляем! Вы выиграли {amount()} сум в акции {random.choice(BANKS)}.',
    lambda: 'Служба безопасности банка: зафиксирован подозрительный перевод с вашей карты.',
    lambda: f'Мама, у меня проблемы, срочно нужно {amount()} сум, потом объясню.',
    lambda: f'Вам начислена компенсация {amount()} сум от государства.',
    lambda: 'Ваш номер выиграл iPhone 15 в розыгрыше оператора.',
    lambda: f'Ошибочно перевел вам {amount()} сум, верните пожалуйста.',
    lambda: f'Ваша посылка задержана на таможне, пошлина {amount()} сум.',
    lambda: f'Вам одобрен кредит {amount()} сум под 0%.',
    lambda: 'Ваш аккаунт Payme будет удален из-за подозрительной активности.',
    lambda: f'Налоговая: у вас задолженность {amount()} сум, начислен штраф.',
]
FRAUD_PRETEXT_UZ = [
    lambda: f'{random.choice(BANKS)}: kartangiz {card()} bloklandi.',
    lambda: f"Tabriklaymiz! Siz {amount()} so'm yutib oldingiz.",
    lambda: "Bank xavfsizlik xizmati: kartangizdan shubhali o'tkazma aniqlandi.",
    lambda: f"Onajon, muammo bo'ldi, tezda {amount()} so'm kerak, keyin tushuntiraman.",
    lambda: f"Sizga davlat tomonidan {amount()} so'm kompensatsiya ajratildi.",
    lambda: 'Raqamingiz iPhone 15 yutib oldi!',
    lambda: f"Adashib sizga {amount()} so'm o'tkazib yubordim, iltimos qaytaring.",
    lambda: f"Posilkangiz bojxonada ushlandi, to'lov {amount()} so'm.",
    lambda: f"Sizga {amount()} so'm kredit 0% bilan tasdiqlandi.",
    lambda: "Payme akkauntingiz shubhali faollik sababli o'chiriladi.",
    lambda: f"Soliq: sizda {amount()} so'm qarzdorlik bor, jarima qo'llanildi.",
]
FRAUD_ACTION_RU = [
    lambda: f'Перейдите по ссылке {random.choice(DOMAINS)}',
    lambda: f'Подтвердите данные карты на {random.choice(DOMAINS)}',
    lambda: 'Продиктуйте код из SMS оператору.',
    lambda: f'Отправьте код {code()} на номер {phone()}',
    lambda: f'Срочно позвоните {phone()}',
    lambda: f'Переведите на карту {card()}',
    lambda: f'Оформите до завтра: {random.choice(DOMAINS)}',
    lambda: 'Сообщите номер карты и срок действия в ответном SMS.',
]
FRAUD_ACTION_UZ = [
    lambda: f'Havolaga kiring: {random.choice(DOMAINS)}',
    lambda: f"Karta ma'lumotlarini tasdiqlang: {random.choice(DOMAINS)}",
    lambda: 'SMS koddagi raqamlarni operatorga ayting.',
    lambda: f'{code()} kodini {phone()} raqamiga yuboring',
    lambda: f"Zudlik bilan qo'ng'iroq qiling: {phone()}",
    lambda: f"{card()} kartaga o'tkazing",
    lambda: f'Ertagacha rasmiylashtiring: {random.choice(DOMAINS)}',
    lambda: 'Karta raqami va amal qilish muddatini javob SMS da yuboring.',
]

# --- ordinary messages -------------------------------------------------------

LEGIT_RU = [
    lambda: f'{random.choice(BANKS)}: Покупка {amount()} UZS, {random.choice(SHOPS)}. Карта {card()}. Баланс {amount()} UZS',
    lambda: f'Код подтверждения: {code()}. Никому не сообщайте этот код{maybe(", даже сотрудникам банка", .5)}.',
    lambda: f'{random.choice(BANKS)}: Пополнение {amount()} UZS. Карта {card()}',
    lambda: f'Ваш заказ в {random.choice(SHOPS)} {random.choice(["доставлен", "передан курьеру", "собран"])}. Спасибо за покупку!',
    lambda: f'{random.choice(NAMES)}, привет! {random.choice(["Встречаемся в 7 у метро?", "Ты дома?", "Перезвони, когда сможешь", "Купи хлеб по дороге"])}',
    lambda: f'Напоминаем: оплата за интернет {amount()} сум до 25 числа.',
    lambda: f'Добрый день! Занятие {day()} переносится на 10:00, аудитория {random.randint(100, 450)}.',
    lambda: f'Ваша запись к врачу подтверждена на {day()} в {random.randint(9, 17)}:00.',
    lambda: f'{random.choice(NAMES)} перевел вам {amount()} сум. Карта {card()}',
    lambda: random.choice(['Скинь фото домашнего задания, я забыл записать', 'Завтра собрание в 8, не опаздывайте',
                           'С днем рождения! Счастья и здоровья!', 'Я задержусь на полчаса']),
    lambda: f'Ваш баланс {random.randint(1, 90) * 1000} сум. Пакет интернета продлен до {day()}.',
]
LEGIT_UZ = [
    lambda: f'{random.choice(BANKS)}: Xarid {amount()} UZS, {random.choice(SHOPS)}. Karta {card()}. Balans {amount()} UZS',
    lambda: f'Tasdiqlash kodi: {code()}. Kodni hech kimga aytmang{maybe(", hatto bank xodimlariga ham", .5)}.',
    lambda: f"{random.choice(BANKS)}: Hisobingiz {amount()} UZS ga to'ldirildi. Karta {card()}",
    lambda: f"Buyurtmangiz {random.choice(['yetkazildi', 'kuryerga topshirildi', 'tayyor'])}. Xaridingiz uchun rahmat!",
    lambda: f"{random.choice(NAMES_UZ)}, salom! {random.choice(['Ertaga soat 9 da uchrashamizmi?', 'Uydamisan?', 'Vaqting bolsa qongiroq qil', 'Yolda non olib kel'])}",
    lambda: f"Eslatma: internet uchun {amount()} so'm to'lov muddati 25-sana.",
    lambda: f"Dars {day()} kuni soat 10:00 ga ko'chirildi, {random.randint(100, 450)}-xona.",
    lambda: f'Shifokor qabuliga yozilishingiz {day()} soat {random.randint(9, 17)}:00 ga tasdiqlandi.',
    lambda: f"{random.choice(NAMES_UZ)} sizga {amount()} so'm o'tkazdi. Karta {card()}",
    lambda: random.choice(["Uy vazifasini rasmini tashla, yozib olmabman", "Ertaga soat 8 da yig'ilish, kechikmang",
                           "Tug'ilgan kuning bilan! Baxt va salomatlik tilayman!", 'Yarim soatga kechikaman']),
    lambda: f"Balansingiz {random.randint(1, 90) * 1000} so'm. Internet paketi {day()} gacha uzaytirildi.",
]


def fraud_message():
    if random.random() < 0.5:
        i = random.randrange(len(FRAUD_PRETEXT_RU))
        return f'{FRAUD_PRETEXT_RU[i]()} {random.choice(FRAUD_ACTION_RU)()}', f'fraud_{i}'
    i = random.randrange(len(FRAUD_PRETEXT_UZ))
    return f'{FRAUD_PRETEXT_UZ[i]()} {random.choice(FRAUD_ACTION_UZ)()}', f'fraud_{i}'


def legit_message():
    templates = LEGIT_RU if random.random() < 0.5 else LEGIT_UZ
    i = random.randrange(len(templates))
    return templates[i](), f'legit_{i}'


def main(n_per_class=2000):
    rows = [(*fraud_message(), 1) for _ in range(n_per_class)]
    rows += [(*legit_message(), 0) for _ in range(n_per_class)]
    random.shuffle(rows)
    out = Path(__file__).parent / 'data' / 'sms.csv'
    out.parent.mkdir(exist_ok=True)
    with out.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['text', 'template', 'is_fraud'])
        w.writerows(rows)
    print(f'{len(rows)} messages -> {out}')


if __name__ == '__main__':
    main()
