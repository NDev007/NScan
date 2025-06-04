<div align="center">
  <h1>NScan</h1>
  <h2>PortScanner & Hikvision and Dahua cameras Bruteforcer</h2>
  <img src="./nscan.png" alt="banner" />
  <h4>Сделанно с любовью NDev007</h4>
  <h4>https://t.me/developer102</h4>
</div>

## Зависимости
- Python 3.7+
- Windows XP+
- 20 мб+
- 1гб RAM+
- Интернет

## Установка и использование
### 📈 Установка:
```bash
git clone https://github.com/NDev007/NScan.git
pip install -r requirements.txt
```
### 🩵 Использование:
После установки вы должны в файл ranges.txt загрузить диапазоны айпи. Например с сайта https://suip.biz/ru/?act=all-country-ip.

Вы также можете настроить программу через config.py **НО ДЕЛАТЬ ЭТО С ОСТОРОЖНОСТЬЮ, ОЧЕНЬ ЧУВСТВИТЕЛЬНАЯ ЧАСТЬ**.

Для запуска пишем в консоль:
```bash
cd ./NScan
run.bat
``` 
ну либо просто запускайте run.bat

Также у нас доступна функция восстановления прогресса скана портов. Просто вместо run.bat запускаем run_with_recovery.bat

Пароли и логины можно менять в "logins.txt", "passwords.txt" соответственно.

Результат будет в папке results, скриншоты с камер в "picturesHikvision", "snapshots".

## Лицензия
Мы используем [Apache License 2.0](https://github.com/NDev007/NScan/blob/main/LICENSE).

## Чем мы лучше?
 - У нас есть функция восстановления прогресса скана портов
 - Мультитул. Скан портов совмещен с брутфорсером Dahua и Hikvision одновременно.
 - Обновленный, ускоренный, улучшенный код hikvision-bruteforcer.
 - Открытый исходный код
 - Читаемый и доступный для обновлений код

## ❤️ Благодарности
### Отдельные благодарности:
- **MrVinik** и **MVFps**
- **Dahua_Brute_Pass++**
- **hikvision-bruteforcer**

# ‼️ Дисклеймер ‼️
# ⚠️ Информация представлена только для обучения. Автор не отвечает за последствия применения.