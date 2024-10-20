async def validate_team(players):
    # Проверка на количество игроков (1 вратарь и 6 полевых)
    if len(players) != 7:
        return False, "Неверное количество игроков. Необходимо выбрать 7 игроков."

    # Проверка на количество вратарей
    goalkeeper_count = sum(1 for player in players if player.position == 'goalkeeper')
    if goalkeeper_count != 1:
        return False, "Нужно выбрать ровно одного вратаря."

    # Проверка на то, что в команде не более 2 игроков из одной команды
    team_count = {}
    for player in players:
        team = player.team
        if team not in team_count:
            team_count[team] = 0
        team_count[team] += 1
        if team_count[team] > 2:
            return False, f"В команде слишком много игроков из {team}. Максимум 2 игрока."

    # Используем правильное поле для рейтинга игрока, например 'price' вместо 'rating'
    total_rating = sum(player.price for player in players)
    if total_rating > 46:
        return False, f"Сумма рейтингов команды превышает допустимый лимит. Максимум: 46, ваша команда: {total_rating}."

    # Если все проверки пройдены, команда валидна
    return True, None