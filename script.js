const stationFeedsFallback = [
  {
    id: 1,
    title: "Cosmo-flies continue attacks on survey drones",
    body: "For reasons still unclear, the winged lifeforms of Sector XX keep targeting exposed antenna arrays.",
    image: "Assets/news-001.jpg",
  },
];

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
    const randomFeed = stationFeeds[Math.floor(Math.random() * stationFeeds.length)];
    feedTitle.textContent = randomFeed.title;
    feedBody.textContent = randomFeed.body;
    feedImage.src = randomFeed.image;
  });
}