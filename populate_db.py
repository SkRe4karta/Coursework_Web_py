import sys
import os
from datetime import datetime, timedelta
sys.path.append(r'c:\Users\zelyo\OneDrive\Documents\Учеба\app')
from app import create_app
from app.models import db, User, Room, Booking, BookingParticipant, Notification, AuditLog

app = create_app()
with app.app_context():
    print("Starting database population...")
    
    # 1. Update old test entries made by the user
    # Renaming Room "123" to something professional
    user_room = Room.query.filter_by(name="123").first()
    if user_room:
        user_room.name = "G-110 Неон"
        user_room.location = "1 этаж, каб. 110"
        user_room.equipment = "Маркерная доска, ТВ-экран"
        user_room.description = "Комната для быстрых встреч и командной работы."
        print("Updated user-created Room '123' to 'G-110 Неон'")
        
    # Renaming bookings with single/meaningless letters (like "йц", "кп")
    # Finding booking with ID 7 (or title containing "йц" / "ц")
    b7 = Booking.query.get(7)
    if b7 and (len(b7.title) <= 3 or b7.title in ["йц", "й", "ц"]):
        b7.title = "Планирование спринта: Мобильный кабинет"
        b7.description = "Детальное планирование спринта с командой мобильной разработки."
        print("Updated user-created Booking ID 7 to 'Планирование спринта: Мобильный кабинет'")
        
    b8 = Booking.query.get(8)
    if b8 and (len(b8.title) <= 3 or b8.title in ["кп", "к", "п"]):
        b8.title = "Синхронизация дизайна: Корпоративный портал"
        b8.description = "Обсуждение макетов нового корпоративного портала с дизайнерами и стейкхолдерами."
        print("Updated user-created Booking ID 8 to 'Синхронизация дизайна: Корпоративный портал'")
        
    # Let's ensure active/completed statuses make sense for dates
    # For dates before June 11, 2026, status should be 'completed'
    # For dates after June 11, 2026, status should be 'active'
    now_date = datetime(2026, 6, 11, 17, 0, 0)
    
    # 2. Add rich mockup bookings throughout June 2026
    # Let's define rooms
    rooms = Room.query.all()
    if not rooms:
        print("Error: No rooms found in the DB. Run seeds first.")
        sys.exit(1)
        
    # Let's check existing bookings to avoid adding duplicates
    existing_titles = {b.title for b in Booking.query.all()}
    
    # List of new bookings to inject
    new_bookings = [
        # --- Week 1 (June 1 - June 7) ---
        {
            'user_id': 3,
            'room_name': 'А-101 Байкал',
            'title': 'Ревью архитектуры базы данных',
            'description': 'Обсуждение оптимизации индексов и структуры таблиц.',
            'start_at': datetime(2026, 6, 1, 11, 0),
            'end_at': datetime(2026, 6, 1, 12, 0),
            'status': 'completed'
        },
        {
            'user_id': 2,
            'room_name': 'B-205 Сириус',
            'title': 'Вводный онбординг стажеров',
            'description': 'Знакомство новых стажеров с процессами и инструментами.',
            'start_at': datetime(2026, 6, 2, 10, 0),
            'end_at': datetime(2026, 6, 2, 11, 30),
            'status': 'completed'
        },
        {
            'user_id': 3,
            'room_name': 'C-310 Дельта',
            'title': 'Встреча 1-на-1 (Юлия / Тимлид)',
            'description': 'Регулярная сессия обратной связи.',
            'start_at': datetime(2026, 6, 3, 15, 0),
            'end_at': datetime(2026, 6, 3, 15, 30),
            'status': 'completed'
        },
        {
            'user_id': 1,
            'room_name': 'D-401 Альфа',
            'title': 'Совет директоров: Итоги квартала',
            'description': 'Презентация финансовых отчетов и утверждение бюджета.',
            'start_at': datetime(2026, 6, 4, 14, 0),
            'end_at': datetime(2026, 6, 4, 17, 0),
            'status': 'completed'
        },
        {
            'user_id': 3,
            'room_name': 'E-112 Нева',
            'title': 'Брейншторм: Концепция маркетинга',
            'description': 'Генерация идей для рекламной кампании в соцсетях.',
            'start_at': datetime(2026, 6, 5, 12, 0),
            'end_at': datetime(2026, 6, 5, 13, 0),
            'status': 'completed'
        },
        
        # --- Week 2 (June 8 - June 14) ---
        {
            'user_id': 2,
            'room_name': 'F-220 Орион',
            'title': 'Собеседование QA Engineer',
            'description': 'Техническое собеседование на позицию ведущего тестировщика.',
            'start_at': datetime(2026, 6, 8, 11, 0),
            'end_at': datetime(2026, 6, 8, 12, 0),
            'status': 'completed'
        },
        {
            'user_id': 3,
            'room_name': 'А-101 Байкал',
            'title': 'Стендап мобильной разработки',
            'description': 'Ежедневная планерка по статусу задач.',
            'start_at': datetime(2026, 6, 9, 10, 0),
            'end_at': datetime(2026, 6, 9, 10, 30),
            'status': 'completed'
        },
        {
            'user_id': 2,
            'room_name': 'B-205 Сириус',
            'title': 'Обсуждение интеграции API',
            'description': 'Синхронизация по интеграции платежного шлюза.',
            'start_at': datetime(2026, 6, 9, 16, 0),
            'end_at': datetime(2026, 6, 9, 17, 0),
            'status': 'completed'
        },
        {
            'user_id': 3,
            'room_name': 'C-310 Дельта',
            'title': 'Встреча 1-на-1 (Никита / Тимлид)',
            'description': 'Обсуждение целей на полугодие.',
            'start_at': datetime(2026, 6, 10, 12, 0),
            'end_at': datetime(2026, 6, 10, 12, 30),
            'status': 'completed'
        },
        # (June 11 is today: already has meetings)
        # June 12 (Tomorrow) - Multiple meetings to show "+ еще X"
        {
            'user_id': 3,
            'room_name': 'B-205 Сириус',
            'title': 'Демо-день: Итоги спринта',
            'description': 'Публичная демонстрация готового инкремента продукта.',
            'start_at': datetime(2026, 6, 12, 11, 0),
            'end_at': datetime(2026, 6, 12, 12, 30),
            'status': 'active'
        },
        {
            'user_id': 2,
            'room_name': 'C-310 Дельта',
            'title': 'Обсуждение замечаний безопасности',
            'description': 'Разбор результатов сканирования уязвимостей.',
            'start_at': datetime(2026, 6, 12, 14, 0),
            'end_at': datetime(2026, 6, 12, 15, 0),
            'status': 'active'
        },
        {
            'user_id': 1,
            'room_name': 'E-112 Нева',
            'title': 'Согласование контракта с партнерами',
            'description': 'Звонок с юристами и партнерами для финализации договора.',
            'start_at': datetime(2026, 6, 12, 16, 0),
            'end_at': datetime(2026, 6, 12, 17, 0),
            'status': 'active'
        },
        
        # --- Week 3 (June 15 - June 21) ---
        {
            'user_id': 2,
            'room_name': 'А-101 Байкал',
            'title': 'Собеседование DevOps Engineer',
            'description': 'Собеседование с кандидатом на позицию системного инженера.',
            'start_at': datetime(2026, 6, 15, 13, 0),
            'end_at': datetime(2026, 6, 15, 14, 0),
            'status': 'active'
        },
        {
            'user_id': 3,
            'room_name': 'F-220 Орион',
            'title': 'Планирование спринта аналитики',
            'description': 'Распределение задач по сбору метрик загруженности комнат.',
            'start_at': datetime(2026, 6, 16, 10, 0),
            'end_at': datetime(2026, 6, 16, 11, 30),
            'status': 'active'
        },
        {
            'user_id': 1,
            'room_name': 'D-401 Альфа',
            'title': 'Общее собрание: Развитие компании',
            'description': 'Ежемесячный Town Hall с участием всех сотрудников.',
            'start_at': datetime(2026, 6, 17, 15, 0),
            'end_at': datetime(2026, 6, 17, 16, 30),
            'status': 'active'
        },
        {
            'user_id': 2,
            'room_name': 'E-112 Нева',
            'title': 'Летучка дизайнеров',
            'description': 'Ревью макетов мобильного приложения.',
            'start_at': datetime(2026, 6, 18, 14, 0),
            'end_at': datetime(2026, 6, 18, 15, 0),
            'status': 'active'
        },
        {
            'user_id': 3,
            'room_name': 'C-310 Дельта',
            'title': 'Встреча 1-на-1 (Анна / HR)',
            'description': 'Плановое интервью по удовлетворенности.',
            'start_at': datetime(2026, 6, 19, 11, 0),
            'end_at': datetime(2026, 6, 19, 11, 45),
            'status': 'active'
        },
        {
            'user_id': 2,
            'room_name': 'А-101 Байкал',
            'title': 'Кризисное совещание: Проблема на проде',
            'description': 'Анализ падения сервера авторизации и выработка решений.',
            'start_at': datetime(2026, 6, 15, 10, 0),
            'end_at': datetime(2026, 6, 15, 11, 0),
            'status': 'cancelled' # Cancelled meeting
        },
        
        # --- Week 4 (June 22 - June 28) ---
        {
            'user_id': 3,
            'room_name': 'B-205 Сириус',
            'title': 'Созвон с клиентом: Приемка этапа',
            'description': 'Презентация функционала личного кабинета.',
            'start_at': datetime(2026, 6, 22, 12, 0),
            'end_at': datetime(2026, 6, 22, 13, 0),
            'status': 'active'
        },
        {
            'user_id': 2,
            'room_name': 'C-310 Дельта',
            'title': 'Встреча 1-на-1 (Дмитрий / Лид)',
            'description': 'Обсуждение производительности и планов.',
            'start_at': datetime(2026, 6, 23, 16, 0),
            'end_at': datetime(2026, 6, 23, 16, 30),
            'status': 'active'
        },
        {
            'user_id': 3,
            'room_name': 'А-101 Байкал',
            'title': 'Командный ретро-анализ',
            'description': 'Ретроспектива по итогам релиза новой админ-панели.',
            'start_at': datetime(2026, 6, 24, 11, 0),
            'end_at': datetime(2026, 6, 24, 12, 30),
            'status': 'active'
        },
        {
            'user_id': 1,
            'room_name': 'D-401 Альфа',
            'title': 'Презентация стратегии 2027',
            'description': 'Обсуждение долгосрочных планов компании.',
            'start_at': datetime(2026, 6, 25, 15, 0),
            'end_at': datetime(2026, 6, 25, 17, 0),
            'status': 'active'
        },
        {
            'user_id': 2,
            'room_name': 'E-112 Нева',
            'title': 'Совещание по контент-плану',
            'description': 'Согласование статей для корпоративного блога.',
            'start_at': datetime(2026, 6, 26, 11, 0),
            'end_at': datetime(2026, 6, 26, 12, 0),
            'status': 'active'
        },
        
        # --- Week 5 (June 29 - June 30) ---
        {
            'user_id': 3,
            'room_name': 'B-205 Сириус',
            'title': 'Планирование спринта 15',
            'description': 'Распределение задач разработчиков на следующий цикл.',
            'start_at': datetime(2026, 6, 29, 10, 0),
            'end_at': datetime(2026, 6, 29, 11, 30),
            'status': 'active'
        },
        {
            'user_id': 2,
            'room_name': 'F-220 Орион',
            'title': 'Собеседование Product Owner',
            'description': 'Второй этап собеседования на руководителя продукта.',
            'start_at': datetime(2026, 6, 30, 14, 0),
            'end_at': datetime(2026, 6, 30, 15, 0),
            'status': 'active'
        }
    ]
    
    # Dictionary map room name -> room object
    room_map = {r.name: r for r in rooms}
    
    bookings_added = 0
    for b_info in new_bookings:
        if b_info['title'] in existing_titles:
            continue
            
        target_room = room_map.get(b_info['room_name'])
        if not target_room:
            continue
            
        b = Booking(
            user_id=b_info['user_id'],
            room_id=target_room.id,
            title=b_info['title'],
            description=b_info['description'],
            participants_count=3,
            start_at=b_info['start_at'],
            end_at=b_info['end_at'],
            status=b_info['status']
        )
        db.session.add(b)
        db.session.flush()
        
        # Add participants
        for email, status in [('developer@company.com', 'accepted'), ('manager@company.com', 'accepted'), ('qa@company.com', 'pending')]:
            registered_user = User.query.filter_by(email=email).first()
            p = BookingParticipant(
                booking_id=b.id,
                participant_email=email,
                response_status=status,
                user_id=registered_user.id if registered_user else None
            )
            db.session.add(p)
        
        bookings_added += 1
        
    print(f"Added {bookings_added} new mockup bookings for June 2026.")
    
    # 3. Create rich audit logs to show in the admin dashboard
    audit_logs_count = AuditLog.query.count()
    if audit_logs_count < 10:
        logs_to_add = [
            AuditLog(user_id=1, entity_type='user', entity_id=2, action='grant_rights', details='Granted can_view_audit_logs to user admin@example.com', created_at=now_date - timedelta(days=5)),
            AuditLog(user_id=1, entity_type='room', entity_id=1, action='edit', details='Updated description and capacity for Room А-101 Байкал', created_at=now_date - timedelta(days=4)),
            AuditLog(user_id=3, entity_type='booking', entity_id=1, action='create', details='Created booking "Дейли митинг команды разработки" in Room А-101 Байкал', created_at=now_date - timedelta(days=3)),
            AuditLog(user_id=2, entity_type='booking', entity_id=2, action='create', details='Created booking "Собеседование с кандидатом (React Developer)" in Room B-205 Сириус', created_at=now_date - timedelta(days=2)),
            AuditLog(user_id=2, entity_type='report', entity_id=None, action='export_pdf', details='Generated and exported PDF report for room occupancy metrics', created_at=now_date - timedelta(days=1)),
            AuditLog(user_id=1, entity_type='privilege', entity_id=3, action='edit', details='Revoked can_manage_rooms from user user@example.com', created_at=now_date - timedelta(hours=10)),
            AuditLog(user_id=2, entity_type='booking', entity_id=7, action='create', details='Created booking "Планирование спринта: Мобильный кабинет" in Room G-110 Неон', created_at=now_date - timedelta(hours=8)),
            AuditLog(user_id=3, entity_type='booking', entity_id=8, action='create', details='Created booking "Синхронизация дизайна: Корпоративный портал" in Room D-401 Альфа', created_at=now_date - timedelta(hours=2)),
            AuditLog(user_id=2, entity_type='report', entity_id=None, action='export_csv', details='Exported full CSV reports of bookings history', created_at=now_date - timedelta(minutes=45))
        ]
        for l in logs_to_add:
            db.session.add(l)
        print(f"Added {len(logs_to_add)} sample audit log entries.")
        
    # 4. Create some realistic unread/read notifications for admin and user
    Notification.query.filter_by(user_id=3).delete()
    Notification.query.filter_by(user_id=2).delete()
    
    notifications = [
        # For User (ID 3)
        Notification(user_id=3, message="Добро пожаловать в систему бронирования Peregovorki!", status='read', created_at=now_date - timedelta(days=5)),
        Notification(user_id=3, message="Администратор перевёл комнату 'G-110 Неон' в статус 'Активна'.", status='read', created_at=now_date - timedelta(days=3)),
        Notification(user_id=3, message="Вы были приглашены на встречу 'Демо-день: Итоги спринта' 12.06.2026 в 11:00.", status='unread', created_at=now_date - timedelta(hours=5)),
        Notification(user_id=3, message="Встреча 'Кризисное совещание: Проблема на проде' была отменена организатором.", status='unread', created_at=now_date - timedelta(hours=2)),
        
        # For Admin (ID 2)
        Notification(user_id=2, message="В системе зарегистрирован новый пользователь: user@example.com", status='read', created_at=now_date - timedelta(days=5)),
        Notification(user_id=2, message="Пользователь Главный Администратор (Root) обновил права вашего аккаунта.", status='unread', created_at=now_date - timedelta(days=1)),
        Notification(user_id=2, message="Новый отзыв/отчет об оборудовании в комнате B-205 Сириус.", status='unread', created_at=now_date - timedelta(hours=1))
    ]
    for n in notifications:
        db.session.add(n)
    print("Added unread/read notifications for admin and user.")
    
    db.session.commit()
    print("Database population completed successfully!")
