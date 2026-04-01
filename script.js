const stationFeedsFallback = [
  {
    id: 1,
    title: "Cosmo-flies continue attacks on survey drones",
    body: "For reasons still unclear, the winged lifeforms of Sector XX keep targeting exposed antenna arrays.",
    image: "Assets/news-001.jpg",
  },
];

const stationFeedRotationMs = 10 * 60 * 1000;
const stationFeedFadeMs = 180;
const stationFeedBootNoiseMs = 300;
const stationFeedStorageKey = "xenologic:last-station-feed-id";
const stationFeedSnapshotStorageKey = "xenologic:last-station-feed-snapshot";

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