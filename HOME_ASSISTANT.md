# Подключение MiLight iBox2 к Home Assistant

Этот туториал показывает, как добавить MiLight iBox2 / MiLight WiFi Box в
Home Assistant через интеграцию **LimitlessLED**.

MiLight, EasyBulb и LimitlessLED используют один и тот же протокол. Для iBox2 обычно
нужны:

```text
version: 6
port: 5987
```

## Что понадобится

* Home Assistant в той же локальной сети, что и MiLight iBox2.
* IP-адрес MiLight iBox2.
* Доступ к файлу `configuration.yaml`.
* Перезапуск Home Assistant после изменения конфигурации.

## 1. Найти IP-адрес iBox2

Варианты:

* посмотреть список клиентов в роутере;
* открыть веб-интерфейс iBox2;
* запустить локальный Python-скрипт из этого проекта:

```powershell
py -3 milight.py
```

Если iBox2 найден, скрипт выведет примерно:

```text
Found iBox2 devices:
  192.168.1.50:5987 (F0:FE:6B:XX:XX:XX)
```

В примерах ниже вместо `192.168.1.50` укажите реальный IP вашего iBox2.

## 2. Добавить интеграцию в Home Assistant

Откройте файл `configuration.yaml` и добавьте блок:

```yaml
light:
  - platform: limitlessled
    bridges:
      - host: 192.168.1.50
        version: 6
        port: 5987
        groups:
          - number: 1
            type: rgbww
            name: MiLight Zone 1
          - number: 2
            type: rgbww
            name: MiLight Zone 2
          - number: 3
            type: rgbww
            name: MiLight Zone 3
          - number: 4
            type: rgbww
            name: MiLight Zone 4
```

Для RGB+CCT/RGBWW ламп обычно подходит:

```yaml
type: rgbww
```

Если лампа другого типа, попробуйте типы из документации Home Assistant LimitlessLED:
`rgbw`, `rgbww`, `white`, `bridge-led`.

## 3. Вариант с группой All / зона 0

В этом проекте по умолчанию используется зона `0`, то есть `all` / все зоны.
В Home Assistant чаще удобнее добавить зоны `1-4` отдельно и объединить их в группу.

Пример группы Home Assistant:

```yaml
light:
  - platform: limitlessled
    bridges:
      - host: 192.168.1.50
        version: 6
        port: 5987
        groups:
          - number: 1
            type: rgbww
            name: MiLight Zone 1
          - number: 2
            type: rgbww
            name: MiLight Zone 2
          - number: 3
            type: rgbww
            name: MiLight Zone 3
          - number: 4
            type: rgbww
            name: MiLight Zone 4

group:
  milight_all:
    name: MiLight All
    entities:
      - light.milight_zone_1
      - light.milight_zone_2
      - light.milight_zone_3
      - light.milight_zone_4
```

Если ваша версия интеграции принимает `number: 0`, можно попробовать отдельную группу:

```yaml
light:
  - platform: limitlessled
    bridges:
      - host: 192.168.1.50
        version: 6
        port: 5987
        groups:
          - number: 0
            type: rgbww
            name: MiLight All
```

Если после перезапуска сущность `MiLight All` не появилась или не работает, используйте
вариант с зонами `1-4` и группой Home Assistant.

## 4. Проверить конфигурацию

В Home Assistant:

```text
Settings -> System -> Repairs -> Check configuration
```

Или через CLI:

```bash
ha core check
```

Если ошибок нет, перезапустите Home Assistant:

```text
Settings -> System -> Restart Home Assistant
```

## 5. Проверить управление

После перезапуска откройте:

```text
Settings -> Devices & services -> Entities
```

Найдите сущности:

```text
light.milight_zone_1
light.milight_zone_2
light.milight_zone_3
light.milight_zone_4
```

Попробуйте включить и выключить лампу из интерфейса Home Assistant.

## 6. Использовать в автоматизациях

Пример автоматизации включения:

```yaml
alias: MiLight on in the evening
trigger:
  - platform: time
    at: "19:00:00"
action:
  - service: light.turn_on
    target:
      entity_id: light.milight_zone_1
    data:
      brightness_pct: 70
mode: single
```

Пример выключения:

```yaml
alias: MiLight off at night
trigger:
  - platform: time
    at: "23:30:00"
action:
  - service: light.turn_off
    target:
      entity_id: light.milight_zone_1
mode: single
```

## 7. Подключить к Алисе или Салюту

После добавления MiLight в Home Assistant можно использовать Home Assistant как мост:

```text
Алиса / Салют
    -> Home Assistant
    -> LimitlessLED
    -> MiLight iBox2
    -> лампа
```

Для Алисы обычно используют интеграцию Яндекс Умного дома с Home Assistant.
Для Салюта нужен мост через поддерживаемую интеграцию Sber, MQTT или отдельный backend.

## Частые проблемы

### iBox2 не найден

Проверьте:

* Home Assistant и iBox2 находятся в одной сети;
* IP-адрес указан правильно;
* iBox2 включен;
* UDP-порт `5987` не блокируется роутером, firewall или VLAN-настройками.

### Команды уходят, но свет не реагирует

Проверьте:

* правильный `type` лампы: `rgbww`, `rgbw`, `white`;
* правильный номер зоны;
* лампа привязана к этой зоне iBox2;
* управление работает из оригинального приложения Mi-Light.

### Работает только одна зона

Проверьте, к каким зонам привязаны лампы. В iBox2 зоны обычно `1-4`, а зона `0`
означает команду для всех зон.

## Полезная ссылка

Официальная документация Home Assistant:

* https://www.home-assistant.io/integrations/limitlessled/
