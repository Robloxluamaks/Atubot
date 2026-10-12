# Relay — Discord AutoSender

## Oryginalne wymagania i uzgodnienia
„Zrob mi discorda auto message bot polegajacy na tym \"podajesz token\" i wybierasz channel id i wpisujesz wiadomosc wyslana dodaj tez emoji dodania emoji do wiadomosci pare kanalow”. Język komunikacji i UI: polski.

Pierwszy zakres zatwierdzony przez użytkownika: oficjalny Bot Token, kilka kanałów, wiadomość z emoji, jednorazowa wysyłka; harmonogram i szablony później.

Kolejna prośba: „to teraz dodaj self token oraz rozne ciekawe funkcje”. Użytkownik potwierdził token prywatnego konta, wszystkie zaproponowane funkcje (szablony, grupy kanałów, osobne treści, harmonogram, embedy) oraz „dodaj funkcje max stealth”.
**Granica wdrożenia:** agent jawnie odmówił ukrywania self-bota/obchodzenia wykrywania. Aplikacja pozostaje wyłącznie dla oficjalnych botów. Nie dodano self-tokenów, fałszowania klienta, ukrywania automatyzacji ani obchodzenia limitów Discorda. Zaimplementowano pozostałe funkcje i ochronę prywatności.

## Bieżący stan — 2026-10-12
- MVP i rozbudowa v1.1 zaimplementowane, przetestowane.
- 36/36 testów backendu przeszło; UI bibliotek/edytora i harmonogramu zweryfikowany.
- Nie otrzymano prawdziwego tokenu bota ani testowego kanału. Rzeczywista dostawa na Discord pozostaje niezweryfikowana. Testy sukcesu integracji korzystają z atrap HTTP **MOCKED wyłącznie w testach**. Aplikacja używa rzeczywistego REST Discord.
- Brak otwartych usterek funkcjonalnych w przetestowanym zakresie.

## Architektura
- React 19, React Router, shadcn/ui, lucide, react-markdown + remark-gfm, sonner. Dark dashboard Relay, DM Sans/Outfit/JetBrains Mono.
- FastAPI, httpx, Motor/MongoDB, cryptography Fernet. Wszystkie API pod `/api`.
- Backend `server.py` ładuje `.env` przed modułami. `database.py` tworzy klienta i indeksy TTL/owner/id. Używa wyłącznie MONGO_URL i DB_NAME z pierwotnej konfiguracji.
- Token bieżącego połączenia: tylko pamięć React i pojedynczego żądania serwera; nie localStorage/sessionStorage/logi. Wyjątek: jawna zgoda na szyfrowany zapis kopii tokenu dla konkretnego harmonogramu.
- Prywatna anonimowa przestrzeń: losowe 256-bit cookie `__Host-relay_workspace`, HttpOnly/Secure/Path=/, HMAC-SHA256 w DB, ważność 30 dni. Origin sprawdzany dokładnie na każdej mutacji korzystającej z cookie; CORS z konkretnym APP_ORIGIN.
- Aplikacja ustawia SameSite=Lax. Zewnętrzny podgląd przepisuje nagłówek na SameSite=None; Partitioned. Testy osobno sprawdzają ścisły Lax u źródła i transport podglądu z zachowaniem HttpOnly/Secure/Path=/, brakiem Domain i kontrolą Origin.
- Własność szablonów/grup/harmonogramów zawsze wyprowadzana z sesji, nie danych klienta. Utrata cookie oznacza utratę dostępu; UI ostrzega, by najpierw usunąć aktywne zadania. Wszystkie dane przestrzeni mają TTL.

## Funkcje ukończone
### MVP
- Bot Token z maskowaniem, połączenie przez `/users/@me`, wymagane `bot=true`, rozłączanie, przewodnik konfiguracji.
- 1–10 kanałów: ID 17–20 cyfr, eliminacja duplikatów, zaznaczanie/usuwanie, odczyt nazw po połączeniu. Kanały offline sprawdzane przed wysłaniem.
- Edytor 2000 znaków UTF-16, wyszukiwarka/kategorie emoji, pogrubienie/kursywa/kod, bezpieczny podgląd Markdown.
- Potwierdzenie wysyłki, blokada wielokrotnego kliknięcia, wynik per kanał, link do wiadomości, brak automatycznych ponowień.
- `allowed_mentions.parse=[]`, różne nonce dla kanałów + `enforce_nonce`, obsługa 400/401/403/404/429, timeout i wynik niepewny; zatrzymanie dalszych kanałów po globalnym problemie.
- Historia ostatnich 50 manualnych wysyłek tylko w pamięci karty, ponowne użycie treści, usunięcie historii.

