# Создаём варианты фраз из slots и подстроки
def mix(strng_parts, slots):
    # Количество вариантов
    count = len(slots) ** (len(strng_parts) - 1)

    # Для каждого пропуска я создаю счётик, какой slot туджа вставить(его индекс)
    help_list = [0] * (len(strng_parts) - 1)

    # Создаём все вариантры
    for i in range(count):
        # Итоговая фраза
        phrase = ""
        for t_part in range(len(strng_parts) - 1):
            phrase += strng_parts[t_part]
            phrase += slots[help_list[t_part]]
        phrase += strng_parts[-1]

        # Изменяем элементы, которые должны быть на месте пропуска
        for j in range(len(strng_parts) - 1):
            help_list[j] = int(((i + 1) / (len(slots) ** j)) % len(slots))
        yield phrase.lower()


# Создаёт список вариантов, в котором ищем нушу строку
def create_search_data(phrase, slots):
    # Если есть подварианты
    if "{" in phrase and slots:
        """
        Разбиваем нашу строку на массив подстрок. Между элементами списка можно втсавлять slots
        Например, "Я люблю {имя}, и {имя}" = ['Я люблю ', ', и ', '']
        """

        # Массив подстрок
        strng_parts = []
        phrase_splited = phrase.split("{")
        for phrase_part in phrase_splited:
            if "}" in phrase_part:
                strng_parts.append(phrase_part.split("}")[1])
            else:
                strng_parts.append(phrase_part)

        # Проходимся по всем возможным фразам для этого варианта и возвращаем их
        for my_phrase in mix(strng_parts, slots):
            yield my_phrase
    # Если нет подвариантов
    else:
        yield phrase


# Это lazy-search, если в двух местах программы убрать .lower(), будет обычный
def phrase_search(object_list, search_string):
    # Создаю id возможного совпадения
    id = 1
    # Прохожусь по всем объектам
    for obj in object_list:
        # Если строка есть в сгенерированном списке всех вариантов для одного объекта
        if search_string.lower() in create_search_data(obj["phrase"], obj["slots"]):
            return id
        id += 1
    return 0


def main():
    """
        len(object) != 0
        object["id"] > 0
        0 <= len(object["phrase"]) <= 120
        0 <= len(object["slots"]) <= 50
    """
    object = [
        {"id": 1, "phrase": "Hello world!", "slots": []},
        {"id": 2, "phrase": "I wanna {pizza}", "slots": ["pizza", "BBQ", "pasta"]},
        {"id": 3, "phrase": "Give me your power", "slots": ["money", "gun"]}
    ]

    assert phrase_search(object, 'I wanna pasta') == 2
    assert phrase_search(object, 'Give me your power') == 3
    assert phrase_search(object, 'Hello world!') == 1
    assert phrase_search(object, 'I wanna nothing') == 0
    assert phrase_search(object, 'Hello again world!') == 0


if __name__ == "__main__":
    main()
