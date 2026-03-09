<template>
  <div class="min-h-screen bg-gray-950 text-gray-100">
    <!-- Header -->
    <header class="border-b border-gray-800 bg-gray-900/50 backdrop-blur sticky top-0 z-50">
      <div class="container mx-auto px-4">
        <div class="flex items-center justify-between h-16">
          <!-- Logo -->
          <NuxtLink to="/" class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
              <UIcon name="i-heroicons-signal-alt" class="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 class="text-lg font-bold"><span class="text-green-500">BR</span><span class="text-black dark:text-white">RADAR</span></h1>
              <p class="text-xs text-gray-500 -mt-0.5">BGP Intelligence</p>
            </div>
          </NuxtLink>
          
          <!-- Search -->
          <div class="flex-1 max-w-xl mx-8">
            <div class="relative">
              <UIcon name="i-heroicons-magnifying-glass" class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input 
                v-model="searchQuery"
                @input="onSearch"
                type="text" 
                placeholder="Buscar ASN, operador, país..."
                class="w-full bg-gray-800 border border-gray-700 rounded-xl py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              >
              
              <!-- Search Results -->
              <div v-if="showResults && results.length" class="absolute top-full left-0 right-0 mt-2 bg-gray-800 border border-gray-700 rounded-xl shadow-2xl overflow-hidden z-50">
                <div 
                  v-for="r in results" 
                  :key="r.asn"
                  class="px-4 py-3 hover:bg-gray-700 cursor-pointer flex items-center justify-between"
                  @click="goToASN(r.asn)"
                >
                  <div class="flex items-center gap-3">
                    <span class="text-emerald-400 font-mono font-bold">AS{{ r.asn }}</span>
                    <span class="text-gray-300">{{ r.name }}</span>
                  </div>
                  <span class="text-xs text-gray-500">{{ r.country }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Nav -->
          <nav class="flex items-center gap-4">
            <NuxtLink to="/" class="text-gray-400 hover:text-white transition" active-class="text-emerald-500">
              Dashboard
            </NuxtLink>
            <NuxtLink to="/asn" class="text-gray-400 hover:text-white transition" active-class="text-emerald-500">
              ASNs
            </NuxtLink>
            <NuxtLink to="/ix" class="text-gray-400 hover:text-white transition" active-class="text-emerald-500">
              IXs
            </NuxtLink>
          </nav>
        </div>
      </div>
    </header>
    
    <!-- Main -->
    <main class="container mx-auto px-4 py-6">
      <slot />
    </main>
    
    <!-- Footer -->
    <footer class="border-t border-gray-800 py-6 mt-12">
      <div class="container mx-auto px-4 text-center text-gray-500 text-sm">
        <p>© 2024 Bradar Network - Inteligência de Rede Brasileira</p>
        <p class="text-xs mt-1">85.518 ASNs Globais | 9.088 ASNs Brasil</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
const searchQuery = ref('')
const results = ref<any[]>([])
const showResults = ref(false)

const config = useRuntimeConfig()
const router = useRouter()

async function onSearch() {
  if (searchQuery.value.length < 2) {
    results.value = []
    return
  }
  
  try {
    const data = await $fetch(`${config.public.apiBase}/search?q=${searchQuery.value}&limit=10`)
    results.value = data as any[]
    showResults.value = true
  } catch (e) {
    console.error(e)
  }
}

function goToASN(asn: number) {
  router.push(`/asn/${asn}`)
  showResults.value = false
  searchQuery.value = ''
}

// Close results on click outside
onMounted(() => {
  document.addEventListener('click', (e) => {
    if (!(e.target as HTMLElement).closest('.relative')) {
      showResults.value = false
    }
  })
})
</script>
