const stationFeedsFallback = [
  {
    id: 1,
    title: "Cosmo-flies continue attacks on survey drones",
    body: "For reasons still unclear, the winged lifeforms of Sector XX keep targeting exposed antenna arrays.",
    image: "Assets/news-001.webp",
  },
];

const stationFeedRotationMs = 10 * 60 * 1000;
const stationFeedFadeMs = 180;
const stationFeedBootNoiseMs = 300;
const stationFeedStorageKey = "xenologic:last-station-feed-id";
const stationFeedSnapshotStorageKey = "xenologic:last-station-feed-snapshot";
const xenopediaGrid = document.querySelector("[data-xenopedia-grid]");

// Utility helpers used by the animated station feed flow.
function wait(durationMs) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, durationMs);
  });
}

function isValidFeed(feed) {
  return Boolean(
    feed &&
      typeof feed.id === "number" &&
      typeof feed.title === "string" &&
      feed.title.trim() &&
      typeof feed.body === "string" &&
      feed.body.trim() &&
      typeof feed.image === "string" &&
      feed.image.trim(),
  );
}

// Station feed - load local news data and fall back to a safe default item.
async function loadStationFeeds() {
  try {
    const response = await fetch("news-feed.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Feed request failed with status ${response.status}`);
    }

    const stationFeeds = await response.json();
    if (!Array.isArray(stationFeeds)) {
      throw new Error("Feed data is not an array");
    }

    const publishedFeeds = stationFeeds.filter(isValidFeed);

    return publishedFeeds.length ? publishedFeeds : stationFeedsFallback;
  } catch {
    return stationFeedsFallback;
  }
}

function pickRandomFeed(stationFeeds, excludedId) {
  if (!Array.isArray(stationFeeds) || !stationFeeds.length) {
    return stationFeedsFallback[0];
  }

  const eligibleFeeds =
    stationFeeds.length > 1
      ? stationFeeds.filter((item) => item.id !== excludedId)
      : stationFeeds;

  return eligibleFeeds[Math.floor(Math.random() * eligibleFeeds.length)];
}

// Station feed - persist the last rendered item so the page can resume smoothly.
function readLastStationFeedId() {
  try {
    return Number.parseInt(localStorage.getItem(stationFeedStorageKey) || "", 10);
  } catch {
    return Number.NaN;
  }
}

function writeLastStationFeedId(feedId) {
  try {
    localStorage.setItem(stationFeedStorageKey, String(feedId));
  } catch {
    // Ignore storage failures and keep runtime behavior.
  }
}

function readStoredFeed() {
  try {
    const storedFeed = JSON.parse(localStorage.getItem(stationFeedSnapshotStorageKey) || "null");
    return isValidFeed(storedFeed) ? storedFeed : null;
  } catch {
    return null;
  }
}

function writeStoredFeed(feed) {
  if (!isValidFeed(feed)) {
    return;
  }

  try {
    localStorage.setItem(stationFeedSnapshotStorageKey, JSON.stringify(feed));
  } catch {
    // Ignore storage failures and keep runtime behavior.
  }
}

// Shared DOM references for navigation and homepage station feed rendering.
const navToggle = document.querySelector("[data-nav-toggle]");
const siteNav = document.querySelector("[data-site-nav]");
const stationFeed = document.querySelector("#station-feed");
const feedTitle = document.querySelector("[data-feed-title]");
const feedBody = document.querySelector("[data-feed-body]");
const feedImage = document.querySelector("[data-feed-image]");

// Station feed - write the chosen item into the visible homepage panel.
function applyFeed(feed) {
  if (!feedTitle || !feedBody || !feedImage || !stationFeed) {
    return;
  }

  feedTitle.textContent = feed.title;
  feedBody.textContent = feed.body;
  feedImage.src = feed.image;
  stationFeed.dataset.loading = "false";
}

function preloadFeedImage(feed) {
  const nextImage = new Image();

  return new Promise((resolve) => {
    const finish = () => resolve(feed);
    nextImage.addEventListener("load", finish, { once: true });
    nextImage.addEventListener("error", finish, { once: true });
    nextImage.src = feed.image;
  });
}

