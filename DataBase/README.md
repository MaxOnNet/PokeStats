
# База данных
По идее Worker должен сам создать структуру БД при первой загрузке, но это не тестировалось.
Тут распологается структура БД, и полный дамп по покемонам, урезаны только секции отвечающие за сканеры.
Так как БД меняется постоянно, и болный дамп коммитить на гитхаб не охота.
Вот ссылки на автоматические дампы.
- [Directory](http://pokestats.tatarnikov.org/database/) Директория с дампами
- [Current Structure](http://pokestats.tatarnikov.org/database/current.structure.sql) Текущая не сжатая структура базы данных
- [Current Data Poke](http://pokestats.tatarnikov.org/database/current.dump.pokemon.sql) Текущий не сжатый дамп покемонов
- [Current Data Poke](http://pokestats.tatarnikov.org/database/current.dump.scanners.sql) Текущий не сжатый дамп настроек сканнеров

# Для запуска надо будет создать
- scanner_location, если координаты оставить в 0, то при запуске адрес переведется в координаты, если координаты установлены, то перевода не будет
- scanner_server, достаточно id
- scanner_account, там все просто, логин\пароль и service[google\ptc]
- scanner, основная рабочая запись, с ссылками на остальные таблицы, поле cd_proxy = NULL, но если прокси нужен, то создаем отметку в scanner_proxy и выставляем id

Для правильной работы надо создать строки в
- scanner_statistic
- scanner_account_statistic
с отпетками и аккаунте и сканере, или же запустить database_structure_check.py в Tools и она создаст их сама