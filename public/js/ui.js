// Shared nav + toast used across pages.
import { auth, api } from "./api.js";

export function toast(msg, kind = "") {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.className = "show " + kind;
  clearTimeout(el._t);
  el._t = setTimeout(() => (el.className = ""), 2800);
}

const STAFF = ["admin", "super_admin"];

export async function mountNav(active = "") {
  const user = auth.user;
  const links = [{ k: "shop", label: "Shop", href: "shop.html" }];

  if (auth.isLoggedIn) {
    const role = user?.role;
    if (role === "customer") {
      links.push({ k: "cart", label: "Cart", href: "cart.html", cart: true });
      links.push({ k: "account", label: "Account", href: "account.html" });
    }
    if (STAFF.includes(role)) {
      links.push({ k: "admin", label: "Dashboard", href: "admin.html" });
    }
    links.push({ k: "logout", label: "Logout", href: "#" });
  } else {
    links.push({ k: "login", label: "Login", href: "login.html" });
    links.push({ k: "signup", label: "Sign Up", href: "signup.html" });
  }

  const nav = document.createElement("nav");
  nav.className = "nav";
  nav.innerHTML = `
    <a class="brand" href="/">Shankis Tea</a>
    <div class="links">
      ${links
        .map(
          (l) =>
            `<a href="${l.href}" data-k="${l.k}" class="${l.k === active ? "active" : ""}">${l.label}${
              l.cart ? ' <span class="cart-count hidden" id="navCartCount">0</span>' : ""
            }</a>`
        )
        .join("")}
    </div>`;
  document.body.prepend(nav);

  nav.querySelector('[data-k="logout"]')?.addEventListener("click", (e) => {
    e.preventDefault();
    auth.logout();
    window.location.href = "/";
  });

  if (auth.isLoggedIn && user?.role === "customer") refreshCartCount();
}

export async function refreshCartCount() {
  try {
    const cart = await api.cart();
    const el = document.getElementById("navCartCount");
    if (el) {
      el.textContent = cart.item_count;
      el.classList.toggle("hidden", cart.item_count === 0);
    }
  } catch {
    /* not a customer / not logged in */
  }
}