// Station feed - swap cards with a preload + fade flow so the image changes cleanly.
function renderFeed(feed) {
  const commitFeed = () => {
    applyFeed(feed);
    writeStoredFeed(feed);
    writeLastStationFeedId(feed.id);
  };

  const imageReady = preloadFeedImage(feed);

  const showFeed = () => {
    if (!stationFeed || stationFeed.dataset.ready !== "true") {
      Promise.all([imageReady, wait(stationFeedBootNoiseMs)]).then(() => {
        commitFeed();
        stationFeed.dataset.ready = "true";
      });
      return;
    }

    imageReady.then(() => {
      stationFeed.dataset.transitioning = "true";

      window.setTimeout(() => {
        commitFeed();
        stationFeed.dataset.transitioning = "false";
      }, stationFeedFadeMs);
    });
  };

  showFeed();
}

// Navigation - open and close the mobile menu.
if (navToggle && siteNav) {
  navToggle.addEventListener("click", () => {
    const isOpen = document.body.classList.toggle("nav-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });

  siteNav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      document.body.classList.remove("nav-open");
      navToggle.setAttribute("aria-expanded", "false");
    });
  });
}

// Station feed - boot the rotating homepage news module.
if (feedTitle && feedBody && feedImage) {
  const storedFeed = readStoredFeed();

  if (stationFeed) {
    stationFeed.dataset.loading = "true";
  }

  loadStationFeeds().then((stationFeeds) => {
    let currentFeedId = Number.isNaN(readLastStationFeedId())
      ? storedFeed?.id ?? Number.NaN
      : readLastStationFeedId();

    const renderRandomFeed = () => {
      const randomFeed = pickRandomFeed(stationFeeds, currentFeedId);
      currentFeedId = randomFeed.id;
      renderFeed(randomFeed);
    };

    renderRandomFeed();

    if (stationFeeds.length > 1) {
      window.setInterval(renderRandomFeed, stationFeedRotationMs);
    }
  });
}

// Xenopedia - validate each entry before it becomes a visible card.
function isValidXenoEntry(entry) {
  return Boolean(
    entry &&
      typeof entry.entry === "number" &&
      typeof entry.name === "string" &&
      entry.name.trim() &&
      typeof entry.description === "string" &&
      entry.description.trim() &&
      typeof entry.threats === "string" &&
      entry.threats.trim() &&
      typeof entry.image === "string" &&
      entry.image.trim(),
  );
}

