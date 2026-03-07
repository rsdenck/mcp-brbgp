<template>
  <div class="space-y-6">
    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="bg-gray-900 rounded-2xl p-5 border border-gray-800">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center">
            <UIcon name="i-heroicons-globe-alt" class="w-6 h-6 text-blue-500" />
          </div>
          <div>
            <p class="text-sm text-gray-400">ASNs Globais</p>
            <p class="text-2xl font-bold text-blue-400">{{ (stats as any)?.total_global_asns?.toLocaleString() || '-' }}</p>
          </div>
        </div>
      </div>
      
      <div class="bg-gray-900 rounded-2xl p-5 border border-gray-800">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
            <UIcon name="i-heroicons-flag" class="w-6 h-6 text-emerald-500" />
          </div>
          <div>
            <p class="text-sm text-gray-400">ASNs Brasil</p>
            <p class="text-2xl font-bold text-emerald-400">{{ (stats as any)?.total_brazil_asns?.toLocaleString() || '-' }}</p>
          </div>
        </div>
      </div>
      
      <div class="bg-gray-900 rounded-2xl p-5 border border-gray-800">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center">
            <UIcon name="i-heroicons-map" class="w-6 h-6 text-purple-500" />
          </div>
          <div>
            <p class="text-sm text-gray-400">Paises</p>
            <p class="text-2xl font-bold text-purple-400">{{ countries.length }}</p>
          </div>
        </div>
      </div>
      
      <div class="bg-gray-900 rounded-2xl p-5 border border-gray-800">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center">
            <UIcon name="i-heroicons-signal" class="w-6 h-6 text-amber-500" />
          </div>
          <div>
            <p class="text-sm text-gray-400">Operadoras</p>
            <p class="text-2xl font-bold text-amber-400">{{ operators.length }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Traffic Chart -->
      <div class="bg-gray-900 rounded-2xl p-6 border border-gray-800">
        <h3 class="text-lg font-semibold mb-4">Trafego de Rede (24h)</h3>
        <div ref="trafficChart" class="h-72"></div>
      </div>
      
      <!-- Countries Chart -->
      <div class="bg-gray-900 rounded-2xl p-6 border border-gray-800">
        <h3 class="text-lg font-semibold mb-4">ASNs por Pais</h3>
        <div ref="countryChart" class="h-72"></div>
      </div>
    </div>

    <!-- Secondary Charts -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-gray-900 rounded-2xl p-5 border border-gray-800">
        <h4 class="text-sm font-medium text-gray-400 mb-4">Tipos de Rede</h4>
        <div ref="networkChart" class="h-48"></div>
      </div>
      <div class="bg-gray-900 rounded-2xl p-5 border border-gray-800">
        <h4 class="text-sm font-medium text-gray-400 mb-4">Distribuicao IP</h4>
        <div ref="prefixChart" class="h-48"></div>
      </div>
      <div class="bg-gray-900 rounded-2xl p-5 border border-gray-800">
        <h4 class="text-sm font-medium text-gray-400 mb-4">Updates BGP</h4>
        <div ref="updatesChart" class="h-48"></div>
      </div>
    </div>

    <!-- Operators Table -->
    <div class="bg-gray-900 rounded-2xl p-6 border border-gray-800">
      <h3 class="text-lg font-semibold mb-4">Principais Operadoras</h3>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-left text-gray-400 border-b border-gray-800">
              <th class="pb-3 font-medium">ASN</th>
              <th class="pb-3 font-medium">Nome</th>
              <th class="pb-3 font-medium">Pais</th>
              <th class="pb-3 font-medium">IP Range</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="op in operators.slice(0, 15)" 
              :key="op.asn"
              class="border-b border-gray-800/50 hover:bg-gray-800/50 cursor-pointer"
              @click="navigateTo(`/asn/${op.asn}`)"
            >
              <td class="py-3 font-mono text-blue-400">AS{{ op.asn }}</td>
              <td class="py-3">{{ op.name }}</td>
              <td class="py-3 text-gray-400">{{ op.country }}</td>
              <td class="py-3 font-mono text-gray-500 text-sm">{{ op.ip_start || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Global Map -->
    <div class="bg-gray-900 rounded-2xl p-6 border border-gray-800">
      <h3 class="text-lg font-semibold mb-4">Mapa Global - Operadoras BGP</h3>
      <ClientOnly>
        <div ref="globalMap" class="h-[500px] rounded-xl overflow-hidden"></div>
      </ClientOnly>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Chart, registerables } from 'chart.js'

const isClient = typeof window !== 'undefined'
if (isClient) {
  Chart.register(...registerables)
}

const { getStats, getOperators, getCountries, getTraffic, getGlobalOperators } = useApi()

const stats = ref<any>(null)
const operators = ref<any[]>([])
const countries = ref<any[]>([])
const traffic = ref<any[]>([])
const globalOperators = ref<any[]>([])

const trafficChart = ref<HTMLElement | null>(null)
const countryChart = ref<HTMLElement | null>(null)
const networkChart = ref<HTMLElement | null>(null)
const prefixChart = ref<HTMLElement | null>(null)
const updatesChart = ref<HTMLElement | null>(null)
const globalMap = ref<HTMLElement | null>(null)

onMounted(async () => {
  const [s, o, c, t, g] = await Promise.all([
    getStats(),
    getOperators(50),
    getCountries(),
    getTraffic(),
    getGlobalOperators()
  ])
  
  stats.value = s
  operators.value = o as any[]
  countries.value = c as any[]
  traffic.value = t as any[]
  globalOperators.value = g as any[]
  
  initCharts()
  initMap()
})

function initCharts() {
  // Traffic Chart
  if (trafficChart.value && traffic.value.length) {
    new Chart(trafficChart.value, {
      type: 'line',
      data: {
        labels: traffic.value.map((d: any) => d.time),
        datasets: [{
          label: 'Trafego (Kbps)',
          data: traffic.value.map((d: any) => d.traffic / 1000),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: '#1f2937' }, ticks: { color: '#9ca3af' } },
          y: { grid: { color: '#1f2937' }, ticks: { color: '#9ca3af' } }
        }
      }
    })
  }

  // Country Chart
  if (countryChart.value && countries.value.length) {
    const topCountries = countries.value.slice(0, 10)
    new Chart(countryChart.value, {
      type: 'bar',
      data: {
        labels: topCountries.map((c: any) => c.country),
        datasets: [{
          label: 'ASNs',
          data: topCountries.map((c: any) => c.count),
          backgroundColor: ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#84cc16', '#ec4899', '#14b8a6', '#f97316']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: '#1f2937' }, ticks: { color: '#9ca3af' } },
          y: { grid: { display: false }, ticks: { color: '#9ca3af' } }
        }
      }
    })
  }

  // Network Types
  if (networkChart.value && stats.value?.network_types) {
    new Chart(networkChart.value, {
      type: 'doughnut',
      data: {
        labels: stats.value.network_types.map((n: any) => n.name),
        datasets: [{
          data: stats.value.network_types.map((n: any) => n.value),
          backgroundColor: ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'right', labels: { color: '#9ca3af', boxWidth: 12 } } }
      }
    })
  }

  // Prefix Distribution
  if (prefixChart.value && stats.value?.prefix_distribution) {
    new Chart(prefixChart.value, {
      type: 'pie',
      data: {
        labels: stats.value.prefix_distribution.map((p: any) => p.name),
        datasets: [{
          data: stats.value.prefix_distribution.map((p: any) => p.value),
          backgroundColor: ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#6b7280']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'right', labels: { color: '#9ca3af', boxWidth: 12 } } }
      }
    })
  }

  // BGP Updates
  if (updatesChart.value && traffic.value.length) {
    new Chart(updatesChart.value, {
      type: 'bar',
      data: {
        labels: traffic.value.map((d: any) => d.time),
        datasets: [{
          label: 'Updates',
          data: traffic.value.map((d: any) => d.updates),
          backgroundColor: '#8b5cf6'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#9ca3af', font: { size: 10 } } },
          y: { grid: { color: '#1f2937' }, ticks: { color: '#9ca3af' } }
        }
      }
    })
  }
}

function initMap() {
  if (!globalMap.value || !isClient) return
  
  import('leaflet').then((LModule) => {
    const L = LModule.default
    
    const map = L.map(globalMap.value!, {
      center: [20, 0],
      zoom: 2
    })
    
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: 'OpenStreetMap CARTO',
      maxZoom: 19
    }).addTo(map)
    
    const colors: Record<string, string> = {
      'BR': '#10b981',
      'US': '#3b82f6',
      'DE': '#ef4444',
      'GB': '#8b5cf6',
      'JP': '#f59e0b',
      'CN': '#ec4899',
      'IN': '#14b8a6',
      'RU': '#f97316'
    }
    
    // Show only first 100 operators to avoid overload
    globalOperators.value.slice(0, 100).forEach((op: any) => {
      if (!op.lat || !op.lng) return
      
      const color = colors[op.country] || '#3b82f6'
      
      const marker = L.circleMarker([op.lat, op.lng], {
        radius: 5,
        fillColor: color,
        color: '#fff',
        weight: 1,
        opacity: 0.9,
        fillOpacity: 0.8
      }).addTo(map)
      
      marker.bindPopup(`
        <div style="min-width: 150px">
          <strong style="color: ${color}">AS${op.asn}</strong><br/>
          <span>${op.name}</span><br/>
          <span style="color: #6b7280; font-size: 11px">${op.country}</span>
        </div>
      `)
    })
  })
}
</script>
