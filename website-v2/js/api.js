(() => {
  "use strict";

  // Same server that served the page (works for 127.0.0.1, localhost or a LAN
  // address). Opened as a local file, it falls back to the default backend.
  const baseUrl = () =>
    (window.FS_API_BASE_URL ||
      (location.protocol.startsWith("http") && location.port !== "8080" ? location.origin : "http://127.0.0.1:8000")
    ).replace(/\/+$/, "");

  class ApiError extends Error {
    constructor(message, status = null, code = null) {
      super(message);
      this.name = "ApiError";
      this.status = status;
      this.code = code;
    }
  }

  async function request(path, options = {}) {
    let response;
    try {
      response = await fetch(`${baseUrl()}${path}`, {
        ...options,
        headers: {
          Accept: "application/json",
          ...(options.body ? { "Content-Type": "application/json" } : {}),
          ...options.headers,
        },
      });
    } catch (error) {
      if (error.name === "AbortError") throw error;
      throw new ApiError("Cannot reach the Field Shift backend. Check that it is running.");
    }

    let payload;
    try {
      payload = await response.json();
    } catch {
      throw new ApiError(
        `The backend returned an unreadable response (HTTP ${response.status}).`,
        response.status
      );
    }

    if (!response.ok) {
      const detail = payload && payload.detail;
      const message =
        typeof detail === "string"
          ? detail
          : detail && typeof detail.message === "string"
            ? detail.message
            : `The backend request failed (HTTP ${response.status}).`;
      throw new ApiError(message, response.status, detail && detail.code);
    }
    return payload;
  }

  window.FS_API = Object.freeze({
    ApiError,
    getRecommendations(cellId, signal) {
      return request(`/api/cells/${encodeURIComponent(cellId)}/recommendations`, {
        signal,
      });
    },
    evaluateWeights(cellId, weights, signal) {
      return request("/api/rotations/evaluate", {
        method: "POST",
        signal,
        body: JSON.stringify({ cell_id: cellId, weights }),
      });
    },
  });
})();