// Xenopedia - load the local data source and return a usable array of entries.
async function loadXenopediaEntries() {
  const response = await fetch("xenopedia.json", { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Xenopedia request failed with status ${response.status}`);
  }

  const xenopediaEntries = await response.json();
  if (!Array.isArray(xenopediaEntries)) {
    throw new Error("Xenopedia data is not an array");
  }

  const publishedEntries = xenopediaEntries.filter(isValidXenoEntry);

  if (!publishedEntries.length) {
    throw new Error("Xenopedia data does not contain valid entries");
  }

  return publishedEntries;
}

// Xenopedia - format and sort entries before they become cards.
function formatEntryNumber(entryNumber) {
  return String(entryNumber).padStart(2, "0");
}

function sortXenopediaEntries(entries) {
  return [...entries].sort((left, right) => left.entry - right.entry);
}

function showXenopediaMessage(message, state = "error") {
  if (!xenopediaGrid) {
    return;
  }

  xenopediaGrid.innerHTML = "";

  const status = document.createElement("p");
  status.className = `xenopedia-status xenopedia-status--${state}`;
  status.textContent = message;
  status.setAttribute("role", state === "error" ? "alert" : "status");

  xenopediaGrid.append(status);
}

// Xenopedia 3D hover - restore the neutral card state when the pointer leaves.
function resetXenoCardTilt(card) {
  card.dataset.hover = "false";
  card.style.setProperty("--xeno-tilt-x", "0deg");
  card.style.setProperty("--xeno-tilt-y", "0deg");
  card.style.setProperty("--xeno-hover-x", "50%");
  card.style.setProperty("--xeno-hover-y", "50%");
}

// Xenopedia 3D hover - rotate the card slightly based on pointer position.
function attachXenoCardTilt(card) {
  resetXenoCardTilt(card);

  card.addEventListener("pointermove", (event) => {
    if (event.pointerType === "touch") {
      return;
    }

    const bounds = card.getBoundingClientRect();
    const horizontal = ((event.clientX - bounds.left) / bounds.width) * 100;
    const vertical = ((event.clientY - bounds.top) / bounds.height) * 100;
    const rotateY = ((horizontal - 50) / 50) * 2.75;
    const rotateX = ((50 - vertical) / 50) * 2.75;

    card.dataset.hover = "true";
    card.style.setProperty("--xeno-hover-x", `${horizontal.toFixed(2)}%`);
    card.style.setProperty("--xeno-hover-y", `${vertical.toFixed(2)}%`);
    card.style.setProperty("--xeno-tilt-x", `${rotateX.toFixed(2)}deg`);
    card.style.setProperty("--xeno-tilt-y", `${rotateY.toFixed(2)}deg`);
  });

  card.addEventListener("pointerleave", () => {
    resetXenoCardTilt(card);
  });

  card.addEventListener("pointercancel", () => {
    resetXenoCardTilt(card);
  });
}

// Xenopedia - build one semantic card from one data object.
function createXenoCard(entry) {
  const article = document.createElement("article");
  article.className = "xeno-card";

  article.innerHTML = `
    <div class="xeno-card__header">
      <p class="xeno-card__name"></p>
      <p class="xeno-card__eyebrow"></p>
    </div>
    <div class="xeno-card__body">
      <div class="xeno-card__copy">
        <div class="xeno-card__field">
          <p class="xeno-card__label">Description</p>
          <p class="xeno-card__text" data-xeno-description></p>
        </div>
        <div class="xeno-card__field">
          <p class="xeno-card__label">Threats</p>
          <p class="xeno-card__text" data-xeno-threats></p>
        </div>
      </div>
      <figure class="xeno-card__visual" aria-label="${entry.name} specimen render">
        <div class="xeno-card__visual-frame">
          <img class="xeno-card__visual-image" alt="${entry.name} specimen render" loading="lazy" />
        </div>
        <figcaption class="xeno-card__visual-caption">Specimen render</figcaption>
      </figure>
    </div>
  `;

  const name = article.querySelector(".xeno-card__name");
  const eyebrow = article.querySelector(".xeno-card__eyebrow");
  const description = article.querySelector("[data-xeno-description]");
  const threats = article.querySelector("[data-xeno-threats]");
  const image = article.querySelector(".xeno-card__visual-image");
  const frame = article.querySelector(".xeno-card__visual-frame");

  if (name) {
    name.textContent = entry.name;
  }

  if (eyebrow) {
    eyebrow.textContent = `ALIEN // ENTRY ${formatEntryNumber(entry.entry)}`;
  }

  if (description) {
    description.textContent = entry.description;
  }

  if (threats) {
    threats.textContent = entry.threats;
  }

  if (image) {
    image.src = entry.image;
    image.addEventListener(
      "error",
      () => {
        frame?.classList.add("is-missing");
      },
      { once: true },
    );
  }

  attachXenoCardTilt(article);

  return article;
}

// Xenopedia - render the full array into repeated DOM cards.
function renderXenopedia(entries) {
  if (!xenopediaGrid) {
    return;
  }

  if (!Array.isArray(entries) || !entries.length) {
    showXenopediaMessage("No Xenopedia entries are available.", "empty");
    return;
  }

  xenopediaGrid.innerHTML = "";

  sortXenopediaEntries(entries).forEach((entry) => {
    xenopediaGrid.append(createXenoCard(entry));
  });
}

// Xenopedia - initialize the page by loading data, rendering cards, or showing an error.
if (xenopediaGrid) {
  loadXenopediaEntries()
    .then((entries) => {
      renderXenopedia(entries);
    })
    .catch(() => {
      showXenopediaMessage("Xenopedia data could not be loaded.");
    });
}