# Smart Class MVP week plan

Period: 6-13 May 2026.

Goal: finish the critical chain without adding extra product scope:

`authorization -> attendance -> learning module -> AI confidence -> unified events -> first role panels`

## Definition of done by 13 May

- Student can log in and join the active lesson.
- Login creates an attendance event with `user_id`, `lesson_id`, `timestamp`, `status`.
- Textbook module is linked to `lesson_id`.
- Textbook actions are stored as events.
- AI module returns `detected`, `confidence`, `timestamp`, `user_id`, `lesson_id`.
- Low-confidence AI results go to manual review.
- Teacher can confirm, reject or correct attendance.
- Admin/teacher/parent panels consume the same event format.
- Privacy checklist is available for team review.

## Owners

- Руководитель проекта: board control, dependencies, daily review of ЗД-02, ЗД-04, ЗД-05.
- Елизавета: privacy checklist and scenario review.
- Гончарук Иван: AI module and local camera processing.
- Андронов Денис: authorization and attendance.
- Барбарян Арам: manual confirmation UI and role panel wireframes.
- Шилов Тимофей: student learning module entry screen.
- Чередниченко Андрей: lesson-linked textbook actions.
- Головин Егор: activity formula.
- Соколов Лёша: pauses, idle and task sequence tracking.
- Жабин Роман: event dictionary.
- Никита Самыловский: JSON format and integration schema.
