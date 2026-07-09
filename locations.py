# O'zbekiston viloyatlari va ularning tuman/shaharlari.
# Eslatma: bu ro'yxatni istalgan vaqt tahrirlashingiz mumkin (yangi tuman qo'shish/o'chirish).

REGIONS = {
    "Toshkent shahri": [
        "Bektemir", "Chilonzor", "Mirzo Ulug'bek", "Mirobod", "Olmazor",
        "Sergeli", "Shayxontohur", "Uchtepa", "Yakkasaroy", "Yashnobod",
        "Yunusobod", "Yangihayot",
    ],
    "Toshkent viloyati": [
        "Angren", "Bekobod", "Bo'ka", "Bo'stonliq", "Chinoz", "Qibray",
        "Ohangaron", "Oqqo'rg'on", "Olmaliq", "Parkent", "Piskent",
        "Quyi Chirchiq", "Toshkent tumani", "O'rta Chirchiq",
        "Yuqori Chirchiq", "Yangiyo'l", "Zangiota", "Nurafshon",
    ],
    "Andijon viloyati": [
        "Andijon shahri", "Andijon tumani", "Asaka", "Baliqchi", "Bo'z",
        "Buloqboshi", "Izboskan", "Jalaquduq", "Xo'jaobod", "Qo'rg'ontepa",
        "Marhamat", "Oltinko'l", "Paxtaobod", "Shahrixon", "Ulug'nor", "Xonobod",
    ],
    "Farg'ona viloyati": [
        "Farg'ona shahri", "Farg'ona tumani", "Beshariq", "Bog'dod", "Buvayda",
        "Dang'ara", "Furqat", "Qo'shtepa", "Quva", "Quvasoy", "Marg'ilon",
        "Oltiariq", "Rishton", "So'x", "Toshloq", "Uchko'prik",
        "O'zbekiston tumani", "Yozyovon",
    ],
    "Namangan viloyati": [
        "Namangan shahri", "Namangan tumani", "Chortoq", "Chust", "Kosonsoy",
        "Mingbuloq", "Norin", "Pop", "To'raqo'rg'on", "Uychi", "Uchqo'rg'on",
        "Yangiqo'rg'on",
    ],
    "Sirdaryo viloyati": [
        "Guliston shahri", "Guliston tumani", "Boyovut", "Mirzaobod",
        "Oqoltin", "Sardoba", "Sayxunobod", "Sirdaryo", "Xovos",
        "Yangiyer", "Shirin",
    ],
    "Jizzax viloyati": [
        "Jizzax shahri", "Jizzax tumani", "Arnasoy", "Baxmal", "Do'stlik",
        "Forish", "G'allaorol", "Mirzachul", "Paxtakor", "Yangiobod",
        "Zafarobod", "Zarbdor", "Zomin",
    ],
    "Samarqand viloyati": [
        "Samarqand shahri", "Samarqand tumani", "Bulung'ur", "Ishtixon",
        "Jomboy", "Kattaqo'rg'on", "Qo'shrabot", "Narpay", "Nurobod",
        "Oqdaryo", "Pastdarg'om", "Payariq", "Paxtachi", "Toyloq", "Urgut",
    ],
    "Buxoro viloyati": [
        "Buxoro shahri", "Buxoro tumani", "G'ijduvon", "Jondor", "Kogon",
        "Qorako'l", "Qorovulbozor", "Peshku", "Romitan", "Shofirkon",
        "Vobkent", "Olot",
    ],
    "Navoiy viloyati": [
        "Navoiy shahri", "Navbahor", "Karmana", "Konimex", "Qiziltepa",
        "Nurota", "Tomdi", "Uchquduq", "Xatirchi", "Zarafshon",
    ],
    "Qashqadaryo viloyati": [
        "Qarshi shahri", "Qarshi tumani", "Dehqonobod", "G'uzor", "Kasbi",
        "Kitob", "Koson", "Mirishkor", "Muborak", "Nishon", "Qamashi",
        "Shahrisabz", "Chiroqchi", "Yakkabog'",
    ],
    "Surxondaryo viloyati": [
        "Termiz shahri", "Angor", "Bandixon", "Boysun", "Denov",
        "Jarqo'rg'on", "Qiziriq", "Qumqo'rg'on", "Muzrabot", "Oltinsoy",
        "Sariosiyo", "Sherobod", "Sho'rchi", "Uzun",
    ],
    "Xorazm viloyati": [
        "Urganch shahri", "Urganch tumani", "Bog'ot", "Gurlan", "Xazorasp",
        "Xonqa", "Qo'shko'pir", "Shovot", "Yangiariq", "Yangibozor", "Xiva",
    ],
    "Qoraqalpog'iston Respublikasi": [
        "Nukus shahri", "Amudaryo", "Beruniy", "Chimboy", "Ellikqal'a",
        "Kegeyli", "Mo'ynoq", "Nukus tumani", "Qanlikko'l", "Qorao'zak",
        "Qo'ng'irot", "Shumanay", "Taxtako'pir", "Taxiatosh", "To'rtko'l", "Xo'jayli",
    ],
}


def get_regions() -> list:
    return list(REGIONS.keys())


def get_districts(region: str) -> list:
    return REGIONS.get(region, [])
