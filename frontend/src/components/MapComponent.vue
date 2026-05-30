<template>
  <div ref="wrapperRef" class="map-wrapper" :style="{ height }">
    <LMap
      v-if="mapReady"
      ref="mapRef"
      :zoom="zoom"
      :center="centerPoint"
      :zoom-snap="0.25"
      :max-bounds="[[-85, -210], [85, 210]]"
      :max-bounds-viscosity="1.0"
      @click="handleMapClick"
      @ready="onMapReady"
    >
      <LControlLayers v-if="showLayerControl" />
      <LTileLayer
        v-if="tracestrackKey"
        :url="`https://tile.tracestrack.com/topo_en/{z}/{x}/{y}.png?key=${tracestrackKey}`"
        attribution='&copy; <a href=&quot;https://www.openstreetmap.org/&quot;>OpenStreetMap</a> contributors &copy; <a href=&quot;https://www.tracestrack.com/&quot;>Tracestrack</a>'
        layer-type="base"
        name="Tracestrack Topo"
        :visible="savedLayer === 'Tracestrack Topo' || (!savedLayer && !!tracestrackKey)"
        :options="{ maxZoom: 19 }"
      />
      <LTileLayer
        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href=&quot;https://www.openstreetmap.org/&quot;>OpenStreetMap</a> contributors &copy; <a href=&quot;https://carto.com/&quot;>CARTO</a>'
        layer-type="base"
        name="CARTO Voyager"
        :visible="savedLayer === 'CARTO Voyager' || (!savedLayer && !tracestrackKey)"
        :options="{ maxZoom: 19 }"
      />
      <LTileLayer
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href=&quot;https://www.openstreetmap.org/&quot;>OpenStreetMap</a> contributors'
        layer-type="base"
        name="OpenStreetMap"
        :visible="savedLayer === 'OpenStreetMap'"
        :options="{ maxZoom: 19 }"
      />
      <LTileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        attribution='&copy; <a href=&quot;https://www.esri.com/&quot;>Esri</a>, Maxar, Earthstar Geographics'
        layer-type="base"
        name="Satellite"
        :visible="savedLayer === 'Satellite'"
        :options="{ maxZoom: 18 }"
      />

      <!-- Markers managed programmatically via markerClusterGroup -->
    </LMap>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { LMap, LTileLayer, LControlLayers } from '@vue-leaflet/vue-leaflet'
import L from 'leaflet'
import 'leaflet.markercluster'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import { useRouter } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'

