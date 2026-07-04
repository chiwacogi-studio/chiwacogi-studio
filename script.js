const BLOG_BASE = "https://goruu-blog.com/wp-json/wp/v2";
const POSTS_PER_PAGE = 9;

const blogList = document.getElementById("blog-list");
const catFilter = document.getElementById("cat-filter");

document.getElementById("year").textContent = new Date().getFullYear();

const navToggle = document.querySelector(".nav-toggle");
const nav = document.querySelector(".nav");
if (navToggle && nav) {
  navToggle.addEventListener("click", () => nav.classList.toggle("is-open"));
  nav.querySelectorAll("a").forEach(a => a.addEventListener("click", () => nav.classList.remove("is-open")));
}

// タブ切替（music.html / stickers.html）
document.querySelectorAll(".tabs").forEach(tabs => {
  const btns = tabs.querySelectorAll(".tab-btn");
  const groups = document.querySelectorAll(".tab-group");
  btns.forEach(btn => {
    btn.addEventListener("click", () => {
      btns.forEach(b => b.classList.toggle("is-active", b === btn));
      const target = btn.dataset.target;
      groups.forEach(g => {
        g.hidden = target !== "all" && g.dataset.group !== target;
      });
    });
  });
});

// ページ先頭へ戻るボタン
const toTop = document.querySelector(".to-top");
if (toTop) {
  window.addEventListener("scroll", () => {
    toTop.classList.toggle("is-visible", window.scrollY > 600);
  }, { passive: true });
  toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
}

const decode = (s) => {
  const t = document.createElement("textarea");
  t.innerHTML = s;
  return t.value;
};

const fmtDate = (iso) => {
  const d = new Date(iso);
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
};

async function loadCategories() {
  try {
    const res = await fetch(`${BLOG_BASE}/categories?per_page=100&orderby=count&order=desc`);
    if (!res.ok) return;
    const cats = await res.json();
    cats
      .filter(c => c.count > 0)
      .forEach(c => {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.textContent = `${decode(c.name)} (${c.count})`;
        catFilter.appendChild(opt);
      });
  } catch (e) {
    console.warn("カテゴリ取得失敗", e);
  }
}

async function loadPosts(categoryId = "") {
  blogList.innerHTML = '<p class="blog-loading">記事を読み込み中…</p>';
  try {
    const params = new URLSearchParams({
      per_page: String(POSTS_PER_PAGE),
      _embed: "wp:featuredmedia,wp:term",
      orderby: "date",
      order: "desc",
    });
    if (categoryId) params.set("categories", categoryId);

    const res = await fetch(`${BLOG_BASE}/posts?${params}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const posts = await res.json();

    if (posts.length === 0) {
      blogList.innerHTML = '<p class="blog-empty">このカテゴリの記事はまだないにゃ</p>';
      return;
    }

    blogList.innerHTML = posts.map(renderPost).join("");
  } catch (e) {
    console.error(e);
    blogList.innerHTML = '<p class="blog-error">記事の取得に失敗したにゃ。<a href="https://goruu-blog.com" target="_blank" rel="noopener">ブログに直接アクセス</a></p>';
  }
}

function renderPost(p) {
  const title = decode(p.title?.rendered || "");
  const date = fmtDate(p.date);
  const link = p.link;

  const media = p._embedded?.["wp:featuredmedia"]?.[0];
  const thumbUrl = media?.media_details?.sizes?.medium_large?.source_url
                || media?.media_details?.sizes?.medium?.source_url
                || media?.source_url
                || "";
  const thumb = thumbUrl
    ? `<div class="blog-thumb" style="background-image:url('${thumbUrl}')"></div>`
    : `<div class="blog-thumb blog-thumb-fallback">🐾</div>`;

  const terms = p._embedded?.["wp:term"]?.[0] || [];
  const cats = terms.slice(0, 3).map(t => `<span class="blog-cat">${decode(t.name)}</span>`).join("");

  return `
    <article class="blog-card">
      <a href="${link}" target="_blank" rel="noopener">
        ${thumb}
        <div class="blog-body">
          ${cats ? `<div class="blog-cat-list">${cats}</div>` : ""}
          <h3 class="blog-title">${title}</h3>
          <time class="blog-date">${date}</time>
        </div>
      </a>
    </article>
  `;
}

// ブログセクションはトップページのみ
if (blogList) {
  catFilter?.addEventListener("change", (e) => loadPosts(e.target.value));
  loadCategories();
  loadPosts();
}
