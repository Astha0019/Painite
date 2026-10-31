/**
 * Centralized API Client for Painite Studio
 * Handles request headers, bearer tokens, error handling, and API endpoints.
 */

const API_BASE = (typeof window !== "undefined" && window.location.origin) 
    ? `${window.location.origin}/api` 
    : "http://127.0.0.1:5000/api";

export async function request(endpoint, options = {}) {
    const token = localStorage.getItem("painite_token");
    const headers = {
        "Content-Type": "application/json",
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
        ...(options.headers || {})
    };

    // If body is FormData, delete Content-Type so browser sets boundary
    if (options.body instanceof FormData) {
        delete headers["Content-Type"];
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 204) {
            return null;
        }

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            // If token expired, clear invalid auth
            if (response.status === 401 && token) {
                localStorage.removeItem("painite_token");
                localStorage.removeItem("painite_user");
            }
            throw new Error(data.detail || data.message || "An unexpected error occurred");
        }

        return data;
    } catch (err) {
        console.error(`[API Error] ${endpoint}:`, err);
        throw err;
    }
}

export const api = {
    auth: {
        login: (email, password) => request("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password })
        }),
        register: (name, email, password, role = "customer") => request("/auth/register", {
            method: "POST",
            body: JSON.stringify({ name, email, password, role })
        }),
        getMe: () => request("/auth/me"),
        logout: () => {
            localStorage.removeItem("painite_token");
            localStorage.removeItem("painite_user");
            return request("/auth/logout", { method: "POST" }).catch(() => {});
        }
    },
    products: {
        list: async (params = {}) => {
            const query = new URLSearchParams();
            if (params.search) query.set("search", params.search);
            if (params.category && params.category !== "All") query.set("category", params.category);
            if (params.gender && params.gender !== "All") query.set("gender", params.gender);
            if (params.size && params.size !== "All") query.set("size", params.size);
            if (params.price && params.price !== "All") query.set("price", params.price);
            if (params.collection && params.collection !== "All") query.set("collection", params.collection);
            if (params.color && params.color !== "All") query.set("color", params.color);
            if (params.sort) query.set("sort", params.sort);
            const qs = query.toString() ? `?${query.toString()}` : "";
            try {
                const res = await request(`/products${qs}`);
                if (Array.isArray(res) && res.length > 0) return res;
            } catch (err) {
                console.warn("[API Warning] /products endpoint error, utilizing client fallback:", err);
            }
            return filterPreloadedProducts(params);
        },
        get: async (id) => {
            try {
                const res = await request(`/products/${id}`);
                if (res && res.id) return res;
            } catch (err) {
                console.warn("[API Warning] /products/:id error, utilizing client fallback:", err);
            }
            const list = (typeof window !== "undefined" && window.PRELOADED_PRODUCTS) ? window.PRELOADED_PRODUCTS : [];
            return list.find(p => p.id === id) || null;
        }
    },
    orders: {
        create: (orderData) => request("/orders", {
            method: "POST",
            body: JSON.stringify(orderData)
        }),
        getMyOrders: () => request("/me/orders")
    },
    admin: {
        getStats: () => request("/admin/stats"),
        getOrders: () => request("/admin/orders"),
        updateOrderStatus: (orderId, status) => request(`/admin/orders/${orderId}`, {
            method: "PATCH",
            body: JSON.stringify({ status })
        }),
        addProduct: (productData) => request("/admin/products", {
            method: "POST",
            body: JSON.stringify(productData)
        }),
        deleteProduct: (id) => request(`/admin/products/${id}`, {
            method: "DELETE"
        })
    },
    upload: {
        uploadArtwork: (file) => {
            const formData = new FormData();
            formData.append("file", file);
            return request("/upload", {
                method: "POST",
                body: formData
            });
        }
    }
};

export function filterPreloadedProducts(params = {}) {
    const list = (typeof window !== "undefined" && Array.isArray(window.PRELOADED_PRODUCTS)) ? window.PRELOADED_PRODUCTS : [];
    let result = [...list];

    if (params.search) {
        const s = params.search.toLowerCase();
        result = result.filter(p => 
            (p.name || "").toLowerCase().includes(s) || 
            (p.description || "").toLowerCase().includes(s) || 
            (p.category || "").toLowerCase().includes(s) ||
            (p.tag || "").toLowerCase().includes(s)
        );
    }
    if (params.category && params.category !== "All") {
        const c = params.category.toLowerCase();
        result = result.filter(p => (p.category || "").toLowerCase().includes(c));
    }
    if (params.gender && params.gender !== "All") {
        const g = params.gender.toLowerCase();
        result = result.filter(p => {
            const pg = (p.gender || "Unisex").toLowerCase();
            return pg === g || pg === "unisex";
        });
    }
    if (params.size && params.size !== "All") {
        result = result.filter(p => Array.isArray(p.sizes) && p.sizes.includes(params.size));
    }
    if (params.price && params.price !== "All") {
        const pr = params.price.toLowerCase();
        if (pr === "under-999") result = result.filter(p => p.price <= 999);
        else if (pr === "1000-1499") result = result.filter(p => p.price >= 1000 && p.price <= 1499);
        else if (pr === "1500-2000") result = result.filter(p => p.price >= 1500 && p.price <= 2000);
    }
    if (params.sort) {
        if (params.sort === "price-asc") result.sort((a, b) => a.price - b.price);
        else if (params.sort === "price-desc") result.sort((a, b) => b.price - a.price);
        else if (params.sort === "discount") result.sort((a, b) => (b.discount_pct || 0) - (a.discount_pct || 0));
        else if (params.sort === "name") result.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
    }
    return result;
}

export default api;
