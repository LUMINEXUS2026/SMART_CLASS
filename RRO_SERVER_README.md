# EduCam / Smart Class на другом ПК

## Как запустить сервер для РРО

1. На главном ноутбуке откройте PowerShell в папке проекта:

   `C:\Users\User\Documents\New project 2`

2. Запустите:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\start_rro_server.ps1
   ```

3. В окне появятся ссылки. Для этого компьютера:

   `http://127.0.0.1:5000/auth/login`

4. Для другого ПК в той же сети используйте IP главного ноутбука. Сейчас основной адрес:

   `http://192.168.0.101:5000/auth/login`

   Демо-урок:

   `http://192.168.0.101:5000/admin/cameras/classroom-5/demo`

## Логины

- Администратор: `admin@example.com / password`
- Учитель: `teacher1@example.com / password`
- Родитель: `parent1@example.com / password`

## Если другой ПК не открывает ссылку

Проверьте:

1. Оба компьютера подключены к одной сети: роутер, телефонная раздача или кабельная сеть.
2. На главном ноутбуке сервер запущен и в PowerShell видно `Running on http://...:5000`.
3. В Windows Firewall разрешён входящий TCP-порт `5000`.

Команда для администратора Windows:

```powershell
New-NetFirewallRule -DisplayName "Smart Class Demo 5000" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5000
```

## Для РРО без Wi-Fi

Самый простой вариант:

- главный ноутбук и второй ПК подключить к одному роутеру кабелем;
- или подключить оба устройства к раздаче телефона;
- или использовать маленький роутер без интернета, только как локальную сеть.

Интернет для открытия EduCam на втором ПК не нужен, если оба устройства находятся в одной локальной сети.
