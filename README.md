# Space Earth Dashboard

Backend i dashboard do prezentowania danych z NASA APOD, NASA NeoWs oraz pozycji ISS.

## Konfiguracja

Skopiuj `.env.example` do `.env` i ustaw klucz NASA:

```env
NASA_API_KEY=twoj_klucz_nasa
```

W trybie Docker Compose dev aplikacja uzywa `.env`.

## Stack

- Python 3.11+
- FastAPI
- PostgreSQL
- Docker Compose
- Pytest
- Locust

## Uruchomienie developerskie

```powershell
docker compose -f docker-compose.dev.yml up --build
```

API: <http://localhost:8000/api/v1/health>

Swagger: <http://localhost:8000/docs>

## Zapis danych do PostgreSQL

Migracje bazy danych są stosowane automatycznie przy starcie Docker Compose. Lokalnie można je
uruchomić poleceniem:

```powershell
alembic upgrade head
```

Nastepnie mozna zapisac dane pobrane z API:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/v1/space/ingest/apod
Invoke-RestMethod -Method Post http://localhost:8000/api/v1/space/ingest/iss-position
Invoke-RestMethod -Method Post "http://localhost:8000/api/v1/space/ingest/neo?start_date=2026-05-23"
```

Endpoint `ingest/apod` korzysta z prostego cache w PostgreSQL: jesli APOD dla
podanej daty jest juz zapisany, backend zwraca rekord z bazy bez ponownego zapytania do NASA.

Endpoint `ingest/neo` korzysta z prostego cache w PostgreSQL: jesli asteroidy dla
podanej daty sa juz zapisane, backend zwraca rekordy z bazy bez ponownego zapytania do NASA.

Zapisane obserwacje sa dostepne pod:

```text
http://localhost:8000/api/v1/space/observations
```

Agregowane podsumowanie dnia:

```text
http://localhost:8000/api/v1/space/daily-summary?target_date=2026-05-23
```

## Sciezka demo

1. Uruchom projekt:

```powershell
docker compose -f docker-compose.dev.yml up --build
```

2. Otworz dashboard:

```text
http://localhost:8000/
```

3. Kliknij `Zapisz APOD`, `Zapisz ISS` i `Zapisz asteroidy`.
4. Sprawdz sekcje `Zapisane obserwacje` oraz `Podsumowanie dnia`.
5. Otworz Swagger:

```text
http://localhost:8000/docs
```

6. Uruchom testy:

```powershell
python -m pytest
```

## Bledy zewnetrznych API

Gdy NASA albo Open Notify nie odpowiada, backend zwraca czytelny blad JSON, np.:

```json
{
  "detail": "NASA API request failed with status 429.",
  "source": "nasa",
  "upstream_status_code": 429
}
```

Bledy sa rowniez zapisywane w logach aplikacji.

## Testy

```powershell
pip install -e ".[dev]"
python -m pytest
```

Testy w Dockerze:

```powershell
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from api
docker compose -f docker-compose.test.yml down
```

## CI — GitHub Actions

Workflow `.github/workflows/ci.yml` uruchamia sie po kazdym pushu i pull requescie.
Dwa niezalezne zadania uruchamiaja Pytest na Pythonie 3.12 oraz buduja obraz
aplikacji z `Dockerfile`. Obraz nie jest publikowany w rejestrze.
Obecne testy nie wymagaja uruchomionej bazy PostgreSQL ani klucza NASA;
odpowiedzi zewnetrznych API sa symulowane w testach klientow.

## Test wydajnosciowy

Uruchom najpierw aplikacje w trybie dev:

```powershell
docker compose -f docker-compose.dev.yml up --build
```

Przed pomiarem upewnij się, że migracje bazy zostały zastosowane:

```powershell
alembic upgrade head
```

W drugim terminalu uruchom Locust w trybie headless:

```powershell
locust -f tests/performance/locustfile.py --host http://localhost:8000 --headless -u 10 -r 2 -t 30s
```

Tryb z interfejsem WWW Locust:

```powershell
locust -f tests/performance/locustfile.py --host http://localhost:8000
```

## Srodowiska

- `docker-compose.dev.yml` - hot reload i lokalna baza developerska.
- `docker-compose.test.yml` - uruchamianie testow w izolowanym kontenerze.
- `docker-compose.prod.yml` - konfiguracja produkcyjna z osobnym plikiem `.env`.
