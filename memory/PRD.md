# Relay — Discord AutoSender

## Oryginalne wymagania
„Zrob mi discorda auto message bot polegajacy na tym \"podajesz token\" i wybierasz channel id i wpisujesz wiadomosc wyslana dodaj tez emoji dodania emoji do wiadomosci pare kanalow”.
Język: polski. Użytkownik zatwierdził oficjalny Bot Token (nie token konta), jednorazową wysyłkę na wiele kanałów i emoji. Harmonogram oraz szablony później.

## Architektura
- React, shadcn/ui, React Router, lucide, react-markdown; polski panel Relay.
- FastAPI + httpx, oficjalny REST Discord v10; MongoDB dostępne z pierwotnych zmiennych środowiska, brak przechowywania sekretów i wiadomości.
- Token tylko w stanie React otwartej karty i w pamięci żądania serwera. Nigdy localStorage, sessionStorage, DB lub logi.
- POST /api/bot/connect, /api/channels/resolve, /api/messages/send; GET /api/health.
- Wysyłka 1–10 unikalnych kanałów, do 2000 znaków UTF-16, allowed_mentions.parse=[], nonce i enforce_nonce; bez automatycznych ponowień. Wyniki per kanał, stop przy 429 i niepewnych błędach sieci.
- Historia wyłącznie bieżącej sesji w pamięci React, bez publicznego endpointu historii.

## Status
- MVP zaimplementowane i przetestowane 2026-10-12. Brak rzeczywistego tokenu bota oraz testowego kanału: dostarczenie wiadomości na Discord pozostaje niezweryfikowane na żywo.
- Integracja aplikacji jest rzeczywista, nie symulowana. Scenariusze udanej wysyłki w testach korzystają z jawnych atrap HTTP (MOCKED wyłącznie w testach).

## Ukończone — 2026-10-12
- Polski, responsywny panel Relay z ciemnym motywem, boczną nawigacją, przewodnikiem konfiguracji bota i prawdziwym statusem połączenia.
- Pole tokenu z maskowaniem, połączenie z Discord /users/@me, odrzucanie kont niebędących botami, rozłączanie i reset stanu po odświeżeniu. Brak analityki PostHog.
- 1–10 kanałów: walidacja snowflake 17–20 cyfr, eliminacja duplikatów, zaznaczanie/usuwanie, pobieranie nazw z Discord przy połączonym bocie. Kanały dodane offline są sprawdzane przed wysyłką.
- Edytor z limitem 2000 znaków UTF-16, emoji z polską wyszukiwarką/kategoriami, pogrubieniem/kursywą/kodem, licznikiem oraz bezpiecznym podglądem Markdown.
- Potwierdzenie jednorazowej wysyłki, blokada podwójnego kliknięcia, raport dla każdego kanału z linkami do wysłanych wiadomości. Pingi użytkowników, ról i everyone wyłączone.
- Historia ostatnich 50 wysyłek w bieżącej karcie, ponowne użycie treści, czyszczenie historii; bez zapisywania wiadomości w bazie.
- Obsługa 400/401/403/404/429, retry-after, niepewnego wyniku przy timeout i pomijania kolejnych kanałów po błędzie globalnym. Nie ma automatycznego ponawiania ani harmonogramu.

## Weryfikacja
- `yarn build`: poprawna kompilacja; Python compileall: poprawny.
- Smoke screenshot `/app/relay-smoke.jpg`: panel działa, nie jest pusty.
- Raport `/app/test_reports/iteration_1.json`; 20/20 pytest, brak znalezionych błędów implementacji.
- Testy UI: token/show-hide, kanały/limity, emoji, Markdown, potwierdzenie/anulowanie, pojedyncza wysyłka, częściowe wyniki, historia, rozłączenie i reset prywatności.
- Testy szerokości 320/768/1024/1440 bez poziomego przewijania.
- Rzeczywiste API: health 200, błędny format tokenu 422 bez ujawnienia wartości, fałszywy token odrzucony przez Discord 401.
- Testy sukcesu connect/resolve/send i dostawy: MOCKED na poziomie testów HTTP/przeglądarki. Rzeczywista dostawa jest jedyną pozostałą luką w weryfikacji.
- Testy wielokrotnego użytku: `/app/backend/tests/`; wynik JUnit: `/app/test_reports/pytest/pytest_results.xml`. Dane i brak poświadczeń opisane w `/app/memory/test_credentials.md`.

## Pliki i konfiguracja
- Backend: `server.py`, `discord_models.py`, `discord_service.py`, `discord_routes.py`.
- Frontend: `context/RelayContext.jsx`, `lib/relay-api.js`, `lib/emojis.js`, `components/relay/`, `pages/ComposePage.jsx`, `pages/HistoryPage.jsx`, `App.css`.
- Konfiguracja środowiskowa: istniejące MONGO_URL, DB_NAME, CORS_ORIGINS, REACT_APP_BACKEND_URL zachowane; dodano DISCORD_API_URL, DISCORD_CDN_URL, DISCORD_WEB_URL do backend/.env.
- Token bota jest celowo podawany przez użytkownika dopiero w UI, nie w .env ani w dokumentacji.
- Dokument projektu: `/app/design_guidelines.json`. Rzeczywista implementacja nie używa sugerowanych tam mocków, harmonogramów ani interwałów.

## Priorytety
- P0: brak otwartych błędów w przetestowanym zakresie.
- P1 / następny krok: użytkownik wpisuje prawdziwy Bot Token w panelu, wybiera własny testowy kanał i potwierdza realną dostawę. Nie prosić o publikowanie sekretu w czacie.
- P1: harmonogram wysyłki po osobnym zatwierdzeniu zakresu; przy realizacji skorzystać z umiejętności scheduled-recurring-tasks, nie z lokalnego timera.
- P2: szablony ogłoszeń jako proponowane usprawnienie, grupy kanałów; trwała prywatna historia dopiero po uzgodnieniu modelu dostępu i ochrony tokenów.