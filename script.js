const stationFeedsFallback = [
  {
    id: 1,
    title: "Cosmo-flies continue attacks on survey drones",
    body: "For reasons still unclear, the winged lifeforms of Sector XX keep targeting exposed antenna arrays.",
    image: "Assets/news-001.jpg",
  },
];

const stationFeedRotationMs = 10 * 60 * 1000;
const stationFeedStorageKey = "xenologic:last-station-feed-id";

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

    const publishedFeeds = stationFeeds.filter((item) => {
      return (
        typeof item?.title === "string" &&
        item.title.trim() &&
        typeof item?.body === "string" &&
        item.body.trim() &&
        typeof item?.image === "string" &&
        item.image.trim()
      );
    });

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

const navToggle = document.querySelector("[data-nav-toggle]");
const siteNav = document.querySelector("[data-site-nav]");
const feedTitle = document.querySelector("[data-feed-title]");
const feedBody = document.querySelector("[data-feed-body]");
const feedImage = document.querySelector("[data-feed-image]");

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
  loadStationFeeds().then((stationFeeds) => {
    let currentFeedId = readLastStationFeedId();

    const renderRandomFeed = () => {
      const randomFeed = pickRandomFeed(stationFeeds, currentFeedId);
      currentFeedId = randomFeed.id;
      feedTitle.textContent = randomFeed.title;
      feedBody.textContent = randomFeed.body;
      feedImage.src = randomFeed.image;
      writeLastStationFeedId(randomFeed.id);
    };

    renderRandomFeed();

    if (stationFeeds.length > 1) {
      window.setInterval(renderRandomFeed, stationFeedRotationMs);
    }
  });
}