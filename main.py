from flask import Flask, request
import logging
import json
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
STORAGE = {}
cities = {
    'москва': ['1540737/daa6e420d33102bf6947', '213044/7df73ae4cc715175059e'],
    'нью-йорк': ['1652229/728d5c86707054d4745f', '1030494/aca7ed7acefde2606bdc'],
    'париж': ["1652229/f77136c2364eb90a3ea8", '123494/aca7ed7acefd12e606bdc'],
    'тула': ["1030494/6065a546b333a9d8b15b", '1540737/bff2ff777d7f996478c1'],
    'нижний новгород': ['1652229/98de848e50da51e7e8ea', '997614/91779f90821f39b5f842']
}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'buttons': [],
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    if response['response']['text'] != 'Ну и ладно!':
        response['response']['buttons'] += [{'title': 'Помощь', 'hide': False, 'payload': {'help': True}}]
    logging.info('Response: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        STORAGE[user_id] = {
            'first_name': None,  # здесь будет храниться имя
            'game_started': False  # здесь информация о том, что пользователь начал игру. По умолчанию False
        }
        return
    if user_id in STORAGE:
        if 'guessed_cities' in STORAGE[user_id]:
            if len(STORAGE[user_id]['guessed_cities']) == len(cities):
                res['response']['text'] = 'Ты отгадал все города!'
                res['end_session'] = True
                return
    else:
        STORAGE[user_id] = {
            'first_name': None,  # здесь будет храниться имя
            'game_started': False  # здесь информация о том, что пользователь начал игру. По умолчанию False
        }
    if 'payload' in req['request']:
        if 'help' in req['request']['payload']:
            res['response']['text'] = ''
            if user_id not in STORAGE:
                res['response']['text'] += 'Пожалуйста, напиши своё имя'
                return
            if 'first_name' not in STORAGE[user_id]:
                res['response']['text'] += 'Пожалуйста, напиши своё имя'
                return
            if not STORAGE[user_id]['first_name']:
                res['response']['text'] += 'Пожалуйста, напиши своё имя'
                return
            if "guessed_cities" in STORAGE[user_id]:
                if len(STORAGE[user_id]['guessed_cities']) != 0:
                    res['response'][
                        'text'] = f'Ты уже отгадывал {len(STORAGE[user_id]["guessed_cities"])} из {len(cities.keys())}\n'
                    return
            if not STORAGE[user_id]['game_started']:
                res['response']['text'] += 'Будешь играть дальше?'
                res['response']['buttons'] += [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    }]
                return
            else:
                if len(res['response']['guessed_cities']) == len(cities.keys()):
                    res['response']['text'] += 'Молодец!'
                    return
                elif 'attempt' in STORAGE[user_id]:
                    if STORAGE[user_id]['attempt'] == 1:
                        res['response']['text'] += 'Отгадай город с фотографии'
                        return
                    elif STORAGE[user_id]['attempt'] == 2:
                        res['response'][
                            'text'] += 'Внимательно посмотри на фото и постарайся отгадать город, изображённый на нём'
                        return
                    else:
                        res['response'][
                            'text'] += 'Ничего. Все могут ошибаться'
                        if len(res['response']['guessed_cities']) != len(cities.keys()):
                            res['response'][
                                'text'] += 'Продолжим игру?'
                        else:
                            res['response'][
                                'text'] += 'Города закончились'
        return

    if STORAGE[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            STORAGE[user_id]['first_name'] = first_name
            # создаём пустой массив, в который будем записывать города, которые пользователь уже отгадал
            STORAGE[user_id]['guessed_cities'] = []
            # как видно из предыдущего навыка, сюда мы попали, потому что пользователь написал своем имя.
            # Предлагаем ему сыграть и два варианта ответа "Да" и "Нет".
            res['response']['text'] = f'Приятно познакомиться, {first_name.title()}. Я Алиса. Отгадаешь город по фото?'
            res['response']['buttons'] += [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }
            ]
    else:
        # У нас уже есть имя, и теперь мы ожидаем ответ на предложение сыграть.
        # В sessionStorage[user_id]['game_started'] хранится True или False в зависимости от того,
        # начал пользователь игру или нет.
        if not STORAGE[user_id]['game_started']:
            # игра не начата, значит мы ожидаем ответ на предложение сыграть.
            if 'да' in req['request']['nlu']['tokens']:
                # если пользователь согласен, то проверяем не отгадал ли он уже все города.
                # По схеме можно увидеть, что здесь окажутся и пользователи, которые уже отгадывали города
                if len(STORAGE[user_id]['guessed_cities']) == len(cities.keys()):
                    # если все три города отгаданы, то заканчиваем игру
                    res['response']['text'] = 'Ты отгадал все города!'
                    res['end_session'] = True
                else:
                    # если есть неотгаданные города, то продолжаем игру
                    STORAGE[user_id]['game_started'] = True
                    # номер попытки, чтобы показывать фото по порядку
                    STORAGE[user_id]['attempt'] = 1
                    # функция, которая выбирает город для игры и показывает фото
                    play_game(res, req)
            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ну и ладно!'
                res['end_session'] = True
            else:
                res['response']['text'] = 'Не поняла ответа! Так да или нет?'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    }
                ]
        else:
            play_game(res, req)


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = STORAGE[user_id]['attempt']
    if attempt == 1:
        # если попытка первая, то случайным образом выбираем город для гадания
        city = random.choice(list(cities))
        # выбираем его до тех пор пока не выбираем город, которого нет в sessionStorage[user_id]['guessed_cities']
        while city in STORAGE[user_id]['guessed_cities']:
            city = random.choice(list(cities))
        # записываем город в информацию о пользователе
        STORAGE[user_id]['city'] = city
        # добавляем в ответ картинку
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Что это за город?'
        res['response']['card']['image_id'] = cities[city][attempt - 1]
        res['response']['text'] = 'Тогда сыграем!'
    else:
        # сюда попадаем, если попытка отгадать не первая
        city = STORAGE[user_id]['city']
        # проверяем есть ли правильный ответ в сообщение
        if get_city(req) == city:
            # если да, то добавляем город к sessionStorage[user_id]['guessed_cities'] и
            # отправляем пользователя на второй круг. Обратите внимание на этот шаг на схеме.
            res['response']['text'] = 'Правильно! Сыграем ещё?'
            STORAGE[user_id]['guessed_cities'].append(city)
            STORAGE[user_id]['game_started'] = False
            res['response']['buttons'] += [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }]
            return
        else:
            # если нет
            if attempt == 3:
                # если попытка третья, то значит, что все картинки мы показали.
                # В этом случае говорим ответ пользователю,
                # добавляем город к sessionStorage[user_id]['guessed_cities'] и отправляем его на второй круг.
                # Обратите внимание на этот шаг на схеме.
                res['response']['text'] = f'Вы пытались. Это {city.title()}. Сыграем ещё?'
                STORAGE[user_id]['game_started'] = False
                res['response']['buttons'] += [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    }]
                STORAGE[user_id]['guessed_cities'].append(city)
                return
            else:
                # иначе показываем следующую картинку
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'Неправильно. Вот тебе дополнительное фото'
                res['response']['card']['image_id'] = cities[city][attempt - 1]
                res['response']['text'] = 'А вот и не угадал!'
    # увеличиваем номер попытки доля следующего шага
    STORAGE[user_id]['attempt'] += 1


def get_city(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO, то пытаемся получить город(city), если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('city', None)


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ != '__main__':
    STORAGE = {}
else:
    app.run()
