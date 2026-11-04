# Space Earth Dashboard

Backend i dashboard do prezentowania danych z NASA APOD, NASA NeoWs oraz pozycji ISS.

Dashboard pokazuje bieżącą pozycję i historię ISS na mapie oraz 30-dniowy trend obiektów
bliskich Ziemi, w tym prędkość, średnicę, odległość minięcia i potencjalne zagrożenie.

## Konfiguracja

Skopiuj `.env.example` do `.env` i ustaw klucz NASA:

```env
NASA_API_KEY=twoj_klucz_nasa
ADMIN_API_TOKEN=losowy_sekret_administracyjny
```

W trybie Docker Compose dev aplikacja uzywa `.env`.

## Stack

- Python 3.11+
- FastAPI
- PostgreSQL
- Docker Compose
- Pytest
- Locust
- APScheduler
- Prometheus metrics

## Uruchomienie developerskie

```powershell
docker compose -f docker-compose.dev.yml up --build
```

API: <http://localhost:8000/api/v1/health>

Swagger: <http://localhost:8000/docs>

Liveness, readiness i metryki Prometheus:

```text
http://localhost:8000/api/v1/health/live
http://localhost:8000/api/v1/health/ready
http://localhost:8000/metrics
```

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

Historia automatycznych i ręcznych uruchomień ingestion jest dostępna pod:

```text
http://localhost:8000/api/v1/space/ingestion-runs
```

Osobny proces `worker` pobiera APOD oraz NEO raz dziennie i pozycję ISS co 5 minut.
Interwał oraz strefę czasową można zmienić przez zmienne środowiskowe.
Ręczne endpointy ingestion wymagają nagłówka `X-Admin-Token`; dashboard korzysta z
automatycznie zebranych danych.

Agregowane podsumowanie dnia:

```text
http://localhost:8000/api/v1/space/daily-summary?target_date=2026-05-23
```

Analityka obiektów NEO z trendami, parametrami przelotu i najbliższymi podejściami:

```text
http://localhost:8000/api/v1/space/analytics/neo?start_date=2026-05-01&end_date=2026-05-31
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

3. Sprawdź mapę ISS, wykres NEO oraz dane APOD.
4. Po uruchomieniu workera sprawdź sekcje `Zapisane obserwacje` i `Podsumowanie dnia`.
5. Otwórz Swagger:

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
Dwa niezalezne zadania uruchamiaja Pytest z PostgreSQL na Pythonie 3.12 oraz buduja obraz
aplikacji z `Dockerfile`. CI sprawdza także Ruff, pokrycie testami i znane podatności
zależności. Po merge do `master` zweryfikowany obraz jest publikowany do GitHub Container
Registry. Odpowiedzi zewnętrznych API są symulowane w testach klientów.

## Wdrożenie

Plik `render.yaml` opisuje usługę webową, osobny worker ingestion i PostgreSQL. Może zostać
użyty jako Render Blueprint. Podczas tworzenia usług należy bezpiecznie podać `NASA_API_KEY`
i `ADMIN_API_TOKEN`;
adres bazy jest przekazywany automatycznie. Migracje są chronione blokadą PostgreSQL, więc
równoległy start API i workera nie uruchomi ich jednocześnie.

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

Scenariusz wydajnościowy korzysta z lokalnych odczytów bazy i nie obciąża zewnętrznych API.

## Srodowiska

- `docker-compose.dev.yml` - hot reload i lokalna baza developerska.
- `docker-compose.test.yml` - uruchamianie testow w izolowanym kontenerze.
- `docker-compose.prod.yml` - konfiguracja produkcyjna z osobnym plikiem `.env`.
