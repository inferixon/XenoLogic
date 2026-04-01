const stationFeeds = [
  {
    title: "Cosmo-flies continue attacks on survey drones",
    body: "For reasons still unclear, the winged lifeforms of Sector XX keep targeting exposed antenna arrays.",
    image: "Assets/news-00001.png",
  },
  {
    title: "Specimen 04 attempted to classify the observer first",
    body: "No consensus has been reached on whether this counts as intelligence, sarcasm, or a territorial reflex.",
    image: "Assets/news-00001.png",
  },
  {
    title: "Three signals were recorded. One was just rude.",
    body: "Field teams confirm that not every transmission from deep space can be described as constructive.",
    image: "Assets/news-00001.png",
  },
  {
    title: "Containment aisle B now requires calmer footsteps",
    body: "A chain of glowing spores has started mirroring the emotional tone of nearby staff conversations.",
    image: "Assets/news-00001.png",
  },
];

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
  const randomFeed = stationFeeds[Math.floor(Math.random() * stationFeeds.length)];
  feedTitle.textContent = randomFeed.title;
  feedBody.textContent = randomFeed.body;
  feedImage.src = randomFeed.image;
}