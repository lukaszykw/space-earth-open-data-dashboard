const api = "/api/v1";

const statusEl = document.querySelector("#status");
const dbStatusEl = document.querySelector("#db-status");
const apodImage = document.querySelector("#apod-image");
const apodVideo = document.querySelector("#apod-video");
const apodFallback = document.querySelector("#apod-fallback");
const apodMediaLink = document.querySelector("#apod-media-link");
const apodTitle = document.querySelector("#apod-title");
const apodDate = document.querySelector("#apod-date");
const apodDescription = document.querySelector("#apod-description");
const issLatitude = document.querySelector("#iss-latitude");
const issLongitude = document.querySelector("#iss-longitude");
const issTimestamp = document.querySelector("#iss-timestamp");
const neoSummary = document.querySelector("#neo-summary");
const neoList = document.querySelector("#neo-list");
const summaryTotal = document.querySelector("#summary-total");
const summaryApod = document.querySelector("#summary-apod");
const summaryIss = document.querySelector("#summary-iss");
const summaryNeo = document.querySelector("#summary-neo");
const observationsTable = document.querySelector("#observations-table");
const detailsEmpty = document.querySelector("#details-empty");
const detailsContent = document.querySelector("#details-content");
const detailsTitle = document.querySelector("#details-title");
const detailsSource = document.querySelector("#details-source");
const detailsExternalId = document.querySelector("#details-external-id");
const detailsObservedAt = document.querySelector("#details-observed-at");
const detailsSummary = document.querySelector("#details-summary");
const detailsLink = document.querySelector("#details-link");
const detailsRaw = document.querySelector("#details-raw");

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      detail = response.statusText;
    }
    throw new Error(`${response.status} ${detail}`);
  }
  return response.json();
}

function setStatus(message) {
  statusEl.textContent = message;
}

function renderApod(apod) {
  apodTitle.textContent = apod.title || "-";
  apodDate.textContent = apod.date || "-";
  apodDescription.textContent = apod.explanation || "-";
  apodImage.hidden = true;
  apodVideo.hidden = true;
  apodFallback.hidden = true;
  apodImage.removeAttribute("src");
  apodVideo.removeAttribute("src");
  apodMediaLink.removeAttribute("href");

  if (apod.media_type === "image" && apod.url) {
    apodImage.hidden = false;
    apodImage.src = apod.url;
    return;
  }

  if (apod.media_type === "video" && apod.url) {
    apodFallback.hidden = false;
    apodMediaLink.href = apod.url;
    return;
  }

  if (apod.url) {
    apodFallback.hidden = false;
    apodMediaLink.href = apod.url;
  }
}

function renderIss(payload) {
  const position = payload.iss_position || {};
  issLatitude.textContent = position.latitude || "-";
  issLongitude.textContent = position.longitude || "-";
  issTimestamp.textContent = payload.timestamp || "-";
}

function renderNeo(payload) {
  const objectsByDate = payload.near_earth_objects || {};
  const objects = Object.values(objectsByDate).flat();
  neoSummary.textContent = `Liczba obiektow: ${objects.length}`;
  neoList.replaceChildren(
    ...objects.slice(0, 8).map((item) => {
      const li = document.createElement("li");
      li.textContent = `${item.name} (${item.id})`;
      return li;
    }),
  );
}

function renderDailySummary(summary) {
  summaryTotal.textContent = summary.total_observations;
  summaryApod.textContent = summary.apod_count;
  summaryIss.textContent = summary.iss_position_count;
  summaryNeo.textContent = summary.neo_count;
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString("pl-PL");
}

function observationName(item) {
  return item.title || item.external_id || String(item.id);
}

function observationSummary(item) {
  if (item.source === "open_notify_iss") {
    return `lat: ${item.latitude ?? "-"}, lon: ${item.longitude ?? "-"}`;
  }
  if (item.source === "nasa_apod") {
    return `media: ${item.media_type || "-"}`;
  }
  if (item.source === "nasa_neows") {
    return item.description || "Obiekt NEO";
  }
  return item.description || "-";
}

function observationLink(item) {
  if (item.media_url) {
    return item.media_url;
  }
  if (item.source === "nasa_neows" && item.description) {
    return item.description;
  }
  return "";
}

function showObservationDetails(item) {
  detailsEmpty.hidden = true;
  detailsContent.hidden = false;
  detailsTitle.textContent = observationName(item);
  detailsSource.textContent = item.source;
  detailsExternalId.textContent = item.external_id || "-";
  detailsObservedAt.textContent = formatDateTime(item.observed_at);
  detailsSummary.textContent = observationSummary(item);
  detailsRaw.textContent = JSON.stringify(item.raw, null, 2);

  const link = observationLink(item);
  if (link) {
    detailsLink.hidden = false;
    detailsLink.href = link;
  } else {
    detailsLink.hidden = true;
    detailsLink.removeAttribute("href");
  }
}

function renderObservations(observations) {
  dbStatusEl.textContent = `Zapisane rekordy: ${observations.length}`;
  observationsTable.replaceChildren(
    ...observations.slice(0, 20).map((item) => {
      const row = document.createElement("tr");
      const sourceCell = document.createElement("td");
      const nameCell = document.createElement("td");
      const dateCell = document.createElement("td");

      row.tabIndex = 0;
      sourceCell.textContent = item.source;
      nameCell.textContent = observationName(item);
      dateCell.textContent = formatDateTime(item.observed_at);
      row.append(sourceCell, nameCell, dateCell);
      row.addEventListener("click", () => showObservationDetails(item));
      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          showObservationDetails(item);
        }
      });
      return row;
    }),
  );

  if (observations.length > 0) {
    showObservationDetails(observations[0]);
  }
}

async function loadDashboard() {
  setStatus("Pobieranie danych...");
  const date = todayIsoDate();

  const [apod, iss, neo] = await Promise.all([
    fetchJson(`${api}/space/apod`),
    fetchJson(`${api}/space/iss-position`),
    fetchJson(`${api}/space/neo?start_date=${date}`),
  ]);

  renderApod(apod);
  renderIss(iss);
  renderNeo(neo);
  setStatus("Dane odswiezone.");

  try {
    const [observations, summary] = await Promise.all([
      fetchJson(`${api}/space/observations`),
      fetchJson(`${api}/space/daily-summary?target_date=${date}`),
    ]);
    renderObservations(observations);
    renderDailySummary(summary);
  } catch (error) {
    dbStatusEl.textContent = `Brak polaczenia z baza: ${error.message}`;
    observationsTable.replaceChildren();
    detailsEmpty.hidden = false;
    detailsContent.hidden = true;
  }
}

async function postAction(url, successMessage) {
  setStatus("Wykonywanie akcji...");
  try {
    await fetchJson(url, { method: "POST" });
    setStatus(successMessage);
    await loadDashboard();
  } catch (error) {
    setStatus(`Blad: ${error.message}`);
  }
}

document.querySelector("#refresh-btn").addEventListener("click", loadDashboard);
document.querySelector("#save-apod-btn").addEventListener("click", () => {
  postAction(`${api}/space/ingest/apod`, "APOD zapisany.");
});
document.querySelector("#save-iss-btn").addEventListener("click", () => {
  postAction(`${api}/space/ingest/iss-position`, "Pozycja ISS zapisana.");
});
document.querySelector("#save-neo-btn").addEventListener("click", () => {
  const date = todayIsoDate();
  postAction(`${api}/space/ingest/neo?start_date=${date}`, "Asteroidy zapisane.");
});

loadDashboard().catch((error) => {
  setStatus(`Blad ladowania danych: ${error.message}`);
});