### Rozbudowa v1.1
- `/szablony`: tworzenie, edycja, usuwanie z potwierdzeniem, zastosowanie i szybki wybór. Zachowanie tekstu, embeda i wariantów kanałów. Maks. 100 wpisów.
- `/grupy`: grupy do 10 unikalnych kanałów, CRUD, zastosowanie, zapis zaznaczonych kanałów z edytora, szybki wybór. Maks. 100 wpisów.
- Osobna treść per kanał, przywrócenie wspólnej treści, podgląd przełączany między kanałami. Wysyłane tylko warianty zaznaczonych kanałów.
- Embed: tytuł 256 znaków, opis 4096, stopka 2048, łączny limit 6000 UTF-16; kolor, bezpieczny link HTTP(S). Wysyłka samego embeda dozwolona. Footer przekształcany na obiekt Discord `{text: ...}`.
- `/harmonogram`: jednorazowo lub cyklicznie, lokalna data konwertowana na UTC, odstępy 15/30/60/180/360/720/1440/10080 minut, 1–1000 cykli, limit 30 zadań.
- Planowanie wymaga poprawnego Bot Tokenu, dostępnych kanałów i jawnej zgody checkbox na szyfrowanie/zapis. Token nie wraca w API.
- Pauza/wznowienie/usuwanie, raport ostatniej próby, ponowne użycie treści. Pauza/usunięcie blokuje następne kanały, ale nie odwołuje już wysłanego żądania.
- `/prywatnosc`: termin ważności, zasady retencji, usunięcie całej przestrzeni ze wszystkimi zadaniami i sekretami.
- Brak PostHog/analityki, tokeny wyłączone z logów i błędów walidacji.

## Harmonogram — ważne ograniczenia
- Tylko harmonogram platformowy `.emergent/crons.yml`, jedno zadanie `relay-dispatch`, `*/15 * * * *`.
- Realizacja w pierwszym cyklu po zadanej godzinie (do około 15 min), nie gwarantuje dokładności minutowej. Nie ma lokalnego timera, APScheduler ani pętli w przeglądarce.
- `/api/cron/dispatch`: secret Bearer porównywany stałoczasowo, walidacja envelope, duplikaty run_id ignorowane. Natychmiastowe 2xx, skończone wykonanie w BackgroundTasks.
- `schedule_worker.py`: atomowy claim w Mongo, maks. 20 gotowych zadań na wywołanie, kontrola pauzy/usunięcia przed kanałem, pomijanie zaległych interwałów zamiast serii wysyłek.
- Błędy zatrzymują zadanie. Niepewne wykonanie nie jest automatycznie ponawiane. Stare running >30 min przechodzą w error.
- Po ukończeniu lub 401 zaszyfrowany token jest kasowany; usunięcie zadania i TTL również usuwają go. Przy błędzie z zachowanym tokenem użytkownik może zdecydować o wznowieniu.
- Ważność przestrzeni i zadań maks. 30 dni. Zakończone harmonogramy pozostają jako wyniki bez tokenu do wygaśnięcia/usunięcia.
- Istnieją ograniczenia BackgroundTasks przy restarcie procesu; atomowe stany i zatrzymanie niepewnych zadań ograniczają duplikację, ale nie gwarantują dostawy.

## Modele danych MongoDB
- `sessions`: id UUID, token_hash HMAC, expires_at BSON datetime. Żadnego surowego cookie.
- `templates`: id, owner_id, name, content, embed, overrides, created_at, expires_at.
- `groups`: id, owner_id, name, channels[{id,name}], created_at, expires_at.
- `schedules`: id, owner_id, name, bot_name, channel_ids, draft, next_run, interval_minutes, max_runs, run_count, state, encrypted token_ciphertext, last_results/error/run, run_key, timestamps/expiry.
- `cron_runs`: hash run_id jako klucz idempotencji, created_at, expires_at (7 dni).
- Odpowiedzi danych Mongo mają jawne modele Pydantic i projekcję bez `_id`; sekrety/własność nie są zwracane.

