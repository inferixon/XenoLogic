const stationFeedsFallback = [
  {
    id: 1,
    title: "Cosmo-flies continue attacks on survey drones",
    body: "For reasons still unclear, the winged lifeforms of Sector XX keep targeting exposed antenna arrays.",
    image: "Assets/news-001.jpg",
  },
  {
    id: 2,
    title: "Station canteen bans soup after zero-g incident",
    body: "After three minor orbital incidents, cooks have been asked to keep all noodles below escape velocity.",
    image: "Assets/news-002.jpg",
  },
  {
    id: 3,
    title: "Moss-whales spotted drifting near Colony Ring 4",
    body: "The balloon-shaped herbivores appear harmless, unless startled by welding sparks or accordion music.",
    image: "Assets/news-003.jpg",
  },
  {
    id: 4,
    title: "Miners report polite tapping beneath ice crust",
    body: "Acoustic teams say the rhythm resembles greeting patterns, though one expert insists it is just plumbing.",
    image: "Assets/news-004.jpg",
  },
  {
    id: 5,
    title: "Dust farmers celebrate first harvest on red plains",
    body: "The crop is technically edible, faintly glowing, and already being marketed as rustic frontier cuisine.",
    image: "Assets/news-005.jpg",
  },
  {
    id: 6,
    title: "Tiny mirror-beetles blamed for solar panel confusion",
    body: "Maintenance crews say the insects keep rearranging themselves into warning icons and rude little faces.",
    image: "Assets/news-006.jpg",
  },
  {
    id: 7,
    title: "Night shift on Europa Pier hears laughing in vents",
    body: "Engineers found no intruders, only warm air, loose bolts, and one extremely pleased gelatin organism.",
    image: "Assets/news-007.jpg",
  },
  {
    id: 8,
    title: "Children on Titan adopt six-legged puddle pet craze",
    body: "Parents remain divided after several pets learned door codes and began waiting outside the dessert lockers.",
    image: "Assets/news-008.jpg",
  },
  {
    id: 9,
    title: "Orbital gardeners lose argument with carnivorous lilies",
    body: "No injuries were reported, but three gloves, one boot, and station dignity could not be recovered.",
    image: "Assets/news-009.jpg",
  },
  {
    id: 10,
    title: "Mayor promises new domes before sand eels return",
    body: "Residents applauded the statement, then immediately checked evacuation routes and bought extra ceiling anchors.",
    image: "Assets/news-010.jpg",
  },
  {
    id: 11,
    title: "Specimen 04 attempted to classify the observer first",
    body: "No consensus has been reached on whether this counts as intelligence, sarcasm, or a territorial reflex.",
    image: "Assets/news-011.jpg",
  },
  {
    id: 12,
    title: "Three signals were recorded. One was just rude.",
    body: "Field teams confirm that not every transmission from deep space can be described as constructive.",
    image: "Assets/news-012.jpg",
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