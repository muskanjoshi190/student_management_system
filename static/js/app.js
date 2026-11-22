/* EduDesk – Student Management System (vanilla JS, talks to the Flask REST API) */
(function () {
  "use strict";

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));

  const state = { page: 1, perPage: 8, q: "", course: "", status: "", sort: "created_at", order: "desc", current: null, pendingDelete: null };
  const COLORS = ["#5b4bdb", "#14b08e", "#f2a20c", "#ef5469", "#2f80ed", "#9b51e0", "#e0568a", "#0f9aa8"];

  const ICON = {
    eye: '<svg viewBox="0 0 24 24"><path d="M12 5c5 0 9 4.500 10 7-1 2.500-5 7-10 7S3 14.500 2 12c1-2.500 5-7 10-7Zm0 2.500A4.500 4.500 0 1 0 12 16.500a4.500 4.500 0 0 0 0-9Zm0 2a2.500 2.500 0 1 1 0 5 2.500 2.500 0 0 1 0-5Z"/></svg>',
    edit: '<svg viewBox="0 0 24 24"><path d="m4 17.500V20h2.500L17.800 8.700l-2.500-2.500L4 17.500Zm15.700-9.800a1 1 0 0 0 0-1.400l-1.900-1.900a1 1 0 0 0-1.400 0l-1.200 1.200 3.300 3.300 1.200-1.200Z"/></svg>',
    trash: '<svg viewBox="0 0 24 24"><path d="M9 3h6l1 2h4a1 1 0 1 1 0 2h-1l-.8 12.100A2 2 0 0 1 16.200 21H7.800a2 2 0 0 1-2-1.900L5 7H4a1 1 0 0 1 0-2h4l1-2Zm-2 4 .8 12h8.400L17 7H7Z"/></svg>',
  };

  /* ---------- helpers ---------- */
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const initials = (n) => n.trim().split(/\s+/).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
  const colorFor = (n) => { let h = 0; for (const ch of n) h = (h * 31 + ch.charCodeAt(0)) >>> 0; return COLORS[h % COLORS.length]; };
  const avatar = (n) => `<span class="avatar" style="background:${colorFor(n)}">${esc(initials(n))}</span>`;
  const cgpaClass = (v) => (v >= 8 ? "hi" : v >= 6.5 ? "mid" : "lo");
  const yearLabel = (y) => ({ 1: "1st", 2: "2nd", 3: "3rd", 4: "4th" }[y] || y) + " year";
  const fmtDate = (d) => { if (!d) return "—"; const x = new Date(d.replace(" ", "T")); return isNaN(x) ? d : x.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }); };

  async function api(url, opts = {}) {
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...opts,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    let data = {};
    try { data = await res.json(); } catch (e) { /* ignore */ }
    if (!res.ok) { const err = new Error(data.message || "Something went wrong."); err.errors = data.errors || {}; err.status = res.status; throw err; }
    return data;
  }

  function toast(msg, type = "ok") {
    const t = document.createElement("div");
    t.className = "toast " + (type === "error" ? "error" : "");
    t.textContent = msg;
    $("#toasts").appendChild(t);
    setTimeout(() => { t.style.opacity = "0"; t.style.transition = "opacity .3s"; setTimeout(() => t.remove(), 300); }, 3200);
  }

  /* ---------- modal helpers ---------- */
  function openModal(id) { const m = $(id); m.hidden = false; document.body.style.overflow = "hidden"; return m; }
  function closeModals() { $$(".modal").forEach((m) => (m.hidden = true)); document.body.style.overflow = ""; }
  document.addEventListener("click", (e) => {
    if (e.target.closest("[data-close]") || e.target.classList.contains("modal")) closeModals();
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModals(); });

  /* ---------- routing ---------- */
  const TITLES = {
    dashboard: ["Dashboard", "Overview of your campus records"],
    students: ["All Students", "Search, filter and manage every student record"],
  };
  function route() {
    const name = (location.hash.replace("#/", "") || "dashboard");
    const view = TITLES[name] ? name : "dashboard";
    $$(".view").forEach((v) => (v.hidden = v.id !== "view-" + view));
    $$(".nav-link[data-route]").forEach((a) => a.classList.toggle("active", a.dataset.route === view));
    $("#pageTitle").textContent = TITLES[view][0];
    $("#pageSub").textContent = TITLES[view][1];
    closeSidebar();
    if (view === "dashboard") loadStats(); else loadStudents();
    window.scrollTo({ top: 0 });
  }
  window.addEventListener("hashchange", route);

  /* ---------- sidebar (mobile) ---------- */
  function closeSidebar() { $("#sidebar").classList.remove("open"); $("#scrim").classList.remove("show"); }
  $("#menuBtn").addEventListener("click", () => { $("#sidebar").classList.add("open"); $("#scrim").classList.add("show"); });
  $("#scrim").addEventListener("click", closeSidebar);

  /* ---------- clock ---------- */
  function tick() {
    const d = new Date();
    $("#clock").innerHTML = d.toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "short", year: "numeric" }) +
      "<br>" + d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  }
  tick(); setInterval(tick, 30000);

  /* ---------- dashboard ---------- */
  function countUp(el, to, decimals = 0) {
    const start = performance.now(), dur = 700;
    (function step(now) {
      const p = Math.min(1, (now - start) / dur), v = to * (1 - Math.pow(1 - p, 3));
      el.textContent = v.toFixed(decimals);
      if (p < 1) requestAnimationFrame(step);
    })(start);
  }

  async function loadStats() {
    try {
      const s = await api("/api/stats");
      countUp($('[data-stat="total"]'), s.total);
      countUp($('[data-stat="active"]'), s.active);
      countUp($('[data-stat="avg_cgpa"]'), s.avg_cgpa, 2);
      $('[data-stat="topper"]').innerHTML = s.topper ? `${esc(s.topper.name)}<em>CGPA ${s.topper.cgpa}</em>` : "—";

      const max = Math.max(1, ...s.by_course.map((c) => c.count));
      $("#courseCount").textContent = s.by_course.length + " courses";
      $("#courseBars").innerHTML = s.by_course.length
        ? s.by_course.map((c) => `<div class="bar-row"><span>${esc(c.course)}</span><div class="bar-track"><div class="bar-fill" data-w="${(c.count / max) * 100}"></div></div><b>${c.count}</b></div>`).join("")
        : '<p class="muted">No data yet.</p>';
      requestAnimationFrame(() => $$(".bar-fill").forEach((b) => (b.style.width = b.dataset.w + "%")));

      const pct = s.total ? Math.round((s.active / s.total) * 100) : 0;
      $("#donut").style.setProperty("--p", pct);
      $("#donutPct").textContent = pct + "%";
      $("#lgActive").textContent = s.active;
      $("#lgInactive").textContent = s.inactive;

      const ymax = Math.max(1, ...s.by_year.map((y) => y.count));
      $("#yearCols").innerHTML = [1, 2, 3, 4].map((y) => {
        const f = s.by_year.find((r) => r.year === y), n = f ? f.count : 0;
        return `<div class="col"><span>${n}</span><i style="height:${Math.max(6, (n / ymax) * 70)}px"></i><span>Y${y}</span></div>`;
      }).join("");

      $("#recentList").innerHTML = s.recent.length
        ? s.recent.map((r) => `<li data-view="${r.id}">${avatar(r.name)}<div class="who"><b>${esc(r.name)}</b><span>${esc(r.course)} · ${esc(r.roll_no)}</span></div></li>`).join("")
        : '<li class="muted">No students yet. Add your first one!</li>';
    } catch (e) { toast(e.message, "error"); }
  }
  $("#recentList").addEventListener("click", (e) => { const li = e.target.closest("[data-view]"); if (li) showDetails(li.dataset.view); });

  /* ---------- students table ---------- */
  function skeleton() {
    $("#tbody").innerHTML = Array.from({ length: 5 }, () => `<tr class="skeleton"><td colspan="7"><i></i></td></tr>`).join("");
  }

  async function loadStudents() {
    skeleton();
    const p = new URLSearchParams({ q: state.q, course: state.course, status: state.status, sort: state.sort, order: state.order, page: state.page, per_page: state.perPage });
    try {
      const d = await api("/api/students?" + p);
      state.page = d.page;
      $("#table").hidden = d.items.length === 0;
      $("#empty").hidden = d.items.length !== 0;
      $("#tbody").innerHTML = d.items.map((s) => `
        <tr>
          <td><div class="person">${avatar(s.name)}<div><b>${esc(s.name)}</b><span>${esc(s.email)}</span></div></div></td>
          <td class="mono">${esc(s.roll_no)}</td>
          <td><span class="chip course">${esc(s.course)}</span></td>
          <td class="c mono">${s.year}</td>
          <td class="c"><span class="cgpa ${cgpaClass(s.cgpa)}">${Number(s.cgpa).toFixed(2)}</span></td>
          <td><span class="chip ${esc(s.status)}">${esc(s.status)}</span></td>
          <td class="r"><div class="row-actions">
            <button class="act" data-act="view" data-id="${s.id}" title="View details" aria-label="View ${esc(s.name)}">${ICON.eye}</button>
            <button class="act" data-act="edit" data-id="${s.id}" title="Edit" aria-label="Edit ${esc(s.name)}">${ICON.edit}</button>
            <button class="act del" data-act="delete" data-id="${s.id}" data-name="${esc(s.name)}" title="Delete" aria-label="Delete ${esc(s.name)}">${ICON.trash}</button>
          </div></td>
        </tr>`).join("");
      renderPager(d);
    } catch (e) { toast(e.message, "error"); }
  }

  function renderPager(d) {
    const from = d.total ? (d.page - 1) * d.per_page + 1 : 0, to = Math.min(d.total, d.page * d.per_page);
    $("#pagerInfo").textContent = d.total ? `Showing ${from}–${to} of ${d.total} students` : "0 students";
    const btns = [`<button class="pg" data-p="${d.page - 1}" ${d.page <= 1 ? "disabled" : ""}>Prev</button>`];
    for (let i = 1; i <= d.pages; i++) {
      if (i === 1 || i === d.pages || Math.abs(i - d.page) <= 1) btns.push(`<button class="pg ${i === d.page ? "on" : ""}" data-p="${i}">${i}</button>`);
      else if (btns[btns.length - 1] !== "<span>…</span>") btns.push("<span>…</span>");
    }
    btns.push(`<button class="pg" data-p="${d.page + 1}" ${d.page >= d.pages ? "disabled" : ""}>Next</button>`);
    $("#pagerBtns").innerHTML = d.pages > 1 ? btns.join("") : "";
  }
  $("#pagerBtns").addEventListener("click", (e) => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { state.page = +b.dataset.p; loadStudents(); } });

  let timer;
  $("#search").addEventListener("input", (e) => { clearTimeout(timer); timer = setTimeout(() => { state.q = e.target.value.trim(); state.page = 1; loadStudents(); }, 250); });
  $("#filterCourse").addEventListener("change", (e) => { state.course = e.target.value; state.page = 1; loadStudents(); });
  $("#filterStatus").addEventListener("change", (e) => { state.status = e.target.value; state.page = 1; loadStudents(); });
  $("#sortBy").addEventListener("change", (e) => { [state.sort, state.order] = e.target.value.split(":"); state.page = 1; loadStudents(); });

  $("#tbody").addEventListener("click", (e) => {
    const b = e.target.closest("[data-act]"); if (!b) return;
    const id = b.dataset.id;
    if (b.dataset.act === "view") showDetails(id);
    if (b.dataset.act === "edit") openForm(id);
    if (b.dataset.act === "delete") askDelete(id, b.dataset.name);
  });

  /* ---------- details ---------- */
  async function showDetails(id) {
    try {
      const s = await api("/api/students/" + id);
      state.current = s;
      $("#viewBody").innerHTML = `
        <div class="detail-hero">${avatar(s.name)}<div><h3>${esc(s.name)}</h3><p>${esc(s.course)} · ${yearLabel(s.year)}</p></div></div>
        <div class="detail-grid">
          <div><span>Roll number</span><b>${esc(s.roll_no)}</b></div>
          <div><span>Status</span><b><span class="chip ${esc(s.status)}">${esc(s.status)}</span></b></div>
          <div><span>Email</span><b>${esc(s.email)}</b></div>
          <div><span>Phone</span><b>${esc(s.phone)}</b></div>
          <div><span>Gender</span><b>${esc(s.gender)}</b></div>
          <div><span>Date of birth</span><b>${fmtDate(s.dob)}</b></div>
          <div><span>CGPA</span><b class="cgpa ${cgpaClass(s.cgpa)}">${Number(s.cgpa).toFixed(2)}</b></div>
          <div><span>Added on</span><b>${fmtDate(s.created_at)}</b></div>
          <div class="full"><span>Address</span><b>${esc(s.address) || "—"}</b></div>
        </div>`;
      openModal("#viewModal");
    } catch (e) { toast(e.message, "error"); }
  }
  $("#viewEdit").addEventListener("click", () => { if (state.current) openForm(state.current.id); });

  /* ---------- add / edit form ---------- */
  const FIELDS = ["name", "roll_no", "email", "phone", "gender", "dob", "course", "year", "cgpa", "status", "address"];

  function clearErrors() { $$("#studentForm .field").forEach((f) => { f.classList.remove("invalid"); $(".err", f).textContent = ""; }); }
  function showErrors(errors) {
    let first = null;
    Object.entries(errors).forEach(([k, msg]) => {
      const input = $("#f_" + k); if (!input) return;
      const f = input.closest(".field"); f.classList.add("invalid"); $(".err", f).textContent = msg;
      if (!first) first = input;
    });
    if (first) first.focus();
  }

  async function openForm(id) {
    closeModals();
    clearErrors();
    $("#studentForm").reset();
    $("#f_id").value = "";
    $("#f_status").value = "Active";
    $("#formTitle").textContent = id ? "Edit student" : "Add student";
    $("#saveBtn").textContent = id ? "Save changes" : "Save student";
    if (id) {
      try {
        const s = await api("/api/students/" + id);
        $("#f_id").value = s.id;
        FIELDS.forEach((k) => { $("#f_" + k).value = s[k] ?? ""; });
      } catch (e) { return toast(e.message, "error"); }
    }
    openModal("#formModal");
    setTimeout(() => $("#f_name").focus(), 50);
  }
  $("#addBtn").addEventListener("click", () => openForm());
  $("#navAdd").addEventListener("click", () => { closeSidebar(); openForm(); });
  $("#emptyAdd").addEventListener("click", () => openForm());

  // quick client-side check (server validates again)
  function localValidate(d) {
    const e = {};
    if (d.name.trim().length < 2) e.name = "Enter the student's full name.";
    if (!/^[A-Za-z0-9\-_/]{3,20}$/.test(d.roll_no.trim())) e.roll_no = "Use 3-20 letters, numbers, - or _.";
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(d.email.trim())) e.email = "Enter a valid email address.";
    if (!/^\d{10,13}$/.test(d.phone.replace(/[\s\-+()]/g, ""))) e.phone = "Enter a valid phone number (10 digits).";
    if (!d.gender) e.gender = "Select a gender.";
    if (!d.course) e.course = "Select a course.";
    if (!d.year) e.year = "Select a year.";
    if (d.cgpa === "" || isNaN(d.cgpa) || d.cgpa < 0 || d.cgpa > 10) e.cgpa = "CGPA must be a number from 0 to 10.";
    return e;
  }

  $("#studentForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    clearErrors();
    const data = {}; FIELDS.forEach((k) => (data[k] = $("#f_" + k).value));
    const local = localValidate(data);
    if (Object.keys(local).length) return showErrors(local);

    const id = $("#f_id").value, btn = $("#saveBtn"), label = btn.textContent;
    btn.disabled = true; btn.textContent = "Saving…";
    try {
      const r = await api(id ? "/api/students/" + id : "/api/students", { method: id ? "PUT" : "POST", body: data });
      closeModals();
      toast(r.message);
      refresh();
    } catch (e) {
      if (e.errors && Object.keys(e.errors).length) showErrors(e.errors); else toast(e.message, "error");
    } finally { btn.disabled = false; btn.textContent = label; }
  });

  /* ---------- delete ---------- */
  function askDelete(id, name) {
    state.pendingDelete = id;
    $("#confirmText").textContent = `${name}'s record will be removed permanently. This cannot be undone.`;
    openModal("#confirmModal");
  }
  $("#confirmYes").addEventListener("click", async () => {
    const id = state.pendingDelete; if (!id) return;
    try {
      const r = await api("/api/students/" + id, { method: "DELETE" });
      closeModals(); toast(r.message); state.pendingDelete = null; refresh();
    } catch (e) { toast(e.message, "error"); }
  });

  function refresh() { if (location.hash === "#/students") loadStudents(); else loadStats(); }

  /* ---------- start ---------- */
  if (!location.hash) history.replaceState(null, "", "#/dashboard");
  route();
})();
