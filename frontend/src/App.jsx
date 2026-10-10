import React, { useEffect, useRef, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  CircleMarker,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "./App.css";

const LOCATION_GROUPS = [
  {
    label: "Telangana — 33 districts",
    options: [
      { label: "Telangana — State (broad location)", value: "Telangana, India" },
      { label: "Adilabad — District", value: "Adilabad, Telangana" },
      { label: "Bhadradri Kothagudem — District", value: "Bhadradri Kothagudem, Telangana" },
      { label: "Hanumakonda — District", value: "Hanumakonda, Telangana" },
      { label: "Hyderabad — District / City", value: "Hyderabad, Telangana" },
      { label: "Jagtial — District", value: "Jagtial, Telangana" },
      { label: "Jangaon — District", value: "Jangaon, Telangana" },
      { label: "Jayashankar Bhupalpally — District", value: "Jayashankar Bhupalpally, Telangana" },
      { label: "Jogulamba Gadwal — District", value: "Jogulamba Gadwal, Telangana" },
      { label: "Kamareddy — District", value: "Kamareddy, Telangana" },
      { label: "Karimnagar — District / City", value: "Karimnagar, Telangana" },
      { label: "Khammam — District / City", value: "Khammam, Telangana" },
      { label: "Komaram Bheem Asifabad — District", value: "Komaram Bheem Asifabad, Telangana" },
      { label: "Mahabubabad — District", value: "Mahabubabad, Telangana" },
      { label: "Mahbubnagar — District / City", value: "Mahbubnagar, Telangana" },
      { label: "Mancherial — District", value: "Mancherial, Telangana" },
      { label: "Medak — District", value: "Medak, Telangana" },
      { label: "Medchal-Malkajgiri — District", value: "Medchal-Malkajgiri, Telangana" },
      { label: "Mulugu — District", value: "Mulugu, Telangana" },
      { label: "Nagarkurnool — District", value: "Nagarkurnool, Telangana" },
      { label: "Nalgonda — District / City", value: "Nalgonda, Telangana" },
      { label: "Narayanpet — District", value: "Narayanpet, Telangana" },
      { label: "Nirmal — District / City", value: "Nirmal, Telangana" },
      { label: "Nizamabad — District / City", value: "Nizamabad, Telangana" },
      { label: "Peddapalli — District", value: "Peddapalli, Telangana" },
      { label: "Rajanna Sircilla — District", value: "Rajanna Sircilla, Telangana" },
      { label: "Rangareddy — District", value: "Rangareddy, Telangana" },
      { label: "Sangareddy — District / City", value: "Sangareddy, Telangana" },
      { label: "Siddipet — District / City", value: "Siddipet, Telangana" },
      { label: "Suryapet — District / City", value: "Suryapet, Telangana" },
      { label: "Vikarabad — District / City", value: "Vikarabad, Telangana" },
      { label: "Wanaparthy — District / City", value: "Wanaparthy, Telangana" },
      { label: "Warangal — District / City", value: "Warangal, Telangana" },
      { label: "Yadadri Bhuvanagiri — District", value: "Yadadri Bhuvanagiri, Telangana" },
    ],
  },
  { label: "Andhra Pradesh", options: [
    { label: "Andhra Pradesh — State (broad location)", value: "Andhra Pradesh, India" },
    { label: "Vijayawada", value: "Vijayawada, Andhra Pradesh" },
    { label: "Guntur", value: "Guntur, Andhra Pradesh" },
    { label: "Visakhapatnam", value: "Visakhapatnam, Andhra Pradesh" },
    { label: "Tirupati", value: "Tirupati, Andhra Pradesh" },
  ]},
  { label: "Arunachal Pradesh", options: [
    { label: "Arunachal Pradesh — State", value: "Arunachal Pradesh, India" },
    { label: "Itanagar", value: "Itanagar, Arunachal Pradesh" },
  ]},
  { label: "Assam", options: [
    { label: "Assam — State", value: "Assam, India" },
    { label: "Dispur", value: "Dispur, Assam" },
    { label: "Guwahati", value: "Guwahati, Assam" },
  ]},
  { label: "Bihar", options: [
    { label: "Bihar — State", value: "Bihar, India" },
    { label: "Patna", value: "Patna, Bihar" },
  ]},
  { label: "Chhattisgarh", options: [
    { label: "Chhattisgarh — State", value: "Chhattisgarh, India" },
    { label: "Raipur", value: "Raipur, Chhattisgarh" },
  ]},
  { label: "Goa", options: [
    { label: "Goa — State", value: "Goa, India" },
    { label: "Panaji", value: "Panaji, Goa" },
  ]},
  { label: "Gujarat", options: [
    { label: "Gujarat — State", value: "Gujarat, India" },
    { label: "Gandhinagar", value: "Gandhinagar, Gujarat" },
    { label: "Ahmedabad", value: "Ahmedabad, Gujarat" },
    { label: "Surat", value: "Surat, Gujarat" },
  ]},
  { label: "Haryana", options: [
    { label: "Haryana — State", value: "Haryana, India" },
    { label: "Chandigarh", value: "Chandigarh, India" },
    { label: "Gurugram", value: "Gurugram, Haryana" },
    { label: "Faridabad", value: "Faridabad, Haryana" },
  ]},
  { label: "Himachal Pradesh", options: [
    { label: "Himachal Pradesh — State", value: "Himachal Pradesh, India" },
    { label: "Shimla", value: "Shimla, Himachal Pradesh" },
  ]},
  { label: "Jharkhand", options: [
    { label: "Jharkhand — State", value: "Jharkhand, India" },
    { label: "Ranchi", value: "Ranchi, Jharkhand" },
  ]},
  { label: "Karnataka", options: [
    { label: "Karnataka — State", value: "Karnataka, India" },
    { label: "Bengaluru", value: "Bengaluru, Karnataka" },
    { label: "Mysuru", value: "Mysuru, Karnataka" },
    { label: "Kalaburagi", value: "Kalaburagi, Karnataka" },
  ]},
  { label: "Kerala", options: [
    { label: "Kerala — State", value: "Kerala, India" },
    { label: "Thiruvananthapuram", value: "Thiruvananthapuram, Kerala" },
    { label: "Kochi", value: "Kochi, Kerala" },
  ]},
  { label: "Madhya Pradesh", options: [
    { label: "Madhya Pradesh — State", value: "Madhya Pradesh, India" },
    { label: "Bhopal", value: "Bhopal, Madhya Pradesh" },
    { label: "Indore", value: "Indore, Madhya Pradesh" },
  ]},
  { label: "Maharashtra", options: [
    { label: "Maharashtra — State", value: "Maharashtra, India" },
    { label: "Mumbai", value: "Mumbai, Maharashtra" },
    { label: "Pune", value: "Pune, Maharashtra" },
    { label: "Nagpur", value: "Nagpur, Maharashtra" },
    { label: "Nashik", value: "Nashik, Maharashtra" },
  ]},
  { label: "Manipur", options: [
    { label: "Manipur — State", value: "Manipur, India" },
    { label: "Imphal", value: "Imphal, Manipur" },
  ]},
  { label: "Meghalaya", options: [
    { label: "Meghalaya — State", value: "Meghalaya, India" },
    { label: "Shillong", value: "Shillong, Meghalaya" },
  ]},
  { label: "Mizoram", options: [
    { label: "Mizoram — State", value: "Mizoram, India" },
    { label: "Aizawl", value: "Aizawl, Mizoram" },
  ]},
  { label: "Nagaland", options: [
    { label: "Nagaland — State", value: "Nagaland, India" },
    { label: "Kohima", value: "Kohima, Nagaland" },
    { label: "Dimapur", value: "Dimapur, Nagaland" },
  ]},
  { label: "Odisha", options: [
    { label: "Odisha — State", value: "Odisha, India" },
    { label: "Bhubaneswar", value: "Bhubaneswar, Odisha" },
    { label: "Cuttack", value: "Cuttack, Odisha" },
  ]},
  { label: "Punjab", options: [
    { label: "Punjab — State", value: "Punjab, India" },
    { label: "Chandigarh", value: "Chandigarh, India" },
    { label: "Ludhiana", value: "Ludhiana, Punjab" },
    { label: "Amritsar", value: "Amritsar, Punjab" },
  ]},
  { label: "Rajasthan", options: [
    { label: "Rajasthan — State", value: "Rajasthan, India" },
    { label: "Jaipur", value: "Jaipur, Rajasthan" },
  ]},
  { label: "Sikkim", options: [
    { label: "Sikkim — State", value: "Sikkim, India" },
    { label: "Gangtok", value: "Gangtok, Sikkim" },
  ]},
  { label: "Tamil Nadu", options: [
    { label: "Tamil Nadu — State", value: "Tamil Nadu, India" },
    { label: "Chennai", value: "Chennai, Tamil Nadu" },
    { label: "Coimbatore", value: "Coimbatore, Tamil Nadu" },
    { label: "Madurai", value: "Madurai, Tamil Nadu" },
  ]},
  { label: "Tripura", options: [
    { label: "Tripura — State", value: "Tripura, India" },
    { label: "Agartala", value: "Agartala, Tripura" },
  ]},
  { label: "Uttar Pradesh", options: [
    { label: "Uttar Pradesh — State", value: "Uttar Pradesh, India" },
    { label: "Lucknow", value: "Lucknow, Uttar Pradesh" },
    { label: "Varanasi", value: "Varanasi, Uttar Pradesh" },
    { label: "Noida", value: "Noida, Uttar Pradesh" },
  ]},
  { label: "Uttarakhand", options: [
    { label: "Uttarakhand — State", value: "Uttarakhand, India" },
    { label: "Dehradun", value: "Dehradun, Uttarakhand" },
  ]},
  { label: "West Bengal", options: [
    { label: "West Bengal — State", value: "West Bengal, India" },
    { label: "Kolkata", value: "Kolkata, West Bengal" },
  ]},
  { label: "Delhi — Union Territory", options: [
    { label: "Delhi", value: "Delhi, India" },
    { label: "New Delhi", value: "New Delhi, India" },
  ]},
  { label: "Jammu & Kashmir — Union Territory", options: [
    { label: "Jammu & Kashmir", value: "Jammu and Kashmir, India" },
    { label: "Srinagar", value: "Srinagar, Jammu and Kashmir" },
    { label: "Jammu", value: "Jammu, Jammu and Kashmir" },
  ]},
  { label: "Ladakh — Union Territory", options: [
    { label: "Ladakh", value: "Ladakh, India" },
    { label: "Leh", value: "Leh, Ladakh" },
  ]},
  { label: "Puducherry — Union Territory", options: [
    { label: "Puducherry", value: "Puducherry, India" },
  ]},
  { label: "Chandigarh — Union Territory", options: [
    { label: "Chandigarh", value: "Chandigarh, India" },
  ]},
  { label: "Andaman & Nicobar Islands — Union Territory", options: [
    { label: "Port Blair", value: "Port Blair, Andaman and Nicobar Islands" },
  ]},
  { label: "Dadra & Nagar Haveli and Daman & Diu — Union Territory", options: [
    { label: "Daman", value: "Daman, India" },
    { label: "Silvassa", value: "Silvassa, India" },
  ]},
  { label: "Lakshadweep — Union Territory", options: [
    { label: "Kavaratti", value: "Kavaratti, Lakshadweep" },
  ]},
];

const LOCATION_VALUES = new Set(
  LOCATION_GROUPS.flatMap((group) => group.options.map((option) => option.value))
);


function getRouteCoordinates(route) {
  const geometry = route?.geometry;

  if (Array.isArray(geometry)) {
    return geometry;
  }

  if (Array.isArray(geometry?.coordinates)) {
    return geometry.coordinates;
  }

  return [];
}


function App() {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [transportMode, setTransportMode] = useState("");

  const [crop, setCrop] = useState("");
  const [quantity, setQuantity] = useState("");
  const [cargoValue, setCargoValue] = useState("");
  const [fragility, setFragility] = useState("");

  const [loading, setLoading] = useState(false);
  const [routeData, setRouteData] = useState(null);
  const [error, setError] = useState("");

  // What-if scenario simulation state
  const [simulationCrop, setSimulationCrop] = useState("");
  const [simulationQuantity, setSimulationQuantity] = useState("");
  const [simulationCargoValue, setSimulationCargoValue] = useState("");
  const [simulationFragility, setSimulationFragility] = useState("");
  const [simulationLoading, setSimulationLoading] = useState(false);
  const [simulationData, setSimulationData] = useState(null);
  const [simulationError, setSimulationError] = useState("");

  // Live-condition / re-routing state
  const [liveRefresh, setLiveRefresh] = useState({
    refreshing: false,
    lastUpdated: null,
    previousRouteId: null,
    changed: false,
    refreshCount: 0,
    refreshStartedAt: null,
    lastRefreshDurationSeconds: null,
  });

  const [refreshElapsedSeconds, setRefreshElapsedSeconds] = useState(0);

  // Decision intelligence / usability features
  const [language, setLanguage] = useState("en");
  const [recommendationTimeline, setRecommendationTimeline] = useState([]);
  const [stopPlan, setStopPlan] = useState(null);
  const [stopPlanLoading, setStopPlanLoading] = useState(false);
  const [stopPlanError, setStopPlanError] = useState("");

  const activeRequestRef = useRef(null);
  const liveRefreshingRef = useRef(false);

  const buildRoutesRequestUrl = (cargoCrop = crop, cargoQuantity = quantity, cargoValueInput = cargoValue, cargoFragility = fragility) => {
    return (
      `/api/routes` +
      `?start=${encodeURIComponent(start)}` +
      `&end=${encodeURIComponent(end)}` +
      `&transport_mode=${encodeURIComponent(transportMode)}` +
      `&crop=${encodeURIComponent(cargoCrop)}` +
      `&quantity_kg=${encodeURIComponent(cargoQuantity)}` +
      `&cargo_value=${encodeURIComponent(cargoValueInput)}` +
      `&fragility=${encodeURIComponent(cargoFragility)}`
    );
  };

  const fetchRoutes = async (
    cargoCrop,
    cargoQuantity,
    cargoValueInput,
    cargoFragility
  ) => {
    if (activeRequestRef.current) {
      activeRequestRef.current.abort();
    }

    const controller = new AbortController();
    activeRequestRef.current = controller;
    let timedOut = false;
    const timeoutId = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 90000);

    try {
      const response = await fetch(
        buildRoutesRequestUrl(
          cargoCrop,
          cargoQuantity,
          cargoValueInput,
          cargoFragility
        ),
        {
          cache: "no-store",
          signal: controller.signal,
        }
      );

      const contentType = response.headers.get("content-type") || "";
      const data = contentType.includes("application/json")
        ? await response.json()
        : null;

      if (!response.ok) {
        const backendDetail =
          data?.detail ||
          data?.message ||
          `HTTP ${response.status}`;
        throw new Error(`Backend request failed: ${backendDetail}`);
      }

      if (!data || data.success === false) {
        throw new Error(
          data?.detail ||
          data?.message ||
          "Backend returned an invalid route-analysis response."
        );
      }

      return data;
    } catch (error) {
      if (error?.name === "AbortError") {
        if (timedOut) {
          const timeoutError = new Error(
            "Live route analysis timed out after 90 seconds. The previous successful analysis is still safe to display."
          );
          timeoutError.code = "REQUEST_TIMEOUT";
          throw timeoutError;
        }

        const cancelledError = new Error("Live request cancelled.");
        cancelledError.code = "REQUEST_CANCELLED";
        throw cancelledError;
      }
      throw error;
    } finally {
      window.clearTimeout(timeoutId);
      if (activeRequestRef.current === controller) {
        activeRequestRef.current = null;
      }
    }
  };

  const updateShipment = () => {
    // Return the shipment form to its original blank state.
    setStart("");
    setEnd("");
    setTransportMode("");
    setCrop("");
    setQuantity("");
    setCargoValue("");
    setFragility("");

    // Clear What-If inputs and results as well.
    setSimulationCrop("");
    setSimulationQuantity("");
    setSimulationCargoValue("");
    setSimulationFragility("");
    setSimulationData(null);
    setSimulationError("");
    setSimulationLoading(false);

    // Clear the current analysis and all live/decision state.
    setRouteData(null);
    setLiveRefresh({
      refreshing: false,
      lastUpdated: null,
      previousRouteId: null,
      changed: false,
      refreshCount: 0,
      refreshStartedAt: null,
      lastRefreshDurationSeconds: null,
    });
    setRefreshElapsedSeconds(0);
    setRecommendationTimeline([]);
    setStopPlan(null);
    setStopPlanLoading(false);
    setStopPlanError("");
    setError("");

    window.setTimeout(() => {
      document.getElementById("shipment-inputs")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
      document.getElementById("start-location")?.focus();
    }, 0);
  };

  const analyzeRoute = async () => {
    if (!start || start === "__custom__" || !end || end === "__custom__") {
      setError("Please choose or enter an origin and destination.");
      return;
    }

    if (!transportMode) {
      setError("Please choose a transport mode.");
      return;
    }

    if (!crop) {
      setError("Please choose a cargo type.");
      return;
    }

    if (!fragility) {
      setError("Please choose cargo fragility.");
      return;
    }

    if (!quantity || Number(quantity) <= 0) {
      setError("Please enter the cargo quantity.");
      return;
    }

    if (!cargoValue || Number(cargoValue) <= 0) {
      setError("Please enter the cargo value.");
      return;
    }

    if (!crop) {
      setError("Please select a crop / cargo type first.");
      return;
    }

    if (Number(quantity) <= 0 || Number(cargoValue) <= 0) {
      setError("Quantity and cargo value must be greater than zero.");
      return;
    }

    setLoading(true);
    setError("");
    setLiveRefresh({
      refreshing: false,
      lastUpdated: null,
      previousRouteId: null,
      changed: false,
      refreshCount: 0,
      refreshStartedAt: null,
      lastRefreshDurationSeconds: null,
    });
    setRefreshElapsedSeconds(0);

    try {
      const data = await fetchRoutes(crop, quantity, cargoValue, fragility);
      const updatedAt = new Date();
      setRouteData(data);
      liveRefreshingRef.current = false;
      setRefreshElapsedSeconds(0);
      setLiveRefresh((current) => ({
        ...current,
        refreshing: false,
        lastUpdated: updatedAt,
        previousRouteId: null,
        changed: false,
        refreshCount: current.refreshCount + 1,
        refreshStartedAt: null,
        lastRefreshDurationSeconds: current.refreshStartedAt
          ? Math.max(0, Math.round((updatedAt.getTime() - current.refreshStartedAt) / 1000))
          : null,
      }));
    } catch (err) {
      console.error(err);
      setError(
        `Unable to analyze routes: ${
          err?.message ||
          "Unknown error"
        }`
      );
    } finally {
      setLoading(false);
    }
  };

  const refreshWholeApp = async () => {
    if (loading) return;

    // Refresh uses the values already entered in the form. If a refresh is
    // currently running, cancel that request and immediately start a new one.
    if (liveRefreshingRef.current && activeRequestRef.current) {
      activeRequestRef.current.abort();
      activeRequestRef.current = null;
      liveRefreshingRef.current = false;
      setLiveRefresh((current) => ({ ...current, refreshing: false }));
      await new Promise((resolve) => window.setTimeout(resolve, 0));
    }

    if (routeData && crop) {
      await refreshLiveRoutes(false);
    } else {
      await analyzeRoute();
    }
  };

  const refreshLiveRoutes = async (automatic = false) => {
    if (!routeData || !crop || liveRefreshingRef.current) return;

    const previousRouteId = Number(
      routeData?.recommendation?.route_id ?? routeData?.routes?.[0]?.route_id
    );

    const startedAt = Date.now();
    liveRefreshingRef.current = true;
    setRefreshElapsedSeconds(0);
    setLiveRefresh((current) => ({
      ...current,
      refreshing: true,
      previousRouteId,
      refreshStartedAt: startedAt,
      lastRefreshDurationSeconds: null,
    }));

    if (!automatic) {
      setError("");
    }

    try {
      const data = await fetchRoutes(crop, quantity, cargoValue, fragility);
      const currentRouteId = Number(
        data?.recommendation?.route_id ?? data?.routes?.[0]?.route_id
      );

      const updatedAt = new Date();
      setRouteData(data);
      liveRefreshingRef.current = false;
      setRefreshElapsedSeconds(0);
      setLiveRefresh((current) => ({
        ...current,
        refreshing: false,
        lastUpdated: updatedAt,
        previousRouteId,
        changed: previousRouteId !== currentRouteId,
        refreshCount: current.refreshCount + 1,
        refreshStartedAt: null,
        lastRefreshDurationSeconds: Math.max(0, Math.round((updatedAt.getTime() - startedAt) / 1000)),
      }));
    } catch (err) {
      console.error(err);
      if (err?.code === "REQUEST_CANCELLED") {
        return;
      }
      liveRefreshingRef.current = false;
      setRefreshElapsedSeconds(0);
      setLiveRefresh((current) => ({
        ...current,
        refreshing: false,
        refreshStartedAt: null,
        lastRefreshDurationSeconds: current.refreshStartedAt
          ? Math.max(0, Math.round((Date.now() - current.refreshStartedAt) / 1000))
          : null,
      }));
      setError(
        "Live refresh failed. The last successful live route analysis is still displayed."
      );
    }
  };

  const simulateScenario = async () => {
    if (!simulationCrop) {
      setSimulationError("Please select a crop / cargo type first.");
      return;
    }
    if (!simulationQuantity || Number(simulationQuantity) <= 0) {
      setSimulationError("Please enter the quantity in kg.");
      return;
    }
    if (!simulationCargoValue || Number(simulationCargoValue) <= 0) {
      setSimulationError("Please enter the cargo value.");
      return;
    }
    if (!simulationFragility) {
      setSimulationError("Please select the cargo fragility.");
      return;
    }

    setSimulationLoading(true);
    setSimulationError("");

    try {
      // What-If uses the already completed live route analysis. The backend
      // recalculates only cargo-dependent risk/economic values, so it does not
      // call Nominatim, OSRM, TomTom or Open-Meteo again.
      const response = await fetch("/api/simulate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        cache: "no-store",
        body: JSON.stringify({
          ...routeData,
          cargo: {
            crop: simulationCrop,
            quantity_kg: Number(simulationQuantity),
            cargo_value: Number(simulationCargoValue),
            fragility: simulationFragility,
          },
        }),
      });

      const contentType = response.headers.get("content-type") || "";
      const data = contentType.includes("application/json")
        ? await response.json()
        : null;

      if (!response.ok || !data?.success) {
        throw new Error(
          data?.detail ||
          `Scenario request failed (HTTP ${response.status}).`
        );
      }

      const backendRecommendation = data?.recommendation || null;
      const recommendedRoute =
        data?.routes?.find(
          (route) =>
            Number(route.route_id) ===
            Number(backendRecommendation?.route_id)
        ) || null;

      setSimulationData({
        ...data,
        mode: "LIVE_EXTERNAL_DATA",
        cargo: {
          crop: simulationCrop,
          quantity_kg: Number(simulationQuantity),
          cargo_value: Number(simulationCargoValue),
          fragility: simulationFragility,
        },
        recommendation: recommendedRoute,
      });
    } catch (err) {
      console.error(err);
      setSimulationError(
        err?.message ||
        "Unable to calculate the scenario from live external data."
      );
    } finally {
      setSimulationLoading(false);
    }
  };

  const clearSimulation = () => {
    setSimulationData(null);
    setSimulationError("");
  };

  const UI_TEXT = {
    en: {
      language: "Language",
      spoilage: "SPOILAGE CLOCK",
      estimatedShelf: "MODELED SHELF-LIFE BASELINE",
      arrival: "ESTIMATED ARRIVAL",
      remaining: "ESTIMATED SHELF LIFE REMAINING",
      baselineNote: "Planning estimate only — not a live shelf-life measurement or guarantee.",
      tie: "NEAR-TIE DETECTED",
      noTie: "NO NEAR-TIE",
      tradeoff: "ROUTE TRADE-OFF",
      timeline: "RECOMMENDATION TIMELINE",
      current: "CURRENT",
      previous: "PREVIOUS",
      driverSummary: "DRIVER SUMMARY",
      download: "DOWNLOAD DRIVER SUMMARY",
      stopPlanning: "STOP PLANNING",
      stopLoading: "Finding mapped logistics stops...",
      noStops: "No verified mapped stop candidates were returned for this corridor.",
      mappedCandidate: "Mapped OSM candidate — verify suitability before use.",
      recommendation: "RECOMMENDATION",
    },
    hi: {
      language: "भाषा",
      spoilage: "खराब होने की घड़ी",
      estimatedShelf: "मॉडल की शेल्फ-लाइफ आधाररेखा",
      arrival: "अनुमानित आगमन",
      remaining: "आगमन पर अनुमानित शेष शेल्फ-लाइफ",
      baselineNote: "केवल योजना अनुमान — लाइव शेल्फ-लाइफ माप या गारंटी नहीं।",
      tie: "लगभग बराबर मार्ग",
      noTie: "लगभग बराबर मार्ग नहीं",
      tradeoff: "मार्ग तुलना",
      timeline: "सिफारिश समयरेखा",
      current: "वर्तमान",
      previous: "पिछला",
      driverSummary: "ड्राइवर सारांश",
      download: "ड्राइवर सारांश डाउनलोड करें",
      stopPlanning: "स्टॉप योजना",
      stopLoading: "मैप किए गए लॉजिस्टिक्स स्टॉप खोज रहे हैं...",
      noStops: "इस कॉरिडोर के लिए कोई सत्यापित मैप किया गया स्टॉप नहीं मिला।",
      mappedCandidate: "मैप किया गया OSM उम्मीदवार — उपयोग से पहले सत्यापित करें।",
      recommendation: "सिफारिश",
    },
    te: {
      language: "భాష",
      spoilage: "చెడిపోవు గడియారం",
      estimatedShelf: "మోడల్ షెల్ఫ్-లైఫ్ ప్రాథమిక అంచనా",
      arrival: "అంచనా రాక సమయం",
      remaining: "రాక సమయానికి అంచనా మిగిలిన షెల్ఫ్-లైఫ్",
      baselineNote: "ప్లానింగ్ అంచనా మాత్రమే — లైవ్ షెల్ఫ్-లైఫ్ కొలత లేదా హామీ కాదు.",
      tie: "దాదాపు సమానమైన మార్గాలు",
      noTie: "దాదాపు సమానమైన మార్గాలు లేవు",
      tradeoff: "మార్గం పోలిక",
      timeline: "సిఫారసు టైమ్‌లైన్",
      current: "ప్రస్తుత",
      previous: "మునుపటి",
      driverSummary: "డ్రైవర్ సారాంశం",
      download: "డ్రైవర్ సారాంశం డౌన్‌లోడ్",
      stopPlanning: "స్టాప్ ప్లానింగ్",
      stopLoading: "మ్యాప్ చేసిన లాజిస్టిక్స్ స్టాప్‌లను వెతుకుతోంది...",
      noStops: "ఈ కారిడార్‌కు ధృవీకరించిన మ్యాప్ చేసిన స్టాప్‌లు లభించలేదు.",
      mappedCandidate: "మ్యాప్ చేసిన OSM అభ్యర్థి — ఉపయోగించే ముందు ధృవీకరించండి.",
      recommendation: "సిఫారసు",
    },
  };

  const tr = (key) => UI_TEXT[language]?.[key] || UI_TEXT.en[key] || key;

  // These are explicit planning baselines, not live observations.
  const SHELF_LIFE_BASELINES_HOURS = {
    tomato: 48,
    potato: 168,
    mango: 120,
    banana: 120,
    "leafy vegetables": 24,
    other: 72,
  };

  const getShelfLifeBaseline = (cropName) => {
    const key = String(cropName || "other").trim().toLowerCase();
    return SHELF_LIFE_BASELINES_HOURS[key] ?? SHELF_LIFE_BASELINES_HOURS.other;
  };

  const getSpoilageClock = (route) => {
    if (!route) return null;
    const durationMinutes = getNumericOrNull(route.duration_minutes);
    if (durationMinutes === null) return null;

    const baselineHours = getShelfLifeBaseline(routeData?.cargo?.crop ?? crop);
    const remainingHours = baselineHours - durationMinutes / 60;
    const arrival = new Date(Date.now() + durationMinutes * 60000);

    return {
      baselineHours,
      durationMinutes,
      remainingHours: Math.max(0, remainingHours),
      depleted: remainingHours <= 0,
      arrival,
    };
  };

  const getNearTie = () => {
    if (!routeData?.routes || routeData.routes.length < 2) return null;
    const ranked = routeData.routes
      .map((route) => ({ route, risk: getOverallRisk(route) }))
      .filter((item) => item.risk !== null)
      .sort((a, b) => a.risk - b.risk);

    if (ranked.length < 2) return null;
    const gap = Math.abs(ranked[1].risk - ranked[0].risk);
    return gap <= 0.2
      ? { first: ranked[0].route, second: ranked[1].route, gap }
      : null;
  };

  const getRouteTradeoff = () => {
    if (!displayedRecommendation?.route || !routeData?.routes?.length) return null;
    const recommended = displayedRecommendation.route;
    const alternatives = routeData.routes.filter(
      (route) => Number(route.route_id) !== Number(recommended.route_id)
    );
    if (!alternatives.length) return null;

    const alternative = alternatives
      .map((route) => ({
        route,
        duration: getNumericOrNull(route.duration_minutes),
        loss: getExpectedLoss(route),
        cost: getNumericOrNull(route?.economic_analysis?.effective_total_cost),
      }))
      .filter((item) => item.duration !== null)
      .sort((a, b) => a.duration - b.duration)[0];

    if (!alternative) return null;

    const recommendedDuration = getNumericOrNull(recommended.duration_minutes);
    const recommendedLoss = getExpectedLoss(recommended);
    const timeDifference = recommendedDuration === null ? null : recommendedDuration - alternative.duration;
    const lossDifference = recommendedLoss !== null && alternative.loss !== null
      ? alternative.loss - recommendedLoss
      : null;

    return { recommended, alternative: alternative.route, timeDifference, lossDifference };
  };

  const formatDuration = (minutes) => {
    const value = getNumericOrNull(minutes);
    if (value === null) return "N/A";
    if (value < 60) return `${Math.round(value)} min`;
    const hours = Math.floor(value / 60);
    const mins = Math.round(value % 60);
    return mins ? `${hours}h ${mins}m` : `${hours}h`;
  };

  const downloadDriverSummary = () => {
    if (!analysisRoute) return;
    const spoilage = getSpoilageClock(analysisRoute);
    const conditions = getConditionData(analysisRoute);
    const summary = [
      "HARVEST SHIELD — DRIVER SUMMARY",
      "",
      `Cargo: ${routeData?.cargo?.crop || crop}`,
      `Quantity: ${routeData?.cargo?.quantity_kg || quantity} kg`,
      `Cargo value: ${formatCurrency(routeData?.cargo?.cargo_value || cargoValue)}`,
      `Origin: ${routeData?.start || start}`,
      `Destination: ${routeData?.destination || end}`,
      `Recommended route: ${getRouteDisplayName(analysisRoute)}`,
      `Distance: ${analysisRoute.distance_km} km`,
      `Travel time: ${formatDuration(analysisRoute.duration_minutes)}`,
      `Modeled cargo risk: ${getOverallRisk(analysisRoute)?.toFixed(1) ?? "N/A"} / 100`,
      `Expected cargo loss: ${formatCurrency(getExpectedLoss(analysisRoute)) || "N/A"}`,
      `Estimated value after modeled loss: ${formatCurrency(getValuePreserved(analysisRoute)) || "N/A"}`,
      `Live traffic: ${conditions.traffic == null ? "N/A" : `${conditions.traffic.toFixed(1)}%`}`,
      `Live incidents: ${conditions.incidentCount == null ? "N/A" : conditions.incidentCount}`,
      `Current weather: ${conditions.temperature == null ? "N/A" : `${conditions.temperature.toFixed(1)}°C`}`,
      spoilage ? `Modeled shelf-life remaining: ${spoilage.remainingHours.toFixed(1)} h` : "",
      "",
      "IMPORTANT: Risk, expected loss and shelf-life are model/planning outputs, not guarantees.",
      "Live external feeds should be checked again before departure or dispatch.",
    ].filter(Boolean).join("\n");

    const blob = new Blob([summary], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "harvest-shield-driver-summary.txt";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const getRiskLabel = (risk) => {
    const numeric = getNumericOrNull(risk);
    if (numeric === null) return "";
    if (numeric < 30) return "LOW";
    if (numeric < 60) return "MODERATE";
    if (numeric < 80) return "HIGH";
    return "CRITICAL";
  };

  const getRiskClass = (risk) => {
    const numeric = getNumericOrNull(risk);
    if (numeric === null) return "";
    if (numeric < 30) return "risk-low";
    if (numeric < 60) return "risk-moderate";
    if (numeric < 80) return "risk-high";
    return "risk-critical";
  };

  const getRouteDisplayName = (route) => {
    if (route?.route_name) return route.route_name;
    const id = Number(route?.route_id);
    if (id === 1) return "Route A";
    if (id === 2) return "Route B";
    if (id === 3) return "Route C";
    return `Route ${Number.isFinite(id) ? id : "?"}`;
  };

  const getNumericOrNull = (value) => {
    if (value === null || value === undefined || value === "") return null;
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
  };

  const formatCurrency = (value) => {
    const numeric = getNumericOrNull(value);
    return numeric === null ? "" : `₹${numeric.toLocaleString("en-IN")}`;
  };

  const getOverallRisk = (route) =>
    getNumericOrNull(
      route?.risk_analysis?.risk_analysis?.overall_risk ??
      route?.risk_analysis?.overall_risk ??
      route?.risk_intelligence?.overall_risk ??
      route?.risk?.overall_risk ??
      route?.overall_risk
    );

  const getSafetyScore = (route) => {
    const direct = getNumericOrNull(
      route?.risk_analysis?.risk_analysis?.safety_score ??
      route?.risk_intelligence?.safety_score ??
      route?.risk_analysis?.safety_score ??
      route?.risk?.safety_score ??
      route?.safety_score
    );

    if (direct !== null) return direct;

    const risk = getOverallRisk(route);
    return risk === null ? null : 100 - risk;
  };

  const getExpectedLoss = (route) => {
    const direct = getNumericOrNull(
      route?.risk_analysis?.financial_analysis?.expected_loss ??
      route?.risk_analysis?.financial_analysis?.expected_cargo_loss ??
      route?.risk_analysis?.risk_analysis?.financial_analysis?.expected_loss ??
      route?.financial_analysis?.expected_loss ??
      route?.financial_analysis?.expected_cargo_loss ??
      route?.economic_analysis?.expected_cargo_loss ??
      route?.economic_analysis?.expected_loss ??
      route?.economic_analysis?.economic_summary?.expected_cargo_loss ??
      route?.expected_loss
    );

    if (direct !== null) return direct;

    // Backend risk is a model output derived from live conditions. If a
    // backend version omits the duplicated financial field, recover the
    // expected-loss display from that same backend risk output and the
    // user-declared cargo value. No synthetic live input is introduced.
    const risk = getOverallRisk(route);
    const cargo = getNumericOrNull(
      routeData?.cargo?.cargo_value ?? cargoValue
    );

    if (risk === null || cargo === null) return null;
    return Math.min(cargo, cargo * risk / 100);
  };

  const getValuePreserved = (route) => {
    const cargo = getNumericOrNull(
      routeData?.cargo?.cargo_value ?? cargoValue
    );
    const expectedLoss = getExpectedLoss(route);

    if (cargo === null || expectedLoss === null) return null;
    return Math.max(0, cargo - expectedLoss);
  };

  const getSimulationValuePreserved = () => {
    const simulatedValue = getNumericOrNull(
      simulationData?.cargo?.cargo_value ?? simulationCargoValue
    );
    const simulatedLoss = getExpectedLoss(simulationData?.recommendation);

    if (simulatedValue === null || simulatedLoss === null) return null;
    return Math.max(0, simulatedValue - simulatedLoss);
  };

  const getRoadQuality = (route) => {
    const value = route?.conditions?.road_quality;
    if (value === null || value === undefined || value === "") return null;
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
  };

  const getRoughRoadPercentage = (route) => {
    const value = route?.conditions?.rough_road_percentage;
    if (value === null || value === undefined || value === "") return null;
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
  };

  const getRoadQualityData = (route) => {
    return route?.conditions?.road_quality_data || null;
  };

  const getConditionData = (route) => {
    const conditions = route?.conditions || {};
    const traffic = conditions.traffic || {};
    const incidents = conditions.incidents || {};
    const weather = conditions.weather || {};
    const numericOrNull = (value) => {
      const number = Number(value);
      return Number.isFinite(number) ? number : null;
    };

    return {
      traffic: numericOrNull(traffic.congestion_percent ?? conditions.traffic_congestion_percent),
      delaySeconds: numericOrNull(traffic.delay_seconds ?? conditions.traffic_delay_seconds),
      incidentCount: numericOrNull(incidents.incident_count ?? conditions.incident_count),
      roadClosure: incidents.road_closure_detected ?? conditions.road_closure_detected ?? null,
      roadworks: incidents.roadworks_detected ?? conditions.roadworks_detected ?? null,
      temperature: numericOrNull(weather.temperature_c ?? conditions.temperature_c),
      humidity: numericOrNull(weather.humidity_percent ?? conditions.humidity_percent),
      precipitation: numericOrNull(weather.precipitation_mm ?? conditions.precipitation_mm),
      status: conditions.status || "unknown",
      provider: conditions.data_source || conditions.source || "Live external sources",
    };
  };

  const getMultimodalInfo = () => {
    const info = routeData?.multimodal_analysis;
    if (!info) return null;

    const routeAnalyses = Array.isArray(info.route_analyses)
      ? info.route_analyses
      : [];

    const selectedRouteId = Number(
      info.selected_route_id ??
      displayedRecommendation?.route?.route_id ??
      routeData?.routes?.[0]?.route_id
    );

    const selectedRouteAnalysis =
      routeAnalyses.find(
        (item) => Number(item?.route_id) === selectedRouteId
      ) ||
      info.selected_route_analysis ||
      null;

    const origin = selectedRouteAnalysis?.transfer_candidates?.origin || null;
    const destination = selectedRouteAnalysis?.transfer_candidates?.destination || null;

    return {
      ...info,
      selectedRouteId,
      selectedRouteAnalysis,
      originCandidate: origin?.candidate || null,
      destinationCandidate: destination?.candidate || null,
      routeAnalyses,
    };
  };

  const getRouteMultimodalAnalysis = (route) => {
    const info = getMultimodalInfo();
    if (!info || transportMode !== "multimodal") return null;

    return (
      info.routeAnalyses?.find(
        (item) => Number(item?.route_id) === Number(route?.route_id)
      ) || null
    );
  };

  const getRouteIncidents = (route) => {
    const incidents = route?.conditions?.incidents?.incidents;
    return Array.isArray(incidents) ? incidents : [];
  };

  const getBaseMetrics = (route) => ({
    risk: getOverallRisk(route),
    expectedLoss: getExpectedLoss(route),
    safetyScore: getSafetyScore(route),
    roadQuality: getRoadQuality(route),
  });

  const getRiskPayload = (route) => {
    const value = route?.risk_analysis || {};
    const nested = value?.risk_analysis;
    return nested && typeof nested === "object" ? nested : value;
  };

  const getRiskContributions = (route) => {
    const contributions = getRiskPayload(route)?.risk_contributions || {};
    return Object.entries(contributions)
      .filter(([, value]) => Number.isFinite(Number(value)))
      .map(([key, value]) => ({ key, value: Number(value) }))
      .sort((a, b) => b.value - a.value);
  };

  const getPrimaryRiskDriver = (route) => {
    const payload = getRiskPayload(route);
    return payload?.primary_risk_driver_label || "Cargo risk";
  };

  const getRiskFactors = (route) => {
    const factors = getRiskPayload(route)?.risk_factors;
    return Array.isArray(factors) ? factors : [];
  };

  const getLiveTimestamp = (route) => {
    const conditions = route?.conditions || {};
    const traffic = conditions.traffic || {};
    const incidents = conditions.incidents || {};
    const weather = conditions.weather || {};

    return {
      traffic: traffic.observed_at || traffic.retrieved_at || null,
      incidents: incidents.retrieved_at || null,
      weather: weather.observed_at || weather.retrieved_at || null,
    };
  };

  const formatLiveTimestamp = (timestamp) => {
    if (!timestamp) return "";

    const parsed = new Date(timestamp);
    if (Number.isNaN(parsed.getTime())) return "";

    return parsed.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const getNormalRecommendation = () => {
    if (!routeData?.routes?.length) return null;

    const backendId = Number(routeData?.recommendation?.route_id);
    const backendRoute = routeData.routes.find(
      (route) => Number(route.route_id) === backendId
    );

    // Accept the backend recommendation when it has a live risk result,
    // even if effective fuel cost is unavailable because no real mileage
    // source returned data. The UI must not replace that with a fake cost.
    if (backendRoute && getOverallRisk(backendRoute) != null) {
      return { route: backendRoute, metrics: getBaseMetrics(backendRoute) };
    }

    const viableRoutes = routeData.routes.filter(
      (route) => getOverallRisk(route) != null
    );

    if (!viableRoutes.length) return null;

    return viableRoutes.reduce((best, route) => {
      const current = getBaseMetrics(route);

      if (!best) return { route, metrics: current };

      // When the backend does not provide a complete economic model,
      // compare the actual modeled cargo-loss and risk outputs.
      if (current.expectedLoss != null && best.metrics.expectedLoss != null) {
        if (current.expectedLoss !== best.metrics.expectedLoss) {
          return current.expectedLoss < best.metrics.expectedLoss
            ? { route, metrics: current }
            : best;
        }
      }

      return current.risk < best.metrics.risk
        ? { route, metrics: current }
        : best;
    }, null);
  };

  const normalRecommendation = getNormalRecommendation();
  const displayedRecommendation = normalRecommendation;
  const analysisRoute =
    displayedRecommendation?.route ||
    routeData?.routes?.find((route) => getOverallRisk(route) !== null) ||
    null;
  const originalRecommendation = normalRecommendation?.route?.route_id ?? null;
  const recommendationChanged =
    liveRefresh.changed &&
    Number(liveRefresh.previousRouteId) !== Number(originalRecommendation);
  const getDecisionExplanation = () => {
    const recommended = displayedRecommendation?.route;
    if (!recommended || !routeData?.routes?.length) return null;

    const recommendedMetrics = displayedRecommendation.metrics;
    const alternatives = routeData.routes.filter(
      (route) => Number(route.route_id) !== Number(recommended.route_id)
    );

    const recommendedRisk = recommendedMetrics.risk;
    const recommendedLoss = recommendedMetrics.expectedLoss;
    const alternativeRisks = alternatives
      .map((route) => ({ route, risk: getOverallRisk(route) }))
      .filter((item) => item.risk !== null);
    const saferAlternative = alternativeRisks.length
      ? [...alternativeRisks].sort((a, b) => a.risk - b.risk)[0]
      : null;

    const alternativeLosses = alternatives
      .map((route) => ({ route, loss: getExpectedLoss(route) }))
      .filter((item) => item.loss !== null);
    const lowerLossAlternative = alternativeLosses.length
      ? [...alternativeLosses].sort((a, b) => a.loss - b.loss)[0]
      : null;

    const declaredCargoValue = getNumericOrNull(
      routeData?.cargo?.cargo_value ?? cargoValue
    );
    const preserved =
      declaredCargoValue !== null && recommendedLoss !== null
        ? Math.max(0, declaredCargoValue - recommendedLoss)
        : null;
    const preservationRate =
      declaredCargoValue !== null && declaredCargoValue > 0 && preserved !== null
        ? (preserved / declaredCargoValue) * 100
        : null;

    const riskReason =
      recommendedRisk === null
        ? "A complete live risk score was not returned for the selected route."
        : saferAlternative && saferAlternative.risk < recommendedRisk
          ? `${getRouteDisplayName(saferAlternative.route)} has ${Math.abs(recommendedRisk - saferAlternative.risk).toFixed(1)} points lower cargo risk. The selected route reflects the complete live-condition analysis.`
          : `The selected route has a cargo risk score of ${recommendedRisk.toFixed(2)}/100 under the current live traffic, incident, weather and travel-time conditions.`;

    const valueReason =
      recommendedLoss === null
        ? "Expected cargo loss was not returned for this route."
        : lowerLossAlternative && lowerLossAlternative.loss < recommendedLoss
          ? `${getRouteDisplayName(lowerLossAlternative.route)} has ₹${Math.round(recommendedLoss - lowerLossAlternative.loss).toLocaleString("en-IN")} lower expected cargo loss. The selected route reflects the overall live-condition analysis.`
          : preservationRate !== null
            ? (() => {
                const closestAlternative = alternatives
                  .map((route) => ({ route, loss: getExpectedLoss(route) }))
                  .filter((item) => item.loss !== null)
                  .sort((a, b) => Math.abs(a.loss - recommendedLoss) - Math.abs(b.loss - recommendedLoss))[0];

                if (!closestAlternative) {
                  return `The selected route leaves ${preservationRate.toFixed(1)}% of declared cargo value remaining after modeled loss.`;
                }

                const lossGap = Math.abs(recommendedLoss - closestAlternative.loss);

                if (lossGap <= 100) {
                  const selectedName = getRouteDisplayName(recommended);
                  const comparisonName = getRouteDisplayName(closestAlternative.route);
                  const selectedTime = getNumericOrNull(recommended.duration_minutes);
                  const comparisonTime = closestAlternative.route
                    ? getNumericOrNull(closestAlternative.route.duration_minutes)
                    : null;
                  const timeDifference =
                    selectedTime !== null && comparisonTime !== null
                      ? Math.abs(selectedTime - comparisonTime)
                      : null;
                  const timeText =
                    timeDifference === null || timeDifference < 0.5
                      ? " with similar travel time."
                      : selectedTime > comparisonTime
                        ? ` while adding about ${Math.round(timeDifference)} min of travel time.`
                        : ` while saving about ${Math.round(timeDifference)} min of travel time.`;
                  const lossText =
                    recommendedLoss < closestAlternative.loss
                      ? `${selectedName} has ₹${Math.round(lossGap).toLocaleString("en-IN")} lower modeled expected loss than ${comparisonName}`
                      : recommendedLoss > closestAlternative.loss
                        ? `${selectedName} has ₹${Math.round(lossGap).toLocaleString("en-IN")} higher modeled expected loss than ${comparisonName}`
                        : `${selectedName} has the same modeled expected loss as ${comparisonName}`;

                  return `${lossText}${recommendedLoss === closestAlternative.loss ? "" : timeText}${recommendedLoss === closestAlternative.loss ? "." : ""} The selected route leaves ${preservationRate.toFixed(1)}% of declared cargo value remaining after modeled loss.`;
                }

                return `The selected route leaves ${preservationRate.toFixed(1)}% of declared cargo value remaining after modeled loss.`;
              })()
            : "The model calculated expected cargo loss for the selected route.";

    return {
      riskReason,
      valueReason,
      tradeoffReason: "Harvest Shield combines live traffic, live incidents, current weather, travel time, mapped road conditions and cargo-specific risk. The engine does not choose a route solely by shortest distance.",
      risk: recommendedRisk,
      safety: recommendedMetrics.safetyScore,
      expectedLoss: recommendedLoss,
      conditions: getConditionData(recommended),
      primaryDriver: getPrimaryRiskDriver(recommended),
    };
  };

  const decisionExplanation = getDecisionExplanation();

  useEffect(() => {
    if (!routeData?.routes?.length || !analysisRoute) {
      setStopPlan(null);
      setStopPlanError("");
      return undefined;
    }

    const controller = new AbortController();
    setStopPlanLoading(true);
    setStopPlanError("");

    fetch("/api/stops", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      signal: controller.signal,
      body: JSON.stringify({ route: analysisRoute }),
    })
      .then(async (response) => {
        const data = await response.json().catch(() => null);
        if (!response.ok) {
          throw new Error(data?.detail || `Stop planning failed (HTTP ${response.status}).`);
        }
        return data;
      })
      .then((data) => setStopPlan(data))
      .catch((err) => {
        if (err?.name !== "AbortError") {
          setStopPlanError(err?.message || "Stop planning is unavailable.");
        }
      })
      .finally(() => setStopPlanLoading(false));

    return () => controller.abort();
  }, [routeData?.routes?.length, analysisRoute?.route_id, analysisRoute?.geometry]);

  useEffect(() => {
    if (!routeData?.recommendation?.route_id) return;
    const currentId = Number(routeData.recommendation.route_id);
    setRecommendationTimeline((current) => {
      if (!current.length) {
        return [{ routeId: currentId, time: new Date().toLocaleTimeString(), reason: "Initial live analysis" }];
      }
      return current;
    });
  }, [routeData?.recommendation?.route_id]);

  useEffect(() => {
    if (!liveRefresh.changed || !liveRefresh.previousRouteId || !routeData?.recommendation?.route_id) return;
    const currentId = Number(routeData.recommendation.route_id);
    const previousId = Number(liveRefresh.previousRouteId);
    if (previousId === currentId) return;

    setRecommendationTimeline((current) => [
      ...current,
      {
        routeId: currentId,
        previousRouteId: previousId,
        time: new Date().toLocaleTimeString(),
        reason: "Live conditions changed the recommendation",
      },
    ].slice(-8));
  }, [liveRefresh.changed, liveRefresh.previousRouteId, routeData?.recommendation?.route_id]);

  useEffect(() => {
    if (!liveRefresh.refreshing || !liveRefresh.refreshStartedAt) {
      return undefined;
    }

    const updateElapsed = () => {
      setRefreshElapsedSeconds(
        Math.max(
          0,
          Math.floor((Date.now() - liveRefresh.refreshStartedAt) / 1000)
        )
      );
    };

    updateElapsed();
    const interval = window.setInterval(updateElapsed, 1000);

    return () => window.clearInterval(interval);
  }, [liveRefresh.refreshing, liveRefresh.refreshStartedAt]);

  useEffect(() => {
    if (!routeData || !crop) return undefined;

    const interval = window.setInterval(() => {
      if (document.visibilityState === "visible") {
        refreshLiveRoutes(true);
      }
    }, 300000);

    return () => window.clearInterval(interval);
  }, [routeData, crop, quantity, cargoValue, fragility, start, end, transportMode]);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">HS</div>
          <div>
            <h1>Harvest Shield</h1>
            <p>Cargo-Centric Route Intelligence</p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <button
            type="button"
            className="simulate-button"
            onClick={refreshWholeApp}
            disabled={loading}
            style={{
              margin: 0,
              padding: "10px 14px",
              fontSize: "11px",
              position: "relative",
              zIndex: 3000,
              pointerEvents: "auto",
              minWidth: "185px",
              opacity: loading ? 0.65 : 1,
            }}
          >
            {loading
              ? "ANALYZING ROUTES..."
              : liveRefresh.refreshing
                ? `UPDATING LIVE DATA · ${refreshElapsedSeconds}s`
                : "REFRESH LIVE DATA ↻"}
          </button>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-end",
              gap: "2px",
              minWidth: "190px",
            }}
          >
            <span
              style={{
                fontSize: "10px",
                fontWeight: 800,
                letterSpacing: "0.8px",
                color: liveRefresh.refreshing ? "#baff72" : "#8fa49a",
              }}
            >
              {liveRefresh.refreshing
                ? `LIVE FEEDS REQUESTED · ${refreshElapsedSeconds}s`
                : liveRefresh.lastUpdated
                  ? `LIVE DATA UPDATED · ${liveRefresh.lastUpdated.toLocaleTimeString()}`
                  : "LIVE DATA READY"}
            </span>
            {!liveRefresh.refreshing && liveRefresh.refreshCount > 0 && (
              <span style={{ fontSize: "9px", color: "#70837a" }}>
                Live refresh #{liveRefresh.refreshCount}
                {liveRefresh.lastRefreshDurationSeconds != null
                  ? ` · ${liveRefresh.lastRefreshDurationSeconds}s`
                  : ""}
              </span>
            )}
          </div>

          <div className="system-status">
            <span className="status-dot"></span>
            ROUTING ENGINE ONLINE
          </div>
        </div>
      </header>

      <main className="main-layout">
        <section className="control-panel" id="shipment-inputs">
          <div className="panel-heading">
            <span className="eyebrow">ROUTE OPTIMIZATION</span>

            <h2>
              Protect the cargo.
              <br />
              Optimize the journey.
            </h2>

            <p>
              Harvest Shield combines real route geometry, live traffic, live incidents, current weather, cargo fragility and economic exposure.
            </p>
          </div>

          <div className="form-section">
            <h3>Journey</h3>

            <label htmlFor="start-location">Starting location</label>

            <select
              id="start-location"
              value={start === "" ? "" : LOCATION_VALUES.has(start) ? start : "__custom__"}
              onChange={(e) => {
                setStart(e.target.value === "__custom__" ? "__custom__" : e.target.value);
                setError("");
              }}
            >
              <option value="">Select origin</option>
              {LOCATION_GROUPS.map((group) => (
                <optgroup key={group.label} label={group.label}>
                  {group.options.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </optgroup>
              ))}
              <option value="__custom__">Other — type a custom location</option>
            </select>

            {start === "__custom__" || (start !== "" && !LOCATION_VALUES.has(start)) ? (
              <input
                id="start-location-custom"
                value={start === "__custom__" ? "" : start}
                onChange={(e) => setStart(e.target.value)}
                placeholder="Type origin, city, district or state"
                autoComplete="off"
                style={{ marginTop: "8px" }}
              />
            ) : null}

            <label htmlFor="destination-location" style={{ marginTop: "12px", display: "block" }}>
              Destination
            </label>

            <select
              id="destination-location"
              value={end === "" ? "" : LOCATION_VALUES.has(end) ? end : "__custom__"}
              onChange={(e) => {
                setEnd(e.target.value === "__custom__" ? "__custom__" : e.target.value);
                setError("");
              }}
            >
              <option value="">Select destination</option>
              {LOCATION_GROUPS.map((group) => (
                <optgroup key={group.label} label={group.label}>
                  {group.options.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </optgroup>
              ))}
              <option value="__custom__">Other — type a custom location</option>
            </select>

            {end === "__custom__" || (end !== "" && !LOCATION_VALUES.has(end)) ? (
              <input
                id="destination-location-custom"
                value={end === "__custom__" ? "" : end}
                onChange={(e) => setEnd(e.target.value)}
                placeholder="Type destination, city, district or state"
                autoComplete="off"
                style={{ marginTop: "8px" }}
              />
            ) : null}

            <label htmlFor="transport-mode" style={{ marginTop: "12px", display: "block" }}>
              Transport mode
            </label>

            <select
              id="transport-mode"
              value={transportMode}
              onChange={(e) => setTransportMode(e.target.value)}
              style={{
                appearance: "auto",
                WebkitAppearance: "auto",
                MozAppearance: "auto",
                cursor: "pointer",
              }}
            >
              <option value="" disabled>Choose transport mode</option>
              <option value="road">Road only — live road routing</option>
              <option value="multimodal">Multimodal — Road + Rail planning</option>
            </select>

            <p
              style={{
                margin: "8px 0 0",
                fontSize: "11px",
                lineHeight: 1.5,
                color: "#7f918b",
              }}
            >
              Multimodal mode checks mapped OpenStreetMap rail infrastructure near
              the route endpoints. It does not invent rail schedules, freight
              service, or rail ETAs.
            </p>


            <p
              style={{
                margin: "9px 0 0",
                fontSize: "11px",
                lineHeight: 1.5,
                color: "#7f918b",
              }}
            >
              Select an origin and destination from the state/district list, or choose “Other” to type any place. The routing engine geocodes the selected value.
            </p>
          </div>

          <div className="form-section">
            <h3>Cargo profile</h3>

            <label>Crop / cargo</label>

            <select
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              style={{
                appearance: "auto",
                WebkitAppearance: "auto",
                MozAppearance: "auto",
                cursor: "pointer",
              }}
            >
              <option value="">
                Choose cargo type
              </option>
              <option>Tomato</option>
              <option>Potato</option>
              <option>Mango</option>
              <option>Banana</option>
              <option>Leafy Vegetables</option>
              <option>Other</option>
            </select>

            <div className="two-column">
              <div>
                <label>Quantity (kg)</label>

                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  min="1"
                />
              </div>

              <div>
                <label>Cargo value (₹)</label>

                <input
                  type="number"
                  value={cargoValue}
                  onChange={(e) => setCargoValue(e.target.value)}
                  min="1"
                />
              </div>
            </div>

            <label>Cargo fragility</label>

            <div className="fragility-buttons">
              {["low", "medium", "high", "very_high"].map((level) => (
                <button
                  key={level}
                  type="button"
                  className={
                    fragility === level
                      ? "fragility active"
                      : "fragility"
                  }
                  onClick={() => setFragility(level)}
                >
                  {level.replace("_", " ").toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <button
            type="button"
            className="analyze-button"
            onClick={analyzeRoute}
            disabled={loading}
          >
            {loading
              ? "ANALYZING ROUTES..."
              : "ANALYZE CARGO ROUTES →"}
          </button>

          {routeData && !loading && (
            <button
              type="button"
              onClick={updateShipment}
              style={{
                width: "100%",
                marginTop: "10px",
                padding: "12px 16px",
                borderRadius: "10px",
                border: "1px solid rgba(186, 255, 114, 0.28)",
                background: "rgba(186, 255, 114, 0.06)",
                color: "#baff72",
                fontSize: "11px",
                fontWeight: 800,
                letterSpacing: "1px",
                cursor: "pointer",
              }}
            >
              UPDATE SHIPMENT ↻
            </button>
          )}

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
        </section>

        <section className="map-section">
          <div className="map-header">
            <div>
              <span className="eyebrow">LIVE ROUTE VIEW</span>
              <h2>Cargo Risk Map</h2>
            </div>

            {routeData && (
              <div className="route-count">
                {routeData.route_count} real routes analyzed
              </div>
            )}
          </div>

          {routeData && routeData.route_count < 3 && (
            <div
              style={{
                marginTop: "14px",
                marginBottom: "14px",
                padding: "12px 14px",
                borderRadius: "12px",
                border: "1px solid rgba(255,255,255,0.12)",
                background: "rgba(255,255,255,0.035)",
                color: "#b9c3d1",
                fontSize: "12px",
                lineHeight: 1.5,
              }}
            >
              <strong style={{ color: "#ffffff" }}>
                Only {routeData.route_count} real route
                {routeData.route_count === 1 ? "" : " alternatives"} returned.
              </strong>{" "}
              {routeData.route_count === 1
                ? "No alternative Route B or Route C was returned for this journey, so there is no route comparison to explain."
                : "Route A and Route B are available for comparison. Route C was not returned by the routing provider."}{" "}
              Harvest Shield does not create synthetic routes when the routing
              service does not return them.
            </div>
          )}

          <div className="map-wrapper" style={{ position: "relative" }}>
            {routeData ? (
              <>
                {(() => {
                  const scenarioStyles = {
                    1: { color: "#f0a35b", label: "Route A", dashArray: "10 8" },
                    2: { color: "#257cff", label: "Route B", dashArray: "18 10" },
                    3: { color: "#9b7bff", label: "Route C", dashArray: "4 8" },
                  };

                  const getRouteStyle = (route) => {
                    const routeId = Number(route?.route_id);
                    const scenario = scenarioStyles[routeId];
                    if (scenario) {
                      return {
                        ...scenario,
                        description: route?.route_type || "OSRM corridor route",
                      };
                    }
                    return {
                      color: "#ffffff",
                      label: getRouteDisplayName(route),
                      description: route?.route_type || "OSRM corridor route",
                      dashArray: "8 8",
                    };
                  };

                  const baseRoute = routeData.routes[0];
                  const baseCoordinates = getRouteCoordinates(baseRoute);
                  const basePositions = baseCoordinates
                    .map((coordinate) => [coordinate[1], coordinate[0]])
                    .filter(
                      (position) =>
                        Number.isFinite(position[0]) &&
                        Number.isFinite(position[1])
                    );

                  if (basePositions.length < 2) {
                    return (
                      <div className="map-placeholder">
                        <div className="map-placeholder-icon">◎</div>
                        <h3>Route geometry unavailable</h3>
                        <p>
                          The backend returned route data, but no drawable road
                          geometry was available.
                        </p>
                      </div>
                    );
                  }

                  const activeRouteId = displayedRecommendation?.route?.route_id == null
                    ? null
                    : Number(displayedRecommendation.route.route_id);

                  const activeRoute =
                    displayedRecommendation?.route
                      ? routeData.routes.find(
                          (route) => Number(route.route_id) === activeRouteId
                        ) || baseRoute
                      : baseRoute;

                  const activeStyle = getRouteStyle(activeRoute);

                  const routePositions = (route) =>
                    getRouteCoordinates(route)
                      .map((coordinate) => [coordinate[1], coordinate[0]])
                      .filter(
                        (position) =>
                          Number.isFinite(position[0]) &&
                          Number.isFinite(position[1])
                      );

                  const isDisrupted =
                    false;

                  const originPosition = basePositions[0];
                  const destinationPosition = basePositions[basePositions.length - 1];

                  return (
                    <>
                      <MapContainer
                        key={`${originPosition.join("-")}-${destinationPosition.join("-")}`}
                        bounds={basePositions}
                        boundsOptions={{ padding: [55, 55] }}
                        zoomControl={true}
                        className="map"
                      >
                        <TileLayer
                          attribution="&copy; OpenStreetMap contributors"
                          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />

                        <Marker
                          position={originPosition}
                        >
                          <Popup>
                            <strong>Origin</strong>
                            <br />
                            {start}
                          </Popup>
                        </Marker>

                        <Marker
                          position={destinationPosition}
                        >
                          <Popup>
                            <strong>Destination</strong>
                            <br />
                            {end}
                          </Popup>
                        </Marker>

                        {Array.from(
                          new Map(
                            routeData.routes
                              .flatMap((route) =>
                                getRouteIncidents(route).map((incident) => ({
                                  ...incident,
                                  affected_route_id: route.route_id,
                                  affected_route_name: getRouteDisplayName(route),
                                }))
                              )
                              .filter((incident) => incident && incident.id)
                              .reduce((items, incident) => {
                                const key = String(incident.id);
                                const existing = items.get(key);

                                if (!existing) {
                                  items.set(key, {
                                    ...incident,
                                    affected_routes: [
                                      {
                                        id: incident.affected_route_id,
                                        name: incident.affected_route_name,
                                      },
                                    ],
                                  });
                                } else if (
                                  !existing.affected_routes.some(
                                    (item) =>
                                      Number(item.id) ===
                                      Number(incident.affected_route_id)
                                  )
                                ) {
                                  existing.affected_routes.push({
                                    id: incident.affected_route_id,
                                    name: incident.affected_route_name,
                                  });
                                }

                                return items;
                              }, new Map())
                              .entries()
                          )
                        ).map(([incidentId, incident]) => {
                          const coordinates = incident?.geometry?.coordinates;

                          if (
                            !Array.isArray(coordinates) ||
                            coordinates.length === 0
                          ) {
                            return null;
                          }

                          const first = coordinates[0];

                          if (
                            !Array.isArray(first) ||
                            first.length < 2
                          ) {
                            return null;
                          }

                          const position = [
                            Number(first[1]),
                            Number(first[0]),
                          ];

                          if (
                            !Number.isFinite(position[0]) ||
                            !Number.isFinite(position[1])
                          ) {
                            return null;
                          }

                          const category = String(
                            incident.icon_category || ""
                          ).toLowerCase();

                          const isClosure =
                            category === "roadclosed";
                          const isWorks =
                            category === "roadworks";

                          const markerColor = isClosure
                            ? "#ef4444"
                            : isWorks
                              ? "#f59e0b"
                              : "#a855f7";

                          return (
                            <CircleMarker
                              key={`incident-${incidentId}`}
                              center={position}
                              radius={isClosure ? 8 : 6}
                              pathOptions={{
                                color: markerColor,
                                fillColor: markerColor,
                                fillOpacity: 0.85,
                                weight: 2,
                              }}
                            >
                              <Popup>
                                <strong>
                                  {isClosure
                                    ? "ROAD CLOSURE"
                                    : isWorks
                                      ? "ROADWORKS"
                                      : "TRAFFIC INCIDENT"}
                                </strong>

                                <br />

                                {incident.from || "Route incident"}

                                {incident.distance_from_route_km != null && (
                                  <>
                                    <br />
                                    {Number(
                                      incident.distance_from_route_km
                                    ).toFixed(2)} km from matched route corridor
                                  </>
                                )}

                                {incident.affected_routes?.length > 0 && (
                                  <>
                                    <br />
                                    Affected: {incident.affected_routes
                                      .map((item) => item.name)
                                      .join(", ")}
                                  </>
                                )}
                              </Popup>
                            </CircleMarker>
                          );
                        })}

                        {transportMode === "multimodal" && (() => {
                          const multimodalInfo = getMultimodalInfo();
                          const selectedAnalysis = multimodalInfo?.selectedRouteAnalysis;
                          const originCandidate = selectedAnalysis?.transfer_candidates?.origin?.candidate;
                          const destinationCandidate = selectedAnalysis?.transfer_candidates?.destination?.candidate;

                          const candidateMarker = (candidate, label) => {
                            if (!candidate) return null;
                            const latitude = Number(candidate.latitude);
                            const longitude = Number(candidate.longitude);
                            if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null;

                            return (
                              <CircleMarker
                                key={`rail-${label}-${candidate.name}-${latitude}-${longitude}`}
                                center={[latitude, longitude]}
                                radius={7}
                                pathOptions={{
                                  color: "#8fb7ff",
                                  fillColor: "#8fb7ff",
                                  fillOpacity: 0.9,
                                  weight: 3,
                                }}
                              >
                                <Popup>
                                  <strong>🚆 {label}</strong>
                                  <br />
                                  {candidate.name}
                                  <br />
                                  {Number(candidate.distance_from_endpoint_km).toFixed(2)} km from road endpoint
                                  <br />
                                  OpenStreetMap mapped railway infrastructure
                                </Popup>
                              </CircleMarker>
                            );
                          };

                          return (
                            <>
                              {candidateMarker(originCandidate, "Origin rail transfer candidate")}
                              {candidateMarker(destinationCandidate, "Destination rail transfer candidate")}
                            </>
                          );
                        })()}

                        {routeData.routes.map((route) => {
                          const positions = routePositions(route);
                          if (positions.length < 2) return null;

                          const routeId = Number(route.route_id);
                          const style = getRouteStyle(route);
                          const selected = displayedRecommendation?.route ? routeId === activeRouteId : false;
                          const disrupted =
                            false;

                          return (
                            <>
                              {selected && !disrupted && (
                                <Polyline
                                  key={`route-${routeId}-recommendation-halo`}
                                  positions={positions}
                                  pathOptions={{
                                    color: "#22c55e",
                                    weight: 10,
                                    opacity: 0.65,
                                    lineCap: "round",
                                    lineJoin: "round",
                                  }}
                                />
                              )}

                              <Polyline
                                key={`route-${routeId}`}
                                positions={positions}
                                pathOptions={{
                                  color: disrupted ? "#ef4444" : style.color,
                                  weight: selected ? 6.5 : 5,
                                  opacity: selected ? 1 : 0.72,
                                  dashArray: style.dashArray,
                                  lineCap: "round",
                                  lineJoin: "round",
                                }}
                              >
                                <Popup>
                                  <strong>{style.label}</strong>
                                  <br />
                                  {style.description}
                                  {selected && (
                                    <>
                                      <br />
                                      <strong>MODEL RECOMMENDATION</strong>
                                    </>
                                  )}
                                  <br />
                                  <strong>Distance:</strong> {route.distance_km} km
                                  <br />
                                  <strong>Travel time:</strong> {route.duration_minutes} min
                                  {getConditionData(route).roadClosure ? (
                                    <>
                                      <br />
                                      <strong>Condition:</strong> CLOSURE DETECTED
                                    </>
                                  ) : getConditionData(route).roadworks ? (
                                    <>
                                      <br />
                                      <strong>Condition:</strong> ROADWORKS DETECTED
                                    </>
                                  ) : null}
                                </Popup>
                              </Polyline>
                            </>
                          );
                        })}

                      </MapContainer>

                      <div
                        style={{
                          position: "absolute",
                          left: "18px",
                          bottom: "18px",
                          zIndex: 1000,
                          padding: "10px 13px",
                          borderRadius: "10px",
                          background: "rgba(13,18,30,0.9)",
                          border: "1px solid rgba(255,255,255,0.12)",
                          color: "#dfe5ef",
                          fontSize: "12px",
                          lineHeight: 1.4,
                          backdropFilter: "blur(8px)",
                        }}
                      >
                        <strong style={{ color: "#ffffff" }}>
                          LIVE ROAD CORRIDOR
                        </strong>
                        <br />
                        {displayedRecommendation?.route
                            ? `Current model recommendation: ${getRouteDisplayName(activeRoute)}`
                            : "No model recommendation: required live condition inputs are incomplete"}
                      </div>

                      <div
                        className="map-route-legend"
                        style={{
                          position: "absolute",
                          right: "18px",
                          top: "18px",
                          zIndex: 1000,
                          width: "280px",
                          padding: "16px",
                          borderRadius: "14px",
                          background: "rgba(13,18,30,0.96)",
                          color: "white",
                          boxShadow: "0 10px 30px rgba(0,0,0,0.30)",
                          border: "1px solid rgba(255,255,255,0.12)",
                          backdropFilter: "blur(10px)",
                        }}
                      >
                        <div
                          style={{
                            fontSize: "13px",
                            fontWeight: 800,
                            letterSpacing: "1px",
                            marginBottom: "12px",
                          }}
                        >
                          MAP LEGEND
                        </div>

                        {routeData.routes.map((route) => {
                            const id = Number(route.route_id);
                            const scenario = getRouteStyle(route);
                            const selected = displayedRecommendation?.route
                              ? Number(id) === activeRouteId
                              : false;

                            return (
                              <div
                                key={id}
                                style={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "10px",
                                  padding: "9px 10px",
                                  marginBottom: "5px",
                                  borderRadius: "9px",
                                  background: selected
                                    ? "rgba(255,255,255,0.09)"
                                    : "transparent",
                                  border: selected
                                    ? "1px solid rgba(255,255,255,0.10)"
                                    : "1px solid transparent",
                                }}
                              >
                                <span
                                  style={{
                                    width: "34px",
                                    height: "5px",
                                    borderRadius: "5px",
                                    background: scenario.color,
                                    flexShrink: 0,
                                  }}
                                />
                                <div>
                                  <div
                                    style={{
                                      fontSize: "13px",
                                      fontWeight: 800,
                                    }}
                                  >
                                    {scenario.label}
                                  </div>
                                  <div
                                    style={{
                                      fontSize: "11px",
                                      color: "#aeb6c5",
                                      marginTop: "2px",
                                    }}
                                  >
                                    {scenario.description}
                                  </div>
                                </div>
                              </div>
                            );
                          })}

                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "10px",
                            padding: "9px 10px",
                            marginTop: "4px",
                          }}
                        >
                          <span
                            style={{
                              width: "34px",
                              height: "9px",
                              borderRadius: "8px",
                              background: "#22c55e",
                              boxShadow: "0 0 9px rgba(34,197,94,0.55)",
                              flexShrink: 0,
                            }}
                          />
                          <div>
                            <div
                              style={{
                                fontSize: "13px",
                                fontWeight: 800,
                              }}
                            >
                              Current model recommendation
                            </div>
                            <div
                              style={{
                                fontSize: "11px",
                                color: "#aeb6c5",
                              }}
                            >
                              Current model recommendation based on the available live conditions and cargo-risk analysis
                            </div>
                          </div>
                        </div>

                        {false && (
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "10px",
                              padding: "9px 10px",
                              marginTop: "2px",
                            }}
                          >
                            <span
                              style={{
                                width: "34px",
                                height: "8px",
                                borderRadius: "8px",
                                background: "#ef4444",
                                boxShadow: "0 0 9px rgba(239,68,68,0.55)",
                                flexShrink: 0,
                              }}
                            />
                            <div>
                              <div
                                style={{
                                  fontSize: "13px",
                                  fontWeight: 800,
                                }}
                              >
                                Disrupted
                              </div>
                              <div
                                style={{
                                  fontSize: "11px",
                                  color: "#aeb6c5",
                                }}
                              >
                                Road condition deterioration
                              </div>
                            </div>
                          </div>
                        )}

                        <div
                          style={{
                            marginTop: "10px",
                            paddingTop: "10px",
                            borderTop: "1px solid rgba(255,255,255,0.10)",
                            fontSize: "11px",
                            lineHeight: 1.45,
                            color: "#aeb6c5",
                          }}
                        >
                          <strong style={{ color: "#ffffff" }}>
                            How to read
                          </strong>
                          <br />
                          The map shows real OSRM route geometry. Green marks the backend recommendation; the other colours show live route alternatives.
                        </div>
                      </div>
                    </>
                  );
                })()}
              </>
            ) : (
              <div className="map-placeholder">
                <div className="map-placeholder-icon">◎</div>
                <h3>Ready to analyze</h3>
                <p>
                  Enter your cargo and journey details,
                  then analyze the route.
                </p>
              </div>
            )}
          </div>
        </section>
      </main>

      {routeData && (
        <section className="what-if-section">
          <div className="what-if-header">
            <div>
              <span className="eyebrow">SCENARIO PLANNING</span>
              <h2>What-If Simulation</h2>
              <p>
                Test how a different cargo profile could change the route, risk,
                expected loss and economic recommendation.
                <strong
                  style={{
                    display: "block",
                    marginTop: "6px",
                    fontWeight: 700,
                  }}
                >
                  Scenario only — this does not change the current shipment analysis or live recommendation.
                </strong>
              </p>
            </div>
            <div className="what-if-badge">
              DECISION SIMULATOR
            </div>
          </div>

          <div className="what-if-grid">
            <div className="what-if-controls">
              <h3>Simulate another shipment</h3>

              <label>Crop / cargo</label>
              <select
                value={simulationCrop}
                onChange={(e) => setSimulationCrop(e.target.value)}
              >
                <option value="" disabled>
                  Select cargo type
                </option>
                <option value="Tomato">Tomato</option>
                <option value="Potato">Potato</option>
                <option value="Mango">Mango</option>
                <option value="Banana">Banana</option>
                <option value="Leafy Vegetables">Leafy Vegetables</option>
                <option value="Other">Other</option>
              </select>

              <div className="two-column">
                <div>
                  <label>Quantity (kg)</label>
                  <input
                    type="number"
                    value={simulationQuantity}
                    min="1"
                    onChange={(e) => setSimulationQuantity(e.target.value)}
                  />
                </div>
                <div>
                  <label>Cargo value (₹)</label>
                  <input
                    type="number"
                    value={simulationCargoValue}
                    min="1"
                    onChange={(e) => setSimulationCargoValue(e.target.value)}
                  />
                </div>
              </div>

              <label>Fragility</label>
              <div className="fragility-buttons">
                {["low", "medium", "high", "very_high"].map((level) => (
                  <button
                    key={`simulation-${level}`}
                    type="button"
                    className={simulationFragility === level ? "fragility active" : "fragility"}
                    onClick={() => setSimulationFragility(level)}
                  >
                    {level.replace("_", " ").toUpperCase()}
                  </button>
                ))}
              </div>

              <div className="what-if-actions">
                <button
                  type="button"
                  className="simulate-button"
                  onClick={simulateScenario}
                  disabled={simulationLoading}
                >
                  {simulationLoading ? "SIMULATING..." : "RUN WHAT-IF SCENARIO →"}
                </button>
                {simulationData && (
                  <button
                    type="button"
                    className="simulate-button secondary"
                    onClick={clearSimulation}
                  >
                    CLEAR
                  </button>
                )}
              </div>

              {simulationError && (
                <div className="error-message">{simulationError}</div>
              )}
            </div>

            <div className="what-if-results">
              {!simulationData ? (
                <div className="what-if-empty">
                  <div className="what-if-empty-icon">◇</div>
                  <h3>Ready for a scenario</h3>
                  <p>
                    Change the cargo characteristics and run the simulation to
                    see how Harvest Shield responds.
                  </p>
                </div>
              ) : (
                <>
                  <div className="scenario-result-header">
                    <div>
                      <span className="eyebrow">WHAT-IF · REUSED LIVE CONDITIONS</span>
                      <h3>{simulationData.cargo.crop} · {simulationData.cargo.quantity_kg.toLocaleString()} kg</h3>
                      <p>
                        Fragility: {simulationData.cargo.fragility.replace("_", " ")}
                        {" · "}
                        Cargo value: ₹{Number(
                          simulationData.cargo.cargo_value
                        ).toLocaleString("en-IN")}
                      </p>
                    </div>
                    <div className="scenario-recommendation">
                      <span>SIMULATED RECOMMENDATION</span>
                      <strong>{simulationData.recommendation ? getRouteDisplayName(simulationData.recommendation) : "Unavailable"}</strong>
                    </div>
                  </div>

                  <div className="scenario-metrics">
                    <div>
                      <span>RISK</span>
                      <strong>{getOverallRisk(simulationData.recommendation) == null ? "" : getOverallRisk(simulationData.recommendation).toFixed(2)}</strong>
                    </div>
                    <div>
                      <span>EXPECTED LOSS</span>
                      <strong>₹{getExpectedLoss(simulationData.recommendation) == null ? "" : getExpectedLoss(simulationData.recommendation).toLocaleString("en-IN")}</strong>
                    </div>
                    <div>
                      <span>ESTIMATED VALUE AFTER MODELED LOSS</span>
                      <strong>₹{getSimulationValuePreserved() == null ? "" : getSimulationValuePreserved().toLocaleString("en-IN")}</strong>
                    </div>
                  </div>

                  <div className="scenario-comparison">
                    <div>
                      <span>CURRENT</span>
                      <strong>{getRouteDisplayName(displayedRecommendation?.route ?? routeData.recommendation)}</strong>
                      <small>{getOverallRisk(displayedRecommendation?.route) == null ? "" : `${getOverallRisk(displayedRecommendation?.route).toFixed(1)} risk`}</small>
                    </div>
                    <div className="scenario-arrow">→</div>
                    <div>
                      <span>WHAT-IF</span>
                      <strong>{simulationData.recommendation ? getRouteDisplayName(simulationData.recommendation) : "Unavailable"}</strong>
                      <small>{getOverallRisk(simulationData.recommendation) == null ? "" : `${getOverallRisk(simulationData.recommendation).toFixed(1)} risk`}</small>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </section>
      )}

      {routeData && (
        <section className="results-section">
          <div className="results-header">
            <div>
              <span className="eyebrow">
                CARGO-CENTRIC ANALYSIS
              </span>

              <h2>
                {routeData.route_count >= 2
                  ? "Route comparison"
                  : "Available route"}
              </h2>
            </div>

            <div className="prototype-note">
              LIVE EXTERNAL DATA
            </div>
          </div>

          <div className="recommendation-card">
            <div className="recommendation-icon">✓</div>

            <div className="recommendation-main">
              <span className="recommendation-label">
                {routeData.route_count >= 2
                  ? "CURRENT MODEL RECOMMENDATION"
                  : "SINGLE AVAILABLE ROUTE"}
              </span>

              <h3>
                {displayedRecommendation?.route
                  ? getRouteDisplayName(displayedRecommendation.route)
                  : "Route A"}
              </h3>

              <p>
                {routeData.route_count >= 2
                  ? liveRefresh.changed
                    ? `Live conditions changed the recommendation to ${getRouteDisplayName(displayedRecommendation?.route)}.`
                    : decisionExplanation?.tradeoffReason ??
                      `The recommendation is based on the available live-condition cargo-risk analysis.`
                  : `The routing provider returned only one real road route for this journey. Harvest Shield shows that route directly and does not claim it was selected over unavailable alternatives.`}
              </p>
            </div>

            <div className="recommendation-stat">
              <span>MODELED CARGO RISK</span>
              <strong>
                {getOverallRisk(analysisRoute) == null ? "" : `${getOverallRisk(analysisRoute).toFixed(1)} / 100`}
              </strong>
            </div>

            <div className="recommendation-stat">
              <span>ESTIMATED VALUE AFTER MODELED LOSS</span>

              <strong>
                {formatCurrency(getValuePreserved(analysisRoute))}
              </strong>
            </div>

            <div className="recommendation-stat">
              <span>SAFETY SCORE</span>

              <strong>
                {getSafetyScore(displayedRecommendation?.route ?? routeData.recommendation) == null
                  ? ""
                  : getSafetyScore(displayedRecommendation?.route ?? routeData.recommendation).toFixed(2)}
              </strong>
            </div>
          </div>

          {(() => {
            const multimodalInfo = getMultimodalInfo();
            if (!multimodalInfo) return null;

            if (transportMode !== "multimodal") {
              return (
                <div
                  style={{
                    margin: "18px 0",
                    padding: "16px",
                    borderRadius: "14px",
                    border: "1px solid rgba(255,255,255,0.08)",
                    background: "rgba(255,255,255,0.025)",
                  }}
                >
                  <div
                    style={{
                      fontSize: "10px",
                      fontWeight: 800,
                      letterSpacing: "1px",
                      color: "#8da196",
                    }}
                  >
                    TRANSPORT MODE · ROAD ONLY
                  </div>
                  <div
                    style={{
                      fontSize: "18px",
                      fontWeight: 800,
                      marginTop: "5px",
                    }}
                  >
                    🚛 Live road-routing analysis
                  </div>
                  <div
                    style={{
                      marginTop: "6px",
                      fontSize: "12px",
                      color: "#9da9a5",
                      lineHeight: 1.55,
                    }}
                  >
                    Only the real OSRM road routes are analyzed. Railway
                    infrastructure is <strong>not checked</strong> in this mode.
                  </div>
                </div>
              );
            }

            const statusLabel =
              multimodalInfo.status === "all_routes_have_candidates"
                ? "CHECK COMPLETED · CANDIDATES FOUND FOR EVERY ROUTE"
                : multimodalInfo.status === "mixed_candidate_coverage"
                  ? "CHECK COMPLETED · MIXED RAIL COVERAGE"
                  : multimodalInfo.status === "no_route_candidates"
                    ? "CHECK COMPLETED · NO RAIL CANDIDATES"
                    : multimodalInfo.status === "lookup_unavailable"
                      ? "RAIL LOOKUP UNAVAILABLE"
                      : "RAIL INFRASTRUCTURE CHECK COMPLETED";

            const routeAnalyses = multimodalInfo.routeAnalyses || [];

            const selectedAnalysis = multimodalInfo.selectedRouteAnalysis;

            const candidateCards = [
              ["ORIGIN TRANSFER CANDIDATE", multimodalInfo.originCandidate],
              ["DESTINATION TRANSFER CANDIDATE", multimodalInfo.destinationCandidate],
            ];

            return (
              <div
                style={{
                  margin: "18px 0",
                  padding: "18px",
                  borderRadius: "16px",
                  border: "1px solid rgba(37,124,255,0.26)",
                  background:
                    "linear-gradient(135deg, rgba(37,124,255,0.09), rgba(34,197,94,0.045))",
                  boxShadow: "0 12px 28px rgba(0,0,0,0.12)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: "12px",
                    alignItems: "flex-start",
                    flexWrap: "wrap",
                  }}
                >
                  <div>
                    <div
                      style={{
                        fontSize: "10px",
                        fontWeight: 800,
                        letterSpacing: "1px",
                        color: "#90a9ff",
                      }}
                    >
                      MULTIMODAL ANALYSIS
                    </div>
                    <div
                      style={{
                        fontSize: "20px",
                        fontWeight: 850,
                        marginTop: "5px",
                      }}
                    >
                      🚛 ROAD + 🚆 RAIL INFRASTRUCTURE CHECK
                    </div>
                    <div
                      style={{
                        marginTop: "5px",
                        fontSize: "11px",
                        color: "#9da9a5",
                      }}
                    >
                      Independently checked for {multimodalInfo.route_count_checked || routeAnalyses.length} real road route(s)
                    </div>
                  </div>

                  <div
                    style={{
                      padding: "8px 11px",
                      borderRadius: "999px",
                      border: "1px solid rgba(255,255,255,0.12)",
                      background: "rgba(0,0,0,0.16)",
                      fontSize: "9px",
                      fontWeight: 850,
                      letterSpacing: "0.5px",
                      color: "#dce8ff",
                    }}
                  >
                    {statusLabel}
                  </div>
                </div>

                <div
                  style={{
                    marginTop: "15px",
                    padding: "11px 12px",
                    borderRadius: "11px",
                    background: "rgba(0,0,0,0.15)",
                    border: "1px solid rgba(255,255,255,0.07)",
                    fontSize: "11px",
                    lineHeight: 1.5,
                    color: "#b1beb8",
                  }}
                >
                  <strong style={{ color: "#ffffff" }}>
                    What is being checked?
                  </strong>{" "}
                  OpenStreetMap-mapped railway stations/halt infrastructure is
                  checked near the start and end of <strong>each available real road route</strong>.
                  This is a planning candidate check, not a confirmed freight service.
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                    gap: "10px",
                    marginTop: "12px",
                  }}
                >
                  {candidateCards.map(([label, candidate]) => (
                    <div
                      key={label}
                      style={{
                        padding: "12px",
                        borderRadius: "11px",
                        border: "1px solid rgba(255,255,255,0.07)",
                        background: "rgba(0,0,0,0.11)",
                      }}
                    >
                      <span
                        style={{
                          display: "block",
                          fontSize: "9px",
                          letterSpacing: "0.45px",
                          color: "#789087",
                        }}
                      >
                        {label}
                      </span>
                      <strong
                        style={{
                          display: "block",
                          marginTop: "5px",
                          fontSize: "13px",
                        }}
                      >
                        {candidate ? candidate.name : "No candidate found"}
                      </strong>
                      <span
                        style={{
                          display: "block",
                          marginTop: "4px",
                          fontSize: "10px",
                          color: "#899891",
                        }}
                      >
                        {candidate
                          ? `${Number(candidate.distance_from_endpoint_km).toFixed(2)} km from route endpoint · OSM ${candidate.railway_type || "rail"}`
                          : "No mapped station/halt within the lookup radius"}
                      </span>
                    </div>
                  ))}
                </div>

                <div
                  style={{
                    marginTop: "14px",
                    fontSize: "10px",
                    fontWeight: 800,
                    letterSpacing: "0.7px",
                    color: "#8da196",
                  }}
                >
                  PER-ROUTE RAIL CHECK STATUS
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                    gap: "8px",
                    marginTop: "8px",
                  }}
                >
                  {routeAnalyses.map((analysis) => {
                    const hasOrigin = Boolean(analysis?.transfer_candidates?.origin?.candidate);
                    const hasDestination = Boolean(analysis?.transfer_candidates?.destination?.candidate);
                    const complete = analysis?.status === "candidate_available";
                    const partial = analysis?.status === "partial_candidate";
                    const label = complete
                      ? "2 transfer candidates"
                      : partial
                        ? "1 transfer candidate"
                        : analysis?.status === "no_candidate"
                          ? "No candidate"
                          : "Lookup unavailable";

                    return (
                      <div
                        key={analysis.route_id}
                        style={{
                          padding: "10px 11px",
                          borderRadius: "10px",
                          border: "1px solid rgba(255,255,255,0.07)",
                          background:
                            Number(analysis.route_id) === Number(multimodalInfo.selectedRouteId)
                              ? "rgba(34,197,94,0.09)"
                              : "rgba(0,0,0,0.10)",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            gap: "8px",
                            alignItems: "center",
                          }}
                        >
                          <strong style={{ fontSize: "12px" }}>
                            {analysis.route_name || `Route ${analysis.route_id}`}
                          </strong>
                          <span
                            style={{
                              fontSize: "9px",
                              fontWeight: 800,
                              color: complete ? "#baff72" : partial ? "#f3d36b" : "#9da9a5",
                            }}
                          >
                            {label}
                          </span>
                        </div>
                        <div
                          style={{
                            marginTop: "4px",
                            fontSize: "9px",
                            color: "#7f8f88",
                          }}
                        >
                          Origin {hasOrigin ? "✓" : "—"} · Destination {hasDestination ? "✓" : "—"}
                          {Number(analysis.route_id) === Number(multimodalInfo.selectedRouteId)
                            ? " · selected route"
                            : ""}
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div
                  style={{
                    marginTop: "13px",
                    fontSize: "11px",
                    lineHeight: 1.5,
                    color: "#9da9a5",
                  }}
                >
                  The rail layer does not change OSRM distance/time and does not claim
                  a live rail timetable, freight capacity, rail duration, or confirmed booking.
                </div>
              </div>
            );
          })()}

          <div className="route-grid">
            {routeData.routes.map((route) => {
              const liveMetrics = getBaseMetrics(route);
              const risk = liveMetrics.risk;

              const isRecommended =
                route.route_id ===
                displayedRecommendation?.route?.route_id;

              return (
                <div
                  className={
                    isRecommended
                      ? "route-card recommended"
                      : "route-card"
                  }
                  key={route.route_id}
                >
                  <div className="route-card-header">
                    <div>
                      <span className="route-number">
                        0{route.route_id}
                      </span>

                      <h3>{getRouteDisplayName(route)}</h3>
                    </div>

                    {isRecommended && (
                      <span className="recommended-tag">
                        MODEL RECOMMENDATION
                      </span>
                    )}
                  </div>

                  <p className="route-type">
                    {route.route_type || "OSRM corridor route"}
                  </p>

                  <div
                    style={{
                      display: "inline-flex",
                      marginTop: "8px",
                      padding: "5px 8px",
                      borderRadius: "999px",
                      border: "1px solid rgba(255,255,255,0.08)",
                      fontSize: "9px",
                      fontWeight: 800,
                      letterSpacing: "0.55px",
                      color: "#aab7b1",
                    }}
                  >
                    ROAD LEG · {transportMode === "multimodal" ? "MULTIMODAL PLANNING" : "LIVE ROAD ROUTING"}
                  </div>

                  {transportMode === "multimodal" && (() => {
                    const railAnalysis = getRouteMultimodalAnalysis(route);
                    if (!railAnalysis) return null;

                    const hasOrigin = Boolean(railAnalysis?.transfer_candidates?.origin?.candidate);
                    const hasDestination = Boolean(railAnalysis?.transfer_candidates?.destination?.candidate);
                    const railLabel =
                      railAnalysis.status === "candidate_available"
                        ? "RAIL CHECK · 2 CANDIDATES"
                        : railAnalysis.status === "partial_candidate"
                          ? "RAIL CHECK · 1 CANDIDATE"
                          : railAnalysis.status === "no_candidate"
                            ? "RAIL CHECK · NONE FOUND"
                            : "RAIL CHECK · UNAVAILABLE";

                    return (
                      <div
                        style={{
                          display: "inline-flex",
                          marginTop: "7px",
                          marginLeft: "6px",
                          padding: "5px 8px",
                          borderRadius: "999px",
                          border: "1px solid rgba(37,124,255,0.16)",
                          background: "rgba(37,124,255,0.055)",
                          fontSize: "9px",
                          fontWeight: 800,
                          letterSpacing: "0.5px",
                          color: railAnalysis.status === "candidate_available"
                            ? "#b8d2ff"
                            : railAnalysis.status === "partial_candidate"
                              ? "#f3d36b"
                              : "#9da9a5",
                        }}
                        title={`Origin ${hasOrigin ? "candidate found" : "not found"} · Destination ${hasDestination ? "candidate found" : "not found"}`}
                      >
                        {railLabel}
                      </div>
                    );
                  })()}

                  <div className="metric-row">
                    <div>
                      <span>Distance</span>

                      <strong>
                        {route.distance_km} km
                      </strong>
                    </div>

                    <div>
                      <span>Travel time</span>

                      <strong>
                        {route.duration_minutes} min
                      </strong>
                    </div>
                  </div>

                  <div className="risk-box">
                    <div className="risk-header">
                      <span>
                        Modeled cargo risk
                      </span>

                      <span className={getRiskClass(risk)}>
                        {risk == null ? "" : getRiskLabel(risk)}
                      </span>
                    </div>

                    <div className="risk-bar">
  <div
    className="risk-fill"
    style={{
      width: `${risk == null ? 0 : risk}%`,
    }}
  />
</div>

<strong className="risk-number">
  {risk == null ? "" : risk.toFixed(2)}
</strong>
                  </div>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                      gap: "8px",
                      margin: "14px 0 4px",
                    }}
                  >
                    {(() => {
                      const conditions = getConditionData(route);
                      return (
                        <>
                          <div
                            style={{
                              padding: "8px 10px",
                              borderRadius: "8px",
                              border: "1px solid rgba(255,255,255,0.07)",
                              background: "rgba(255,255,255,0.02)",
                            }}
                          >
                            <span style={{ display: "block", fontSize: "9px", color: "#789087" }}>
                              LIVE TRAFFIC
                            </span>
                            <strong style={{ display: "block", marginTop: "3px", fontSize: "12px" }}>
                              {conditions.traffic == null ? "" : `${conditions.traffic.toFixed(1)}%`}
                            </strong>
                          </div>
                          <div
                            style={{
                              padding: "8px 10px",
                              borderRadius: "8px",
                              border: "1px solid rgba(255,255,255,0.07)",
                              background: "rgba(255,255,255,0.02)",
                            }}
                          >
                            <span style={{ display: "block", fontSize: "9px", color: "#789087" }}>
                              LIVE INCIDENTS
                            </span>
                            <strong style={{ display: "block", marginTop: "3px", fontSize: "12px" }}>
                              {conditions.incidentCount == null ? "" : conditions.incidentCount}
                            </strong>
                          </div>
                          <div
                            style={{
                              padding: "8px 10px",
                              borderRadius: "8px",
                              border: "1px solid rgba(255,255,255,0.07)",
                              background: "rgba(255,255,255,0.02)",
                            }}
                          >
                            <span style={{ display: "block", fontSize: "9px", color: "#789087" }}>
                              CURRENT WEATHER
                            </span>
                            <strong style={{ display: "block", marginTop: "3px", fontSize: "12px" }}>
                              {conditions.temperature == null ? "" : `${conditions.temperature.toFixed(1)}°C`}
                            </strong>
                          </div>
                          <div
                            style={{
                              padding: "8px 10px",
                              borderRadius: "8px",
                              border: "1px solid rgba(255,255,255,0.07)",
                              background: "rgba(255,255,255,0.02)",
                            }}
                          >
                            <span style={{ display: "block", fontSize: "9px", color: "#789087" }}>
                              HUMIDITY
                            </span>
                            <strong style={{ display: "block", marginTop: "3px", fontSize: "12px" }}>
                              {conditions.humidity == null ? "" : `${conditions.humidity.toFixed(1)}%`}
                            </strong>
                          </div>
                        </>
                      );
                    })()}
                  </div>

                  <div className="card-metrics">
                    {(() => {
                      const roadData = getRoadQualityData(route) || {};
                      const roadQuality =
                        liveMetrics.roadQuality ??
                        getNumericOrNull(roadData.road_quality);
                      const roughRoad =
                        getRoughRoadPercentage(route) ??
                        getNumericOrNull(roadData.rough_road_percentage);
                      const roughRoadKm = getNumericOrNull(
                        roadData.rough_road_km
                      );
                      const observations = getNumericOrNull(
                        roadData.matched_observations
                      );
                      const hasRoadData =
                        roadQuality != null ||
                        roughRoad != null ||
                        roughRoadKm != null ||
                        observations != null;

                      return (
                        <>
                          <div>
                            <span>Harvest Shield road-condition score</span>
                            <strong>{roadQuality == null ? "Not available" : `${roadQuality.toFixed(1)}/100`}</strong>
                          </div>

                          <div>
                            <span>Mapped rough road</span>
                            <strong>{roughRoad == null ? "Not available" : `${roughRoad.toFixed(1)}%`}</strong>
                          </div>

                          <div>
                            <span>Mapped rough-road distance</span>
                            <strong>{roughRoadKm == null ? "Not available" : `${roughRoadKm.toFixed(1)} km`}</strong>
                          </div>

                          <div>
                            <span>Mapped observations</span>
                            <strong>{observations == null ? "Not available" : observations}</strong>
                          </div>

                          <div className="road-source-row">
                            <span>Road-quality source</span>
                            <strong>OpenStreetMap mapped surface, smoothness and tracktype metadata</strong>
                          </div>
                        </>
                      );
                    })()}

                    <div className="expected-loss-row">
                      <span>Expected loss</span>

                      <strong>{formatCurrency(liveMetrics.expectedLoss) || "Not available"}</strong>
                    </div>

                  </div>
                </div>
              );
            })}

            {routeData.route_count === 2 && (
              <div className="route-c-unavailable">
                <strong>Route C — NOT AVAILABLE</strong>
                <span>No third real routing alternative was returned by the routing provider. Harvest Shield does not invent route values.</span>
              </div>
            )}
          </div>

          <section className="decision-intelligence-panel">
            <div className="feature-panel-header">
              <div>
                <span className="eyebrow">DECISION INTELLIGENCE</span>
                <h2>{tr("recommendation")} · {getRouteDisplayName(analysisRoute)}</h2>
              </div>
              <div className="feature-actions">
                <label className="language-control">
                  <span>{tr("language")}</span>
                  <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                    <option value="en">English</option>
                    <option value="hi">हिन्दी</option>
                    <option value="te">తెలుగు</option>
                  </select>
                </label>
                <button type="button" className="driver-summary-button" onClick={downloadDriverSummary}>
                  {tr("download")}
                </button>
              </div>
            </div>

            <div className="decision-feature-grid">
              {(() => {
                const spoilage = getSpoilageClock(analysisRoute);
                const tie = getNearTie();
                const tradeoff = getRouteTradeoff();
                return (
                  <>
                    <div className="decision-feature-card spoilage-feature">
                      <span className="feature-label">{tr("spoilage")}</span>
                      <h3>{routeData?.cargo?.crop || crop}</h3>
                      {spoilage ? (
                        <>
                          <div className="clock-value">{spoilage.remainingHours.toFixed(1)} h</div>
                          <div className="clock-subtext">{tr("remaining")}</div>
                          <div className="clock-details">
                            {tr("estimatedShelf")}: <strong>{spoilage.baselineHours} h</strong><br />
                            {tr("arrival")}: <strong>{spoilage.arrival.toLocaleString()}</strong>
                          </div>
                        </>
                      ) : (
                        <div className="clock-subtext">ETA unavailable</div>
                      )}
                      <small>{tr("baselineNote")}</small>
                    </div>

                    <div className="decision-feature-card">
                      <span className="feature-label">{tie ? tr("tie") : tr("noTie")}</span>
                      {tie ? (
                        <>
                          <h3>{getRouteDisplayName(tie.first)} ≈ {getRouteDisplayName(tie.second)}</h3>
                          <p>Risk gap is only <strong>{tie.gap.toFixed(2)}</strong> points. Travel time is surfaced as the practical distinction between the nearly tied routes.</p>
                        </>
                      ) : (
                        <p>No near-tie detected at the 0.20-point threshold.</p>
                      )}
                    </div>

                    <div className="decision-feature-card">
                      <span className="feature-label">{tr("tradeoff")}</span>
                      {tradeoff ? (
                        <>
                          <h3>{getRouteDisplayName(tradeoff.alternative)} vs {getRouteDisplayName(tradeoff.recommended)}</h3>
                          <p>
                            {tradeoff.timeDifference == null ? "" : Math.abs(tradeoff.timeDifference) < 0.5
                              ? "Travel times are effectively equal. "
                              : tradeoff.timeDifference > 0
                                ? `${getRouteDisplayName(tradeoff.alternative)} is ${formatDuration(Math.abs(tradeoff.timeDifference))} faster. `
                                : `${getRouteDisplayName(tradeoff.alternative)} is ${formatDuration(Math.abs(tradeoff.timeDifference))} slower. `}
                            {tradeoff.lossDifference == null
                              ? "Expected-loss comparison is unavailable."
                              : tradeoff.lossDifference > 0
                                ? `${getRouteDisplayName(tradeoff.alternative)} has ₹${Math.round(tradeoff.lossDifference).toLocaleString("en-IN")} higher modeled expected loss.`
                                : tradeoff.lossDifference < 0
                                  ? `${getRouteDisplayName(tradeoff.alternative)} has ₹${Math.round(Math.abs(tradeoff.lossDifference)).toLocaleString("en-IN")} lower modeled expected loss.`
                                  : "Modeled expected loss is equal."}
                          </p>
                        </>
                      ) : (
                        <p>No comparable alternative is available.</p>
                      )}
                    </div>
                  </>
                );
              })()}
            </div>

            {liveRefresh.changed && liveRefresh.previousRouteId && (
              <div className="recommendation-flip-alert">
                <strong>RECOMMENDATION CHANGED</strong>
                <span>{getRouteDisplayName({ route_id: liveRefresh.previousRouteId })} → {getRouteDisplayName(analysisRoute)}</span>
                <small>New live conditions changed the model recommendation.</small>
              </div>
            )}

            <div className="recommendation-timeline">
              <div className="feature-label">{tr("timeline")}</div>
              {recommendationTimeline.length ? recommendationTimeline.map((item, index) => (
                <div className="timeline-item" key={`${item.time}-${index}`}>
                  <span>{item.time}</span>
                  <strong>{getRouteDisplayName({ route_id: item.routeId })}</strong>
                  <p>{item.reason}</p>
                </div>
              )) : <p>No recommendation changes recorded yet.</p>}
            </div>

            <div className="stop-planning-panel">
              <div>
                <span className="feature-label">{tr("stopPlanning")}</span>
                {stopPlanLoading && <p>{tr("stopLoading")}</p>}
                {!stopPlanLoading && stopPlanError && <p>{stopPlanError}</p>}
                {!stopPlanLoading && !stopPlanError && stopPlan && (stopPlan.stops || []).length === 0 && <p>{tr("noStops")}</p>}
                {!stopPlanLoading && stopPlan && (stopPlan.stops || []).length > 0 && (
                  <div className="stop-list">
                    {stopPlan.stops.slice(0, 6).map((stop) => (
                      <div className="stop-item" key={`${stop.name}-${stop.latitude}-${stop.longitude}`}>
                        <strong>{stop.name}</strong>
                        <span>{stop.category} · {Number(stop.distance_from_route_km).toFixed(1)} km from route</span>
                        <small>{tr("mappedCandidate")}</small>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </section>

          <div
            style={{
              marginTop: "24px",
              padding: "12px 16px",
              borderRadius: "12px",
              background: liveRefresh.refreshing
                ? "rgba(186, 255, 114, 0.08)"
                : "rgba(255,255,255,0.025)",
              border: liveRefresh.refreshing
                ? "1px solid rgba(186,255,114,0.35)"
                : "1px solid rgba(255,255,255,0.08)",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "12px",
                flexWrap: "wrap",
              }}
            >
              <strong
                style={{
                  fontSize: "11px",
                  letterSpacing: "0.8px",
                  color: liveRefresh.refreshing ? "#baff72" : "#a8b9b0",
                }}
              >
                {liveRefresh.refreshing
                  ? `● LIVE UPDATE IN PROGRESS · ${refreshElapsedSeconds}s`
                  : liveRefresh.lastUpdated
                    ? `● LIVE VALUES UPDATED · ${liveRefresh.lastUpdated.toLocaleTimeString()}`
                    : "● LIVE VALUES READY"}
              </strong>
              <span style={{ fontSize: "10px", color: "#71857b" }}>
                {liveRefresh.refreshing
                  ? "TomTom + Open-Meteo + OpenStreetMap feeds are being queried"
                  : liveRefresh.refreshCount > 0
                    ? `Successful live refresh #${liveRefresh.refreshCount}`
                    : "Run the live refresh from the header button"}
              </span>
            </div>
          </div>

          <div
            style={{
              marginTop: "24px",
              padding: "22px",
              borderRadius: "18px",
              background: "rgba(16, 24, 24, 0.82)",
              border: "1px solid rgba(255,255,255,0.08)",
            }}
          >
            <div style={{ marginBottom: "16px" }}>
              <span className="eyebrow">ROUTE INTELLIGENCE</span>
              <h2 style={{ margin: "6px 0 4px" }}>Live condition snapshot</h2>
              <p style={{ margin: 0, color: "#9aa6a4" }}>
                The selected route is explained using the same external signals and risk model that produced the recommendation.
              </p>
            </div>

            {analysisRoute && (() => {
              const c = getConditionData(analysisRoute);
              const q = getRoadQualityData(analysisRoute);
              const contributions = getRiskContributions(analysisRoute).slice(0, 4);
              const timestamps = getLiveTimestamp(analysisRoute);
              const labels = {
                cargo_fragility: "Cargo fragility",
                live_traffic: "Live traffic",
                live_incidents: "Live incidents",
                mapped_road_quality: "Harvest Shield road-condition score",
                travel_time: "Travel time",
                temperature: "Cargo-specific temperature",
                weather: "Weather",
              };
              const valueText = (value, suffix = "") => value == null ? "" : `${value}${suffix}`;
              return (
                <>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: "10px" }}>
                    <div className="financial-metric">
                      <span>LIVE TRAFFIC</span>
                      <strong>{valueText(c.traffic, "%")}</strong>
                      <small>{c.delaySeconds == null ? "TomTom Traffic Flow" : `${Math.round(c.delaySeconds / 60)} min modeled delay`}</small>
                    </div>
                    <div className="financial-metric">
                      <span>LIVE INCIDENTS</span>
                      <strong>{valueText(c.incidentCount)}</strong>
                      <small>{c.roadClosure ? "At least one road-closure incident detected in the route corridor" : c.roadworks ? "Roadworks detected" : "TomTom corridor incidents"}</small>
                    </div>
                    <div className="financial-metric">
                      <span>CURRENT WEATHER</span>
                      <strong>{c.temperature == null ? "" : `${c.temperature.toFixed(1)}°C`}</strong>
                      <small>{c.humidity == null ? "Open-Meteo" : `${c.humidity.toFixed(1)}% humidity`}</small>
                    </div>
                    {q?.status === "mapped" && (
                      <div className="financial-metric">
                        <span>MAPPED ROAD</span>
                        <strong>{getNumericOrNull(q.road_quality) == null ? "" : `${getNumericOrNull(q.road_quality).toFixed(1)}/100`}</strong>
                        <small>{getNumericOrNull(q.rough_road_percentage) == null ? "" : `${getNumericOrNull(q.rough_road_percentage).toFixed(1)}% mapped rough`}</small>
                      </div>
                    )}
                  </div>

                  <div style={{ marginTop: "18px", display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: "18px" }}>
                    <div>
                      <div style={{ fontWeight: 800, marginBottom: "10px" }}>Top modeled risk drivers</div>
                      {contributions.length ? contributions.map((item) => (
                        <div key={item.key} style={{ marginBottom: "10px" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "4px" }}>
                            <span>{labels[item.key] || item.key}</span>
                            <strong>{item.value.toFixed(1)}</strong>
                          </div>
                          <div style={{ height: "7px", borderRadius: "7px", background: "rgba(255,255,255,0.08)", overflow: "hidden" }}>
                            <div style={{ width: `${Math.min(100, item.value * 5)}%`, height: "100%", background: "#9df35f", borderRadius: "7px" }} />
                          </div>
                        </div>
                      )) : <span style={{ color: "#9aa6a4" }}>Risk contribution data was not returned.</span>}
                    </div>
                    <div>
                      <div style={{ fontWeight: 800, marginBottom: "10px" }}>Primary risk driver</div>
                      <div style={{ fontSize: "22px", fontWeight: 900 }}>{getPrimaryRiskDriver(analysisRoute)}</div>
                      <div style={{ marginTop: "12px", color: "#9aa6a4", fontSize: "12px", lineHeight: 1.6 }}>
                        {getRiskFactors(analysisRoute).slice(0, 3).map((factor, index) => (
                          <div key={`${factor}-${index}`}>• {factor}</div>
                        ))}
                      </div>
                      <div style={{ marginTop: "14px", color: "#7f8a88", fontSize: "11px", lineHeight: 1.6 }}>
                        {timestamps.traffic && (
                          <div>TomTom traffic: {formatLiveTimestamp(timestamps.traffic)}</div>
                        )}
                        {timestamps.incidents && (
                          <div>TomTom incidents: {formatLiveTimestamp(timestamps.incidents)}</div>
                        )}
                        {timestamps.weather && (
                          <div>Open-Meteo weather: {formatLiveTimestamp(timestamps.weather)}</div>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              );
            })()}
          </div>

          <div className="financial-protection-card">
            <div className="financial-protection-header">
              <div>
                <span className="eyebrow">FINANCIAL PROTECTION</span>
                <h2>Modeled Cargo Value-at-Risk Analysis</h2>
                <p>
                  Harvest Shield translates cargo risk into financial impact,
                  showing how much cargo value is exposed and how much value the
                  current recommendation is expected to preserve.
                </p>
              </div>
              <div className="financial-symbol">₹</div>
            </div>

            <div className="financial-grid">
              <div className="financial-metric highlight">
                <span>MODELED CARGO EXPOSURE</span>
                <strong>
                  {getExpectedLoss(analysisRoute) == null || Number(routeData.cargo.cargo_value) <= 0
                    ? ""
                    : `${((getExpectedLoss(analysisRoute) / Number(routeData.cargo.cargo_value)) * 100).toFixed(2)}%`}
                </strong>
                <small>modeled cargo value at risk</small>
              </div>
              <div className="financial-metric">
                <span>TOTAL CARGO VALUE</span>
                <strong>₹{Number(routeData.cargo.cargo_value).toLocaleString()}</strong>
                <small>{Number(routeData.cargo.quantity_kg).toLocaleString()} kg of {routeData.cargo.crop}</small>
              </div>
              <div className="financial-metric">
                <span>MODELED VALUE AT RISK</span>
                <strong>{formatCurrency(getExpectedLoss(analysisRoute))}</strong>
                <small>modeled damage and spoilage exposure</small>
              </div>
              <div className="financial-metric">
                <span>ESTIMATED VALUE AFTER MODELED LOSS</span>
                <strong>{formatCurrency(getValuePreserved(analysisRoute))}</strong>
                <small>estimated value remaining after modeled loss</small>
              </div>
            </div>

            <div className="financial-insight">
              <strong>Financial Protection Insight</strong>
              <p>
                For this {routeData.cargo.crop} shipment, Harvest Shield models
                {formatCurrency(getExpectedLoss(analysisRoute))}
                of cargo value as expected damage and spoilage exposure on the
                current route recommendation. The model estimates
                {formatCurrency(getValuePreserved(analysisRoute))}
                of cargo value remaining after the modeled loss.
              </p>
            </div>

            <div className="financial-insight">
              <strong>Important: model output, not a guaranteed loss</strong>
              <p>
                The displayed rupee exposure is a modeled estimate derived from the live conditions and cargo profile. It is not an observed or guaranteed future loss.
              </p>
            </div>
          </div>

          <div className="live-intelligence-card">
            <div className="live-intelligence-header">
              <div>
                <span className="eyebrow">LIVE CONDITION INTELLIGENCE</span>
                <h2>Dynamic Route Re-Routing</h2>
                <p>
                  Refresh the real external feeds and let the backend recalculate the recommendation from current conditions. Automatic refresh runs every 5 minutes while this tab is visible.
                </p>
              </div>

              <div className={liveRefresh.refreshing ? "live-status active" : "live-status"}>
                <span className="live-status-dot"></span>
                {liveRefresh.refreshing ? "REFRESHING LIVE DATA" : "LIVE DATA READY"}
              </div>
            </div>

            <div className="live-intelligence-body">
              {(() => {
                const route = displayedRecommendation?.route;
                const conditions = route ? getConditionData(route) : null;
                return (
                  <>
                    <div className="live-event-box">
                      <span className="live-event-label">LIVE DATA STATUS</span>
                      <strong>
                        {liveRefresh.refreshing
                          ? "Refreshing external feeds..."
                          : conditions?.roadClosure
                            ? "ROAD CLOSURE NEAR ROUTE CORRIDOR"
                            : conditions?.roadworks
                              ? "ROADWORKS DETECTED"
                              : "Monitoring current route conditions"}
                      </strong>
                      <p>
                        {conditions
                          ? [
                              conditions.traffic == null ? "" : `Traffic congestion metric ${conditions.traffic.toFixed(1)}%`,
                              conditions.incidentCount == null ? "" : `${conditions.incidentCount} incidents`,
                              conditions.temperature == null ? "" : `${conditions.temperature.toFixed(1)}°C`,
                              conditions.humidity == null ? "" : `${conditions.humidity.toFixed(1)}% humidity`,
                            ]
                              .filter(Boolean)
                              .join(" · ")
                          : ""}
                      </p>
                    </div>

                    <div className="live-route-change">
                      <div>
                        <span>PREVIOUS RECOMMENDATION</span>
                        <strong>
                          {liveRefresh.previousRouteId
                            ? getRouteDisplayName({ route_id: liveRefresh.previousRouteId })
                            : "Initial analysis"}
                        </strong>
                      </div>

                      <div className="reroute-arrow">→</div>

                      <div>
                        <span>CURRENT RECOMMENDATION</span>
                        <strong>{getRouteDisplayName(route)}</strong>
                      </div>
                    </div>

                    <div className="live-metrics-grid">
                      <div>
                        <span>LIVE RISK</span>
                        <strong>{getOverallRisk(route) == null ? "" : getOverallRisk(route).toFixed(2)}</strong>
                      </div>
                      <div>
                        <span>EXPECTED LOSS</span>
                        <strong>{formatCurrency(getExpectedLoss(route))}</strong>
                      </div>
                    </div>

                    <div
                      className="live-action-row"
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        gap: "14px",
                        flexWrap: "wrap",
                      }}
                    >
                      <span>
                        {liveRefresh.refreshing
                          ? `Live refresh in progress · ${refreshElapsedSeconds}s elapsed · fetching new external values now`
                          : liveRefresh.changed
                            ? `Live data changed the recommendation to ${getRouteDisplayName(route)}.`
                            : liveRefresh.lastUpdated
                              ? `Last successful live refresh: ${liveRefresh.lastUpdated.toLocaleTimeString()} · Refresh #${liveRefresh.refreshCount}`
                              : `Current live recommendation: ${getRouteDisplayName(route)}.`}
                      </span>
                    </div>

                    <div className="live-disclaimer">
                      Live feeds: TomTom Traffic Flow, TomTom Traffic Incidents, Open-Meteo Current Weather and Open-Meteo Forecast. The traffic percentage is a TomTom congestion metric, not a claim that the road has that percentage of traffic. Road-surface metadata: OpenStreetMap. OSM road quality is mapped metadata, not a physical pavement sensor measurement.
                    </div>
                  </>
                );
              })()}
            </div>
          </div>

          {routeData.route_count >= 2 && (
            <div className="why-route">
              <div>
                <span className="eyebrow">
                  DECISION EXPLANATION
                </span>

                <h2>
                  Why {getRouteDisplayName(displayedRecommendation?.route ?? routeData.recommendation)}?
                </h2>
              </div>

              <div className="explanation-grid">
                <div>
                  <span>01</span>

                  <h3>Live-condition basis</h3>

                  <p>
                    {decisionExplanation?.tradeoffReason}
                  </p>
                </div>

                <div>
                  <span>02</span>

                  <h3>Risk trade-off</h3>

                  <p>
                    {decisionExplanation?.riskReason}
                  </p>

                  <small>
                    Risk: {decisionExplanation?.risk == null ? "N/A" : decisionExplanation.risk.toFixed(1)} / 100 ·
                    Safety: {decisionExplanation?.safety == null ? "N/A" : decisionExplanation.safety.toFixed(1)} / 100
                  </small>
                </div>

                <div>
                  <span>03</span>

                  <h3>Estimated cargo value remaining</h3>

                  <p>
                    {decisionExplanation?.valueReason}
                  </p>

                  <small>
                    Expected loss: {formatCurrency(decisionExplanation?.expectedLoss)}
                  </small>
                </div>
              </div>

              <div className="decision-tradeoff">
                <strong>Why this route instead of simply choosing the shortest?</strong>
                <span>{decisionExplanation?.tradeoffReason}</span>
              </div>
            </div>
          )}

        </section>
      )}
    </div>
  );
}

export default App;
