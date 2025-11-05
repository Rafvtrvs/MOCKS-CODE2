// Utilidad: obtener email de usuario desde localStorage de forma robusta
function cg_obtenerUsuarioEmail() {
  let usuarioEmail = localStorage.getItem("usuarioEmail");
  if (!usuarioEmail) {
    const usuarioLocal = localStorage.getItem("usuario");
    if (usuarioLocal) {
      try {
        const usuarioObj = JSON.parse(usuarioLocal);
        if (usuarioObj && typeof usuarioObj === "object" && usuarioObj.correo) {
          usuarioEmail = usuarioObj.correo;
          localStorage.setItem("usuarioEmail", usuarioEmail);
        }
      } catch (e) {
        if (typeof usuarioLocal === "string" && usuarioLocal.includes("@")) {
          usuarioEmail = usuarioLocal;
          localStorage.setItem("usuarioEmail", usuarioEmail);
        }
      }
    }
  }
  return usuarioEmail || null;
}

// Llamada al backend para obtener carrito actual
async function cg_fetchCarrito() {
  try {
    const usuarioEmail = cg_obtenerUsuarioEmail();
    const url = usuarioEmail
      ? `http://127.0.0.1:8000/carrito?usuario_email=${encodeURIComponent(usuarioEmail)}`
      : `http://127.0.0.1:8000/carrito`;
    const resp = await fetch(url);
    if (!resp.ok) return [];
    const items = await resp.json();
    return Array.isArray(items) ? items : [];
  } catch (e) {
    console.error("Error cargando carrito:", e);
    return [];
  }
}

// Eliminar item del carrito y refrescar
async function cg_eliminarItemCarrito(id) {
  try {
    const usuarioEmail = cg_obtenerUsuarioEmail();
    const url = usuarioEmail
      ? `http://127.0.0.1:8000/carrito/${id}?usuario_email=${encodeURIComponent(usuarioEmail)}`
      : `http://127.0.0.1:8000/carrito/${id}`;
    await fetch(url, { method: "DELETE" });
    cg_initCartDropdown();
  } catch (e) {
    console.error("Error eliminando item del carrito:", e);
  }
}

// Render del dropdown del carrito
function cg_renderCartDropdown(items) {
  const container = document.getElementById("cart-items-container");
  const listWrapper = document.getElementById("cart-products");
  const emptyMsg = document.getElementById("empty-cart-message");
  const totalEl = document.getElementById("cart-total");

  if (!container) return; // No hay dropdown en esta página

  if (listWrapper) listWrapper.innerHTML = "";

  if (!items || items.length === 0) {
    if (emptyMsg) emptyMsg.style.display = "block";
    if (totalEl) totalEl.textContent = "$0";
    return;
  }

  if (emptyMsg) emptyMsg.style.display = "none";

  let total = 0;
  const frag = document.createDocumentFragment();

  items.forEach((p) => {
    const li = document.createElement("li");
    li.className = "dropdown-item d-flex align-items-center gap-2";

    const img = document.createElement("img");
    img.src = p.imagen || "https://via.placeholder.com/40";
    img.alt = p.nombre || "Producto";
    img.style.width = "40px";
    img.style.height = "40px";
    img.style.objectFit = "cover";
    img.className = "rounded";

    const textWrap = document.createElement("div");
    textWrap.className = "flex-fill";
    const nameEl = document.createElement("div");
    nameEl.textContent = p.nombre || "Producto";
    nameEl.className = "small";
    const priceEl = document.createElement("div");
    const precioNum = parseInt(p.precio) || 0;
    priceEl.textContent = new Intl.NumberFormat("es-CL", { style: "currency", currency: "CLP", minimumFractionDigits: 0 }).format(precioNum);
    priceEl.className = "small text-success";
    textWrap.appendChild(nameEl);
    textWrap.appendChild(priceEl);

    const btn = document.createElement("button");
    btn.className = "btn btn-sm btn-outline-danger";
    btn.innerHTML = '<i class="fas fa-trash"></i>';
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      if (p._id) cg_eliminarItemCarrito(p._id);
    });

    li.appendChild(img);
    li.appendChild(textWrap);
    li.appendChild(btn);
    frag.appendChild(li);

    total += precioNum || 0;
  });

  if (listWrapper) listWrapper.appendChild(frag);
  if (totalEl) {
    totalEl.textContent = new Intl.NumberFormat("es-CL", { style: "currency", currency: "CLP", minimumFractionDigits: 0 }).format(total);
  }
}

// Punto de notificación en ícono del carrito
function cg_updateCartDot(items) {
  const dot = document.getElementById("cart-notification-badge") || document.getElementById("cart-indicator");
  if (!dot) return;
  const count = Array.isArray(items) ? items.length : 0;
  if (dot.id === "cart-notification-badge") {
    // Este usa clase active para mostrar/ocultar
    if (count > 0) {
      dot.classList.add("active");
    } else {
      dot.classList.remove("active");
    }
  } else {
    // Variante simple: toggle display
    dot.style.display = count > 0 ? "inline-block" : "none";
  }
}

// Inicializar dropdown (cargar y renderizar)
async function cg_initCartDropdown() {
  const items = await cg_fetchCarrito();
  cg_renderCartDropdown(items);
  cg_updateCartDot(items);
}

// Auto inicialización al cargar
document.addEventListener("DOMContentLoaded", () => {
  // Solo inicializar si existe el contenedor del dropdown en la página
  if (document.getElementById("cart-items-container")) {
    cg_initCartDropdown();
  }
});

// Limpiar UI del carrito (para cierre de sesión)
function cg_clearCartUI() {
  try {
    const listWrapper = document.getElementById("cart-products");
    const emptyMsg = document.getElementById("empty-cart-message");
    const totalEl = document.getElementById("cart-total");
    const dot = document.getElementById("cart-notification-badge") || document.getElementById("cart-indicator");
    if (listWrapper) listWrapper.innerHTML = "<li class=\"dropdown-item text-muted text-center\" id=\"empty-cart-message\">El carrito está vacío.</li>";
    if (emptyMsg) emptyMsg.style.display = "block";
    if (totalEl) totalEl.textContent = "$0";
    if (dot) {
      if (dot.id === "cart-notification-badge") dot.classList.remove("active");
      else dot.style.display = "none";
    }
  } catch (e) {
    console.warn("No se pudo limpiar UI del carrito:", e);
  }
}

// Exponer limpiador global por si se necesita invocarlo desde otras páginas
window.cg_clearCartUI = cg_clearCartUI;