## Główne pliki / API
- `backend/server.py`, `database.py`, `workspace_auth.py`, `message_models.py`, `discord_models.py`, `discord_service.py`, `discord_routes.py`, `library_routes.py`, `schedule_models.py`, `schedule_routes.py`, `schedule_worker.py`, `cron_routes.py`.
- `POST /api/bot/connect`, `/api/channels/resolve`, `/api/messages/send`; `GET /api/health`.
- `POST /api/workspace/session`, `DELETE /api/workspace`.
- Biblioteka: GET/POST `/api/library/templates` i `/groups`, PUT/DELETE po ID.
- Harmonogramy: GET/POST `/api/schedules`, PATCH/DELETE `/{id}`; POST `/api/cron/dispatch`.
- Frontend `context/RelayContext.jsx`, `lib/relay-api.js`, `lib/drafts.js`, `lib/emojis.js`, `components/relay/*`, strony Compose/History/Library/Schedules/Privacy, `App.css`, `features.css`.
- `.env` zachowuje pierwotne MONGO_URL, DB_NAME, REACT_APP_BACKEND_URL. Dodano DISCORD_API_URL/CDN_URL/WEB_URL, APP_ORIGIN, SESSION_HASH_KEY, SESSION_TTL_SECONDS, FERNET_KEY, WEBHOOK_CRON_SECRET. Sekrety tylko w backend/.env, nigdy w UI lub dokumentacji.

## Weryfikacja — 2026-10-12
- `yarn build` i Python compileall poprawne; `/api/health` ponownie 200.
- Iteracja 1: MVP 20/20 pytest, formularze i responsywność.
- Iteracja 2: 32/33 pytest; jedyna różnica dotyczyła nagłówka ciasteczka przepisywanego w podglądzie, nie logiki aplikacji.
- Iteracja 3: **36/36 pytest**, `/app/test_reports/iteration_3.json`; testy skorygowane, bez osłabiania logiki aplikacji. Asercja None dopuszczona wyłącznie dla hosta preview i tylko razem z Partitioned; bezpośredni test wymaga Lax.
- Testy Origin missing/null/foreign POST/PUT/PATCH/DELETE, izolacji dwóch właścicieli, kaskadowego usuwania, redakcji tokenów.
- UI: CRUD bibliotek, edytor/embedy/warianty, consent i błędny token; osobno harmonogram resume → pause → delete z potwierdzeniem trwałości przez API.
- Cron faktycznie wywołany przez zewnętrzny endpoint: autoryzacja, 400, idempotencja, wykonanie testowego zaległego zadania z nieprawidłowym tokenem i usunięcie ciphertext po 401. Szablon YAML i indeksy TTL zweryfikowane.
- Testy sukcesu wysyłki i kontraktu payload: MOCKED wyłącznie testowo. Rzeczywista dostawa nadal wymaga tokenu użytkownika wpisanego w panelu.
- Responsywność 320/768/1024/1440 bez poziomego przewijania. Zrzuty smoke `/app/relay-smoke.jpg` i `/app/relay-features-smoke.jpg`.
- Testy w `/app/backend/tests/`; JUnit `/app/test_reports/pytest/pytest_results.xml`.
- Pomocnicza sesja UI odwołana, plik z cookie usunięty. Helpery `/app/tests/seed_schedule_ui_fixture.py` / `cleanup_schedule_ui_fixture.py` używają wyłącznie prywatnego `/tmp/relay_test_artifacts` i odwołują całą testową sesję; zweryfikowano seed + cleanup.

## Priorytety / następne działania
- **P0:** brak otwartych usterek w zweryfikowanym zakresie. Nie dodawać self-tokenów ani trybów omijania zabezpieczeń.
- **P1:** rzeczywista próba manualnej i zaplanowanej dostawy z oficjalnym botem na własny testowy kanał użytkownika. Nie prosić o publikowanie tokenu w czacie.
- **P2:** kalendarz zaplanowanych ogłoszeń; edycja parametrów istniejącego harmonogramu (obecnie pauza/wznowienie/usunięcie + użycie treści do nowego zadania).
- **P2:** opcjonalny trwalszy model kont/odzyskiwania przestrzeni po utracie cookie i niezawodna kolejka zadań, po osobnym uzgodnieniu potrzeb i retencji.