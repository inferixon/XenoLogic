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

const xenopediaFallback = [
  {
    id: 1,
    entry: 1,
    name: "Glorp",
    description:
      "Known for tapping inspection glass in suspiciously regular patterns. Often appears in the station's training reports because it encourages clean implication chains.",
    threats:
      "Low under normal observation. Escalates immediately if allowed near office locks, coffee machines, or anything with a blinking confirmation light.",
    image: "Assets/alien-01.webp",
  },
  {
    id: 2,
    entry: 2,
    name: "Zaxer",
    description:
      "A fast-moving archive pest with a talent for creating false causal stories. Excellent for training analysts not to confuse sequence with proof.",
    threats:
      "Moderate to paperwork and staff morale. One unattended Zaxer can generate three bad reports, two rumors, and a completely fake emergency sequence.",
    image: "Assets/alien-02.webp",
  },
  {
    id: 3,
    entry: 3,
    name: "Plunk",
    description:
      "A small lifeform with a dramatic instinct for pressing the wrong button at the perfect moment. Frequently used in protocols about contradiction and insufficient information.",
    threats:
      "Low, but consistently loud. A startled Plunk can turn a quiet lab into a full alarm rehearsal before anyone confirms what actually happened.",
    image: "Assets/alien-03.webp",
  },
  {
    id: 4,
    entry: 4,
    name: "Vrex",
    description:
      "A territorial observer-class organism that reacts strongly to category errors. Useful for class membership, subclassing, and mistaken generalization examples.",
    threats:
      "Situational and highly offended by bad labeling. If you classify a Vrex as office furniture, it will spend the next hour proving you wrong at full volume.",
    image: "Assets/alien-04.webp",
  },
];

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

const navToggle = document.querySelector("[data-nav-toggle]");
const siteNav = document.querySelector("[data-site-nav]");
const stationFeed = document.querySelector("#station-feed");
const feedTitle = document.querySelector("[data-feed-title]");
const feedBody = document.querySelector("[data-feed-body]");
const feedImage = document.querySelector("[data-feed-image]");

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

function isValidXenoEntry(entry) {
  return Boolean(
    entry &&
      typeof entry.id === "number" &&
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

async function loadXenopediaEntries() {
  try {
    const response = await fetch("xenopedia.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Xenopedia request failed with status ${response.status}`);
    }

    const xenopediaEntries = await response.json();
    if (!Array.isArray(xenopediaEntries)) {
      throw new Error("Xenopedia data is not an array");
    }

    const publishedEntries = xenopediaEntries.filter(isValidXenoEntry);
    return publishedEntries.length ? publishedEntries : xenopediaFallback;
  } catch {
    return xenopediaFallback;
  }
}

function formatEntryNumber(entryNumber) {
  return String(entryNumber).padStart(2, "0");
}

function sortXenopediaEntries(entries) {
  return [...entries].sort((left, right) => left.name.localeCompare(right.name, "en", { sensitivity: "base" }));
}

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

  return article;
}

function renderXenopedia(entries) {
  if (!xenopediaGrid) {
    return;
  }

  xenopediaGrid.innerHTML = "";

  sortXenopediaEntries(entries).forEach((entry) => {
    xenopediaGrid.append(createXenoCard(entry));
  });
}

if (xenopediaGrid) {
  loadXenopediaEntries().then((entries) => {
    renderXenopedia(entries);
  });
}