const props = defineProps({
  destinations: {
    type: Array,
    default: () => []
  },
  center: {
    type: Array,
    default: () => [20, 0]
  },
  zoom: {
    type: Number,
    default: 2
  },
  height: {
    type: String,
    default: '100%'
  },
  selectable: {
    type: Boolean,
    default: false
  },
  selectedPosition: {
    type: Object,
    default: null
  },
  showLayerControl: {
    type: Boolean,
    default: false
  },
  mapId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['markerClick', 'mapClick', 'update:selectedPosition'])
const settingsStore = useSettingsStore()

const mappableDestinations = computed(() => {
  return props.destinations.filter(d => d.latitude != null && d.longitude != null && (d.latitude !== 0 || d.longitude !== 0))
})

const router = useRouter()
const wrapperRef = ref(null)
const mapRef = ref(null)
const mapReady = ref(false)

const tracestrackKey = import.meta.env.VITE_TRACESTRACK_KEY || ''

// Load saved layer preference for this map instance
const savedLayer = ref(null)
if (props.mapId) {
  try {
    savedLayer.value = localStorage.getItem(`tg-map-layer-${props.mapId}`)
  } catch { /* ignore */ }
}

const centerPoint = computed(() => {
  return props.center
})

const getMarkerIcon = (status) => {
  const statusColors = {
    suggested: '#93c5fd',
    researching: '#f59e0b',
    want_to_visit: '#22c55e',
    planned: '#f87171',
    visited: '#c084fc',
    archived: '#9ca3af'
  }

  const color = statusColors[status] || '#3b82f6'

  return L.divIcon({
    html: `
      <div style="
        background-color: ${color};
        width: 30px;
        height: 30px;
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <i style="color: white; font-size: 14px;" class="pi pi-map-marker"></i>
      </div>
    `,
    iconSize: [30, 30],
    className: 'map-marker'
  })
}

let clusterGroup = null
let resizeObserver = null
let scaleControl = null

const updateMinZoom = (map) => {
  const bounds = L.latLngBounds([[-85, -210], [85, 210]])
  const size = map.getSize()

  // Calculate zoom for EW: longitude span fits container width
  const ewBounds = L.latLngBounds([[0, -210], [0, 210]])
  const zoomEW = map.getBoundsZoom(L.latLngBounds([[0, -210], [0, 210]]), false)

  // Calculate zoom for NS: latitude span fits container height
  // Use a very narrow longitude range so only height matters
  const zoomNS = map.getBoundsZoom(L.latLngBounds([[-85, 0], [85, 0]]), false)

  // Take the HIGHER zoom (more zoomed in) — whichever axis fits first
  const minZoom = Math.max(zoomEW, zoomNS)
  map.setMinZoom(minZoom)
  if (map.getZoom() < minZoom) {
    map.setZoom(minZoom)
  }
}

const createClusterIcon = (cluster) => {
  const count = cluster.getChildCount()
  let size = 36
  let fontSize = 13
  if (count >= 100) { size = 48; fontSize = 14 }
  else if (count >= 10) { size = 42; fontSize = 13 }

  return L.divIcon({
    html: `<div style="
      background-color: #1f2937;
      width: ${size}px;
      height: ${size}px;
      border-radius: 50%;
      border: 3px solid #6b7280;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      font-weight: 700;
      font-size: ${fontSize}px;
      line-height: 1;
    ">${count}</div>`,
    iconSize: [size, size],
    className: 'map-cluster-icon'
  })
}

const buildPopupHtml = (dest) => {
  let html = `<div style="width:200px;padding:0;">`
  html += `<h4 style="font-size:0.9rem;font-weight:600;margin:0 0 0.5rem 0;">${dest.name}</h4>`
  html += `<div style="margin-bottom:0.5rem;"><span class="status-badge status-${dest.status}" style="
    display:inline-block;padding:0.25rem 0.75rem;border-radius:9999px;font-size:0.75rem;font-weight:600;white-space:nowrap;
  ">${statusLabels[dest.status] || dest.status}</span></div>`
  if (dest.city || dest.country) {
    html += `<div style="font-size:0.8rem;color:#9ca3af;margin-bottom:0.5rem;">`
    if (dest.city) html += `${dest.city}`
    if (dest.city && dest.country) html += `, `
    if (dest.country) html += `${dest.country}`
    html += `</div>`
  }
  if (dest.thumbnail_url) {
    html += `<div style="width:100%;height:100px;margin:0.5rem 0;overflow:hidden;border-radius:0.375rem;">
      <img src="${dest.thumbnail_url}" alt="${dest.name}" style="width:100%;height:100%;object-fit:cover;" />
    </div>`
  }
  html += `<a href="/destinations/${dest.id}" style="display:inline-block;margin-top:0.5rem;font-size:0.8rem;color:#60a5fa;text-decoration:none;font-weight:500;">View Details →</a>`
  html += `</div>`
  return html
}

const statusLabels = {
  suggested: 'Suggested',
  researching: 'Researching',
  want_to_visit: 'Want to Visit',
  planned: 'Planned',
  visited: 'Visited',
  archived: 'Archived'
}

const syncMarkers = () => {
  const map = mapRef.value?.leafletObject
  if (!map || !clusterGroup) return

  clusterGroup.clearLayers()

  mappableDestinations.value.forEach(dest => {
    const marker = L.marker([dest.latitude, dest.longitude], {
      icon: getMarkerIcon(dest.status)
    })
    marker.bindPopup(() => buildPopupHtml(dest), { maxWidth: 250 })
    marker.on('click', () => emit('markerClick', dest))
    clusterGroup.addLayer(marker)
  })
}

watch(mappableDestinations, () => {
  syncMarkers()
}, { deep: true })

// Live-update scale control when metric/imperial setting changes
watch(() => settingsStore.useMetricUnits, (isMetric) => {
  const map = mapRef.value?.leafletObject
  if (!map) return
  if (scaleControl) {
    map.removeControl(scaleControl)
  }
  scaleControl = L.control.scale({
    position: 'bottomleft',
    imperial: !isMetric,
    metric: isMetric,
    maxWidth: 200
  })
  scaleControl.addTo(map)
})

const handleMapClick = (event) => {
  if (props.selectable) {
    const { lat, lng } = event.latlng
    emit('mapClick', { lat, lng })
    emit('update:selectedPosition', { lat, lng })
  }
}

const onMapReady = () => {
  nextTick(() => {
    const map = mapRef.value?.leafletObject
    if (map) {
      map.invalidateSize()

      // Configure zoom behavior for smoother scrolling
      map.options.zoomSnap = 0.25
      map.options.zoomDelta = 0.25
      map.options.wheelPxPerZoomLevel = 120

      // Add scale control (single unit based on setting)
      const isMetric = settingsStore.useMetricUnits
      scaleControl = L.control.scale({
        position: 'bottomleft',
        imperial: !isMetric,
        metric: isMetric,
        maxWidth: 200
      })
      scaleControl.addTo(map)

      // Initialize cluster group
      clusterGroup = L.markerClusterGroup({
        iconCreateFunction: createClusterIcon,
        maxClusterRadius: 50,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
        disableClusteringAtZoom: 18
      })
      map.addLayer(clusterGroup)
      syncMarkers()

      // Set dynamic minZoom based on container size
      updateMinZoom(map)

      // Recalculate minZoom when the container resizes
      if (wrapperRef.value) {
        resizeObserver = new ResizeObserver(() => {
          map.invalidateSize()
          updateMinZoom(map)
        })
        resizeObserver.observe(wrapperRef.value)
      }

      // Listen for base layer changes to persist selection
      if (props.mapId) {
        map.on('baselayerchange', (e) => {
          try {
            localStorage.setItem(`tg-map-layer-${props.mapId}`, e.name)
          } catch { /* ignore */ }
        })
      }
    }
  })
}

onMounted(async () => {
  // Wait for the wrapper div to be in the DOM, then allow LMap to render
  await nextTick()
  if (wrapperRef.value && wrapperRef.value.offsetParent !== null) {
    // Container is visible — safe to render the map
    mapReady.value = true
  } else {
    // Container might be hidden (e.g. inactive tab) — poll until visible
    const check = setInterval(() => {
      if (wrapperRef.value && wrapperRef.value.offsetParent !== null) {
        mapReady.value = true
        clearInterval(check)
      }
    }, 250)
    // Give up after 10 seconds to avoid infinite polling
    setTimeout(() => clearInterval(check), 10000)
  }
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (clusterGroup) {
    clusterGroup.clearLayers()
    clusterGroup = null
  }
})
</script>

<style>
/* Unscoped: override markercluster default styles */
.map-cluster-icon {
  background: transparent !important;
}

.marker-cluster {
  background: transparent !important;
}

.marker-cluster div {
  background: transparent !important;
}
</style>

<style scoped>
.map-wrapper {
  width: 100%;
  position: relative;
  z-index: 0;
}

.map-wrapper :deep(.leaflet-container) {
  background-color: #1a2f4d;
  z-index: 0;
}

.map-wrapper :deep(.leaflet-control-scale) {
  margin-bottom: 20px;
}

.popup-content {
  width: 200px;
  padding: 0;
}

.popup-title {
  font-size: 0.9rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: var(--color-text-bright);
}

.popup-status {
  margin-bottom: 0.5rem;
}

.popup-info {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
}

.popup-thumbnail {
  width: 100%;
  height: 100px;
  margin: 0.5rem -8px;
  overflow: hidden;
  border-radius: 0.375rem;
}

.popup-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.popup-link {
  display: inline-block;
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: var(--color-accent-hover);
  text-decoration: none;
  font-weight: 500;
}

.popup-link:hover {
  text-decoration: underline;
}
</style>
