// carrito-global.js
// Sistema de carrito compartido entre páginas

let carritoGlobal = [];

// Cargar carrito desde el backend y sincronizar con sessionStorage
async function inicializarCarrito() {
    try {
        // Intentar obtener del backend
        const response = await fetch("http://127.0.0.1:8000/carrito");
        const productosCarrito = await response.json();
        
        carritoGlobal = productosCarrito;
        
        // Guardar en sessionStorage para persistencia
        sessionStorage.setItem("carrito", JSON.stringify(carritoGlobal));
        
        // Actualizar UI del dropdown
        actualizarDropdownCarrito();
        
        console.log("Carrito inicializado:", carritoGlobal);
    } catch (error) {
        console.error("Error al inicializar carrito:", error);
        // Si falla, intentar cargar desde sessionStorage
        const carritoLocal = sessionStorage.getItem("carrito");
        if (carritoLocal) {
            carritoGlobal = JSON.parse(carritoLocal);
            actualizarDropdownCarrito();
        }
    }
}

// Actualizar el dropdown del carrito en el navbar
function actualizarDropdownCarrito() {
    const cartProductsContainer = document.getElementById("cart-products");
    const emptyMessage = document.getElementById("empty-cart-message");
    const cartTotal = document.getElementById("cart-total");
    const cartNotificationBadge = document.getElementById("cart-notification-badge");
    
    if (!cartProductsContainer) return; // Si no existe el elemento, salir
    
    // Limpiar contenido
    cartProductsContainer.innerHTML = "";
    
    if (carritoGlobal.length === 0) {
        // Mostrar mensaje de carrito vacío
        cartProductsContainer.innerHTML = '<li class="dropdown-item text-muted text-center" id="empty-cart-message">El carrito está vacío.</li>';
        cartTotal.textContent = "$0";
        
        // Ocultar indicador de notificación
        if (cartNotificationBadge) {
            cartNotificationBadge.classList.remove("active");
        }
    } else {
        // Mostrar productos
        let total = 0;
        
        carritoGlobal.forEach((producto, index) => {
            const cantidad = producto.cantidad || 1;
            const subtotal = producto.precio * cantidad;
            total += subtotal;
            
            const item = document.createElement("li");
            item.className = "dropdown-item d-flex align-items-center justify-content-between py-2";
            item.innerHTML = `
                <div class="d-flex align-items-center flex-grow-1">
                    <img src="${producto.imagen || 'https://via.placeholder.com/40'}" 
                         width="40" height="40" 
                         class="rounded me-2" 
                         style="object-fit: cover;">
                    <div class="flex-grow-1">
                        <div class="fw-bold text-dark" style="font-size: 0.9rem;">${producto.nombre}</div>
                        <small class="text-muted">
                            ${cantidad} x $${producto.precio.toLocaleString('es-CL')}
                        </small>
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-danger ms-2" 
                        onclick="eliminarDelCarritoDropdown('${producto._id}')" 
                        title="Eliminar">
                    <i class="fas fa-trash-alt"></i>
                </button>
            `;
            cartProductsContainer.appendChild(item);
        });
        
        // Actualizar total
        cartTotal.textContent = `$${total.toLocaleString('es-CL')}`;
        
        // Mostrar indicador de notificación
        if (cartNotificationBadge) {
            cartNotificationBadge.classList.add("active");
        }
    }
}

// Agregar producto al carrito (desde cualquier página)
async function agregarAlCarritoGlobal(id, nombre, precio, imagen) {
    try {
        // Verificar si el producto ya está en el carrito
        const productoExistente = carritoGlobal.find(p => p.nombre === nombre);
        
        if (productoExistente) {
            alert("Este producto ya está en tu carrito 🛒");
            return false;
        }
        
        // Agregar al backend
        const response = await fetch("http://127.0.0.1:8000/carrito", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                nombre, 
                precio, 
                imagen,
                cantidad: 1 
            })
        });

        if (response.ok) {
            const result = await response.json();
            
            // Agregar al carrito global
            carritoGlobal.push({
                _id: result._id,
                nombre,
                precio,
                imagen,
                cantidad: 1
            });
            
            // Actualizar sessionStorage
            sessionStorage.setItem("carrito", JSON.stringify(carritoGlobal));
            
            // Actualizar dropdown
            actualizarDropdownCarrito();
            
            console.log("Producto agregado al carrito:", nombre);
            return true;
        } else {
            alert("No se pudo agregar el producto al carrito ❌");
            return false;
        }
    } catch (error) {
        console.error("Error al agregar al carrito:", error);
        alert("Error al agregar al carrito");
        return false;
    }
}

// Eliminar producto del carrito desde el dropdown
async function eliminarDelCarritoDropdown(idProducto) {
    try {
        // Eliminar del backend
        const response = await fetch(`http://127.0.0.1:8000/carrito/${idProducto}`, {
            method: "DELETE"
        });

        if (response.ok) {
            // Eliminar del carrito global
            carritoGlobal = carritoGlobal.filter(p => p._id !== idProducto);
            
            // Actualizar sessionStorage
            sessionStorage.setItem("carrito", JSON.stringify(carritoGlobal));
            
            // Actualizar dropdown
            actualizarDropdownCarrito();
            
            console.log("Producto eliminado del carrito");
            
            // Si estamos en la página del carrito, recargar
            if (window.location.pathname.includes("Carrito.html")) {
                window.location.reload();
            }
        } else {
            alert("Error al eliminar el producto ❌");
        }
    } catch (error) {
        console.error("Error al eliminar del carrito:", error);
        alert("Error al eliminar del carrito");
    }
}

// Verificar si un producto está en el carrito (por nombre o ID)
function estaEnCarrito(identificador) {
    return carritoGlobal.some(p => 
        p._id === identificador || 
        p.nombre === identificador
    );
}

// Obtener cantidad de items en el carrito
function obtenerCantidadItems() {
    return carritoGlobal.reduce((total, p) => total + (p.cantidad || 1), 0);
}

// Vaciar carrito completo
async function vaciarCarritoCompleto() {
    try {
        const response = await fetch("http://127.0.0.1:8000/carrito", {
            method: "DELETE"
        });

        if (response.ok) {
            carritoGlobal = [];
            sessionStorage.removeItem("carrito");
            actualizarDropdownCarrito();
            console.log("Carrito vaciado");
        }
    } catch (error) {
        console.error("Error al vaciar carrito:", error);
    }
}

// Inicializar el carrito cuando se carga cualquier página
document.addEventListener("DOMContentLoaded", function() {
    inicializarCarrito();
});