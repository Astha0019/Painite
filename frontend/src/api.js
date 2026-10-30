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
        list: (params = {}) => {
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
            return request(`/products${qs}`);
        },
        get: (id) => request(`/products/${id}`)
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

export default api;